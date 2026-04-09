import os

from core.data_loader import load_all_data
from core.gnn_model import generate_heatmap
from core.solver import (
    compute_global_costs,
    solve_allocation,
    solve_best_fit,
    solve_nearest_neighbor,
)


def _rank_key(costs):
    return (
        -float(costs.get("feasible_rate", 0.0)),
        float(costs.get("total_cost", float("inf"))),
        float(costs.get("makespan", float("inf"))),
        float(costs.get("total_travel", float("inf"))),
    )


def test_gcn_not_worse_than_constructive_fallbacks_under_hard_constraints():
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    _, _, orders, charging_stations = load_all_data(order_limit=120)
    unique_nodes = list(
        set(
            [(o["start_x"], o["start_y"], o["start_z"]) for o in orders]
            + [(o["end_x"], o["end_y"], o["end_z"]) for o in orders]
        )
    )
    node_to_idx = {node: i for i, node in enumerate(unique_nodes)}
    model_path = os.path.join(repo_dir, "models", "gcn_model.pth")
    heatmap = generate_heatmap(unique_nodes, model_path=model_path, temperature=1.0, train=False)

    gcn_agvs, gcn_stats = solve_allocation(
        orders,
        heatmap,
        node_to_idx,
        charging_stations=charging_stations,
        return_stats=True,
    )
    bf_agvs, bf_stats = solve_best_fit(
        orders, charging_stations=charging_stations, return_stats=True
    )
    nn_agvs, nn_stats = solve_nearest_neighbor(
        orders, charging_stations=charging_stations, return_stats=True
    )

    gcn_costs = compute_global_costs(gcn_agvs, metrics=gcn_stats)
    bf_costs = compute_global_costs(bf_agvs, metrics=bf_stats)
    nn_costs = compute_global_costs(nn_agvs, metrics=nn_stats)

    assert _rank_key(gcn_costs) <= _rank_key(bf_costs)
    assert _rank_key(gcn_costs) <= _rank_key(nn_costs)
    assert 0.0 <= gcn_costs["feasible_rate"] <= 1.0
    assert gcn_costs["unassigned_orders"] >= 0

