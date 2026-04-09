"""
Algorithm comparison runner (8 algorithms, hard constraints, unified metrics).
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import shutil
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(__file__))

from core.config import (  # noqa: E402
    BATTERY_RISK_WEIGHT,
    GAMMA_HEAT,
    GCN_TUNING_SPACE,
    LAMBDA_DIST,
    LAMBDA_LOAD,
    RANDOM_SEED,
    TW_URGENCY_WEIGHT,
)
from core.data_loader import load_all_data  # noqa: E402
from core.gnn_model import generate_heatmap  # noqa: E402
from core.metaheuristics import (  # noqa: E402
    solve_ant_colony_optimization,
    solve_genetic_algorithm,
    solve_simulated_annealing,
    solve_tabu_search,
)
from core.solver import (  # noqa: E402
    compute_global_costs,
    solve_allocation,
    solve_best_fit,
    solve_first_fit,
    solve_nearest_neighbor,
)


def _sha256(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def _ranking_key(algo_data: dict):
    return (
        -_safe_float(algo_data.get("feasible_rate", 0.0), 0.0),
        _safe_float(algo_data.get("total_cost", float("inf")), float("inf")),
        _safe_float(algo_data.get("makespan", float("inf")), float("inf")),
        _safe_float(algo_data.get("total_travel", float("inf")), float("inf")),
    )


def _default_gcn_params():
    return {
        "LAMBDA_DIST": float(LAMBDA_DIST),
        "LAMBDA_LOAD": float(LAMBDA_LOAD),
        "GAMMA_HEAT": float(GAMMA_HEAT),
        "TW_URGENCY_WEIGHT": float(TW_URGENCY_WEIGHT),
        "BATTERY_RISK_WEIGHT": float(BATTERY_RISK_WEIGHT),
    }


def _safe_filename(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")


def _build_gcn_candidates(max_candidates: int = 20):
    base = _default_gcn_params()
    keys = [
        "LAMBDA_DIST",
        "LAMBDA_LOAD",
        "GAMMA_HEAT",
        "TW_URGENCY_WEIGHT",
        "BATTERY_RISK_WEIGHT",
    ]
    candidates: List[dict] = [dict(base)]

    # One-at-a-time perturbation around defaults (conservative bounded search).
    for key in keys:
        values = GCN_TUNING_SPACE.get(key, [base[key]])
        for value in values:
            if float(value) == float(base[key]):
                continue
            c = dict(base)
            c[key] = float(value)
            candidates.append(c)

    # Add a few combined random candidates.
    rng = random.Random(RANDOM_SEED)
    while len(candidates) < max_candidates:
        c = {}
        for key in keys:
            values = GCN_TUNING_SPACE.get(key, [base[key]])
            c[key] = float(rng.choice(values))
        if c not in candidates:
            candidates.append(c)
        if len(candidates) >= max_candidates:
            break
    return candidates


class ComparisonExperiment:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.algorithms = {
            "GCN-Guided": solve_allocation,
            "Best Fit": solve_best_fit,
            "First Fit": solve_first_fit,
            "Nearest Neighbor": solve_nearest_neighbor,
            "SA": solve_simulated_annealing,
            "GA": solve_genetic_algorithm,
            "TS": solve_tabu_search,
            "ACO": solve_ant_colony_optimization,
        }

        self.results: List[dict] = []
        self.overall_ranking: List[dict] = []
        self.gcn_params = _default_gcn_params()

    def save_run_snapshot(self, test_scales: Sequence[int], model_path: str):
        snap_dir = os.path.join(self.output_dir, "run_snapshot")
        os.makedirs(snap_dir, exist_ok=True)

        files_to_copy = [
            os.path.join(os.path.dirname(__file__), "core", "config.py"),
            os.path.join(os.path.dirname(__file__), "core", "solver.py"),
            os.path.join(os.path.dirname(__file__), "core", "data_loader.py"),
            os.path.join(os.path.dirname(__file__), "core", "metaheuristics.py"),
            os.path.join(os.path.dirname(__file__), "run_comparison.py"),
        ]
        for src in files_to_copy:
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(snap_dir, os.path.basename(src)))

        snapshot_meta = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_scales": list(test_scales),
            "gcn_params": dict(self.gcn_params),
            "model_path": model_path,
            "model_sha256": _sha256(model_path),
        }
        with open(os.path.join(snap_dir, "snapshot_meta.json"), "w", encoding="utf-8") as f:
            json.dump(snapshot_meta, f, indent=2, ensure_ascii=False)

    def tune_gcn_params(
        self,
        all_orders: Sequence[dict],
        heatmap,
        node_to_idx: Dict[Tuple[float, float, int], int],
        charging_stations,
    ):
        # Medium-scale tuning set.
        target_scales = [200, 500]
        tune_scales = [s for s in target_scales if s <= len(all_orders)]
        if not tune_scales:
            tune_scales = [min(200, len(all_orders))]

        candidates = _build_gcn_candidates(max_candidates=18)
        best_params = dict(self.gcn_params)
        best_score = float("inf")

        print("\n[GCN Tuning] Start bounded parameter search...")
        print(f"[GCN Tuning] Scales: {tune_scales}, Candidates: {len(candidates)}")

        for idx, params in enumerate(candidates, start=1):
            aggregate_score = 0.0
            for scale in tune_scales:
                subset = list(all_orders[:scale])
                agvs, stats = solve_allocation(
                    subset,
                    heatmap=heatmap,
                    node_to_idx=node_to_idx,
                    charging_stations=charging_stations,
                    return_stats=True,
                    algorithm_params=params,
                )
                costs = compute_global_costs(agvs, metrics=stats)
                infeasible_penalty = (1.0 - costs.get("feasible_rate", 0.0)) * 1e7
                aggregate_score += costs["total_cost"] + infeasible_penalty

            aggregate_score /= max(1, len(tune_scales))
            if aggregate_score < best_score:
                best_score = aggregate_score
                best_params = dict(params)
            print(
                f"[GCN Tuning] {idx:02d}/{len(candidates)} "
                f"score={aggregate_score:.4f} params={params}"
            )

        self.gcn_params = best_params
        print(f"[GCN Tuning] Selected params: {self.gcn_params}")

    def run_single_experiment(
        self,
        orders: Sequence[dict],
        order_count: int,
        heatmap,
        node_to_idx: Dict[Tuple[float, float, int], int],
        charging_stations,
    ):
        print("\n" + "=" * 78)
        print(f"Experiment: {order_count} orders")
        print("=" * 78)

        experiment_result = {
            "order_count": int(order_count),
            "algorithms": {},
        }

        for algo_name, algo_func in self.algorithms.items():
            print(f"Running {algo_name} ...")
            start_time = time.time()
            try:
                if algo_name == "GCN-Guided":
                    agvs, stats = algo_func(
                        orders,
                        heatmap,
                        node_to_idx,
                        charging_stations=charging_stations,
                        return_stats=True,
                        algorithm_params=self.gcn_params,
                    )
                else:
                    agvs, stats = algo_func(
                        orders,
                        charging_stations=charging_stations,
                        return_stats=True,
                    )

                costs = compute_global_costs(agvs, metrics=stats)
                elapsed = time.time() - start_time
                row = {
                    "makespan": costs["makespan"],
                    "total_travel": costs["total_travel"],
                    "total_cost": costs["total_cost"],
                    "local_cost": costs.get("local_cost", 0.0),
                    "feasible_rate": costs.get("feasible_rate", 0.0),
                    "tw_violations": int(costs.get("tw_violations", 0)),
                    "battery_violations": int(costs.get("battery_violations", 0)),
                    "unassigned_orders": int(costs.get("unassigned_orders", 0)),
                    "assigned_orders": int(costs.get("assigned_orders", 0)),
                    "charging_insertions": int(costs.get("charging_insertions", 0)),
                    "elapsed_time": elapsed,
                    "status": "ok",
                }
                experiment_result["algorithms"][algo_name] = row
                print(
                    f"  feasible={row['feasible_rate']:.4f}, "
                    f"cost={row['total_cost']:.2f}, "
                    f"mk={row['makespan']:.2f}, travel={row['total_travel']:.2f}, "
                    f"unassigned={row['unassigned_orders']}, t={elapsed:.2f}s"
                )
            except Exception as exc:
                elapsed = time.time() - start_time
                experiment_result["algorithms"][algo_name] = {
                    "status": "error",
                    "error": str(exc),
                    "elapsed_time": elapsed,
                    "feasible_rate": 0.0,
                    "total_cost": float("inf"),
                    "makespan": float("inf"),
                    "total_travel": float("inf"),
                    "unassigned_orders": len(orders),
                    "tw_violations": len(orders),
                    "battery_violations": len(orders),
                }
                print(f"  ERROR: {exc}")

        self._rank_single_scale(experiment_result)
        self.results.append(experiment_result)
        return experiment_result

    def _rank_single_scale(self, experiment_result: dict):
        algos = experiment_result["algorithms"]
        valid = []
        for name, data in algos.items():
            if data.get("status") == "ok":
                valid.append((name, data))
            else:
                data["rank"] = None

        valid.sort(key=lambda x: _ranking_key(x[1]))
        for i, (name, data) in enumerate(valid, start=1):
            data["rank"] = i

    def compute_overall_ranking(self):
        aggregate = {}
        for result in self.results:
            for name, data in result["algorithms"].items():
                bucket = aggregate.setdefault(
                    name,
                    {
                        "algorithm": name,
                        "rank_sum": 0.0,
                        "rank_count": 0,
                        "first_places": 0,
                        "success_scales": 0,
                    },
                )
                rank = data.get("rank")
                if rank is not None:
                    bucket["rank_sum"] += rank
                    bucket["rank_count"] += 1
                    bucket["success_scales"] += 1
                    if rank == 1:
                        bucket["first_places"] += 1

        ranking = []
        for name, bucket in aggregate.items():
            if bucket["rank_count"] == 0:
                avg_rank = float("inf")
            else:
                avg_rank = bucket["rank_sum"] / bucket["rank_count"]
            ranking.append(
                {
                    "algorithm": name,
                    "avg_rank": avg_rank,
                    "first_places": bucket["first_places"],
                    "success_scales": bucket["success_scales"],
                }
            )

        ranking.sort(key=lambda x: (x["avg_rank"], -x["first_places"], -x["success_scales"], x["algorithm"]))
        for i, row in enumerate(ranking, start=1):
            row["overall_rank"] = i
        self.overall_ranking = ranking

        # Backfill each scale row with overall rank.
        overall_map = {row["algorithm"]: row["overall_rank"] for row in ranking}
        for result in self.results:
            for algo, data in result["algorithms"].items():
                data["overall_rank"] = overall_map.get(algo)

    def save_summary_csv(self):
        csv_path = os.path.join(self.output_dir, "summary.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "scale",
                    "algorithm",
                    "rank",
                    "overall_rank",
                    "feasible_rate",
                    "total_cost",
                    "makespan",
                    "total_travel",
                    "unassigned_orders",
                    "tw_violations",
                    "battery_violations",
                    "charging_insertions",
                    "elapsed_time",
                    "status",
                ]
            )
            for result in self.results:
                scale = result["order_count"]
                for algo_name, data in result["algorithms"].items():
                    writer.writerow(
                        [
                            scale,
                            algo_name,
                            data.get("rank"),
                            data.get("overall_rank"),
                            data.get("feasible_rate"),
                            data.get("total_cost"),
                            data.get("makespan"),
                            data.get("total_travel"),
                            data.get("unassigned_orders"),
                            data.get("tw_violations"),
                            data.get("battery_violations"),
                            data.get("charging_insertions"),
                            data.get("elapsed_time"),
                            data.get("status", "ok"),
                        ]
                    )
            writer.writerow([])
            writer.writerow(["OVERALL", "algorithm", "overall_rank", "avg_rank", "first_places", "success_scales"])
            for row in self.overall_ranking:
                writer.writerow(
                    [
                        "OVERALL",
                        row["algorithm"],
                        row["overall_rank"],
                        row["avg_rank"],
                        row["first_places"],
                        row["success_scales"],
                    ]
                )
        print(f"Saved summary: {csv_path}")

    def save_raw_results(self):
        json_path = os.path.join(self.output_dir, "raw_results.json")
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "gcn_params": self.gcn_params,
            "ranking_rule": "feasible_rate desc -> total_cost asc -> makespan asc -> total_travel asc",
            "results": self.results,
            "overall_ranking": self.overall_ranking,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Saved raw results: {json_path}")

    def save_text_report(self):
        txt_path = os.path.join(self.output_dir, "comparison_report.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("=" * 90 + "\n")
            f.write("Algorithm Comparison Report (Hard Constraints)\n")
            f.write("=" * 90 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"GCN params: {self.gcn_params}\n")
            f.write("Ranking rule: feasible_rate desc -> total_cost asc -> makespan asc -> total_travel asc\n\n")

            for result in self.results:
                f.write("-" * 90 + "\n")
                f.write(f"Scale: {result['order_count']} orders\n")
                f.write("-" * 90 + "\n")
                rows = list(result["algorithms"].items())
                rows.sort(
                    key=lambda item: item[1]["rank"] if item[1].get("rank") is not None else 999
                )
                for algo_name, data in rows:
                    if data.get("status") != "ok":
                        f.write(f"{algo_name:20s} ERROR: {data.get('error')}\n")
                        continue
                    f.write(
                        f"{algo_name:20s} "
                        f"rank={data.get('rank')} "
                        f"overall={data.get('overall_rank')} "
                        f"fr={data.get('feasible_rate', 0):.4f} "
                        f"cost={data.get('total_cost', 0):.2f} "
                        f"mk={data.get('makespan', 0):.2f} "
                        f"travel={data.get('total_travel', 0):.2f} "
                        f"unassigned={data.get('unassigned_orders', 0)} "
                        f"twv={data.get('tw_violations', 0)} "
                        f"bv={data.get('battery_violations', 0)}\n"
                    )
                f.write("\n")

            f.write("=" * 90 + "\n")
            f.write("Overall Ranking\n")
            f.write("=" * 90 + "\n")
            for row in self.overall_ranking:
                f.write(
                    f"#{row['overall_rank']}: {row['algorithm']} "
                    f"(avg_rank={row['avg_rank']:.3f}, first_places={row['first_places']}, "
                    f"success_scales={row['success_scales']})\n"
                )
        print(f"Saved report: {txt_path}")

    def _save_metric_svg(
        self,
        path: str,
        title: str,
        scales: Sequence[int],
        series: Dict[str, List[float]],
        higher_is_better: bool,
    ):
        width, height = 1200, 700
        left, top, right, bottom = 90, 80, 60, 90
        plot_w = width - left - right
        plot_h = height - top - bottom

        all_values = [v for vals in series.values() for v in vals if v == v and v != float("inf")]
        if not all_values:
            all_values = [0.0, 1.0]
        y_min = min(all_values)
        y_max = max(all_values)
        if y_max - y_min < 1e-9:
            y_max = y_min + 1.0

        def x_of(i: int) -> float:
            if len(scales) <= 1:
                return left + plot_w / 2.0
            return left + (i / (len(scales) - 1)) * plot_w

        def y_of(v: float) -> float:
            ratio = (v - y_min) / (y_max - y_min)
            return top + (1.0 - ratio) * plot_h

        palette = [
            "#1f77b4",
            "#d62728",
            "#2ca02c",
            "#ff7f0e",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#17becf",
        ]

        lines: List[str] = []
        lines.append(
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
            f"viewBox='0 0 {width} {height}'>"
        )
        lines.append("<rect x='0' y='0' width='100%' height='100%' fill='white'/>")
        lines.append(
            f"<text x='{width/2}' y='38' text-anchor='middle' font-size='26' font-family='Arial'>{title}</text>"
        )
        direction = "higher is better" if higher_is_better else "lower is better"
        lines.append(
            f"<text x='{width/2}' y='62' text-anchor='middle' font-size='14' fill='#666' font-family='Arial'>{direction}</text>"
        )

        # axes
        lines.append(f"<line x1='{left}' y1='{top + plot_h}' x2='{left + plot_w}' y2='{top + plot_h}' stroke='#222'/>")
        lines.append(f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top + plot_h}' stroke='#222'/>")

        # y ticks
        for i in range(6):
            yv = y_min + (i / 5.0) * (y_max - y_min)
            py = y_of(yv)
            lines.append(f"<line x1='{left-5}' y1='{py:.2f}' x2='{left}' y2='{py:.2f}' stroke='#666'/>")
            lines.append(
                f"<text x='{left-10}' y='{py+4:.2f}' text-anchor='end' font-size='12' fill='#444' font-family='Arial'>{yv:.4g}</text>"
            )
            lines.append(
                f"<line x1='{left}' y1='{py:.2f}' x2='{left+plot_w}' y2='{py:.2f}' stroke='#eee'/>"
            )

        # x ticks
        for i, scale in enumerate(scales):
            px = x_of(i)
            lines.append(f"<line x1='{px:.2f}' y1='{top+plot_h}' x2='{px:.2f}' y2='{top+plot_h+5}' stroke='#666'/>")
            lines.append(
                f"<text x='{px:.2f}' y='{top+plot_h+24}' text-anchor='middle' font-size='12' fill='#444' font-family='Arial'>{scale}</text>"
            )

        # series
        legend_x = left + 10
        legend_y = top + 10
        for idx, (algo, vals) in enumerate(series.items()):
            color = palette[idx % len(palette)]
            points = []
            for i, v in enumerate(vals):
                if v != v or v == float("inf"):
                    continue
                points.append(f"{x_of(i):.2f},{y_of(v):.2f}")
            if points:
                lines.append(
                    f"<polyline fill='none' stroke='{color}' stroke-width='2.2' points='{' '.join(points)}'/>"
                )
            for i, v in enumerate(vals):
                if v != v or v == float("inf"):
                    continue
                lines.append(
                    f"<circle cx='{x_of(i):.2f}' cy='{y_of(v):.2f}' r='3.5' fill='{color}'/>"
                )

            ly = legend_y + idx * 22
            lines.append(f"<line x1='{legend_x}' y1='{ly}' x2='{legend_x+22}' y2='{ly}' stroke='{color}' stroke-width='3'/>")
            lines.append(
                f"<text x='{legend_x+30}' y='{ly+4}' font-size='12' fill='#222' font-family='Arial'>{algo}</text>"
            )

        lines.append("</svg>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def save_charts(self):
        if not self.results:
            return

        scales = [int(r["order_count"]) for r in self.results]
        algo_names = list(self.algorithms.keys())

        metric_specs = [
            ("feasible_rate", "Feasible Rate", True),
            ("total_cost", "Total Cost", False),
            ("makespan", "Makespan", False),
            ("total_travel", "Total Travel", False),
        ]

        try:
            import matplotlib.pyplot as plt  # type: ignore

            has_matplotlib = True
        except Exception:
            has_matplotlib = False

        for metric, title, higher_is_better in metric_specs:
            series: Dict[str, List[float]] = {}
            for algo in algo_names:
                values = []
                for result in self.results:
                    data = result["algorithms"].get(algo, {})
                    values.append(_safe_float(data.get(metric, float("nan")), float("nan")))
                series[algo] = values

            if has_matplotlib:
                fig, ax = plt.subplots(figsize=(11, 6))
                for algo, values in series.items():
                    ax.plot(scales, values, marker="o", linewidth=1.8, label=algo)
                ax.set_title(f"{title} by Scale")
                ax.set_xlabel("Order Count")
                ax.set_ylabel(title)
                ax.grid(True, linestyle="--", alpha=0.35)
                ax.legend(fontsize=8, ncol=2)
                out_path = os.path.join(self.output_dir, f"chart_{_safe_filename(metric)}.png")
                fig.tight_layout()
                fig.savefig(out_path, dpi=180)
                plt.close(fig)
                print(f"Saved chart: {out_path}")
            else:
                out_path = os.path.join(self.output_dir, f"chart_{_safe_filename(metric)}.svg")
                self._save_metric_svg(out_path, f"{title} by Scale", scales, series, higher_is_better)
                print(f"Saved chart: {out_path}")


def main():
    print("\n" + "=" * 78)
    print("Algorithm Comparison (GCN + Hard Constraints + 8 Algorithms)")
    print("=" * 78)

    # 1) Load data
    print("\n[1/6] Loading data...")
    nodes, edges, all_orders, charging_stations = load_all_data(order_limit=None)
    print(f"Orders loaded: {len(all_orders)}")

    # 2) Build heatmap
    print("\n[2/6] Generating heatmap...")
    unique_nodes = list(
        set(
            [(o["start_x"], o["start_y"], o["start_z"]) for o in all_orders]
            + [(o["end_x"], o["end_y"], o["end_z"]) for o in all_orders]
        )
    )
    node_to_idx = {node: i for i, node in enumerate(unique_nodes)}

    model_path = os.path.join(os.path.dirname(__file__), "models", "gcn_model.pth")
    heatmap = generate_heatmap(unique_nodes, model_path=model_path, temperature=1.0, train=True)
    print(f"Heatmap shape: {heatmap.shape}")

    # Output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(__file__), "results", f"comparison_{timestamp}")
    experiment = ComparisonExperiment(output_dir=output_dir)

    test_scales = [50, 100, 200, 500, 1000, len(all_orders)]
    test_scales = [s for s in test_scales if s <= len(all_orders)]

    experiment.save_run_snapshot(test_scales=test_scales, model_path=model_path)

    # 3) Tune GCN
    print("\n[3/6] Tuning GCN parameters (bounded search)...")
    experiment.tune_gcn_params(
        all_orders=all_orders,
        heatmap=heatmap,
        node_to_idx=node_to_idx,
        charging_stations=charging_stations,
    )

    # 4) Run full comparison
    print("\n[4/6] Running full comparison...")
    for scale in test_scales:
        subset = list(all_orders[:scale])
        experiment.run_single_experiment(
            orders=subset,
            order_count=scale,
            heatmap=heatmap,
            node_to_idx=node_to_idx,
            charging_stations=charging_stations,
        )

    experiment.compute_overall_ranking()

    # 5) Save outputs
    print("\n[5/6] Saving outputs...")
    experiment.save_summary_csv()
    experiment.save_raw_results()
    experiment.save_text_report()
    print("\n[6/6] Generating charts...")
    experiment.save_charts()

    gcn_overall = next((r for r in experiment.overall_ranking if r["algorithm"] == "GCN-Guided"), None)
    if gcn_overall is not None:
        print(
            f"\nGCN overall rank: {gcn_overall['overall_rank']} "
            f"(avg_rank={gcn_overall['avg_rank']:.3f}, first_places={gcn_overall['first_places']})"
        )
    print(f"Results directory: {output_dir}")


if __name__ == "__main__":
    main()
