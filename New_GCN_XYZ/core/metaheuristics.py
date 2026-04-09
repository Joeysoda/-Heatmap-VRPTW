"""
Constraint-consistent metaheuristic baselines.

All methods reuse the same hard-constraint constructive engine from core.solver.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple

from .config import RANDOM_SEED
from .solver import (
    compute_global_costs,
    solve_best_fit,
    solve_first_fit,
    solve_nearest_neighbor,
)


def _run_constructive(
    constructor,
    orders: Sequence[dict],
    charging_stations=None,
):
    return constructor(orders, charging_stations=charging_stations, return_stats=True)


def _solution_cost(agvs, stats):
    costs = compute_global_costs(agvs, metrics=stats)
    return float(costs["total_cost"])


def _permute_orders(orders: Sequence[dict], rng: random.Random, swap_count: int = 8):
    candidate = [dict(o) for o in orders]
    n = len(candidate)
    if n < 2:
        return candidate
    for _ in range(min(swap_count, n // 2 + 1)):
        i, j = rng.randrange(n), rng.randrange(n)
        candidate[i], candidate[j] = candidate[j], candidate[i]
    return candidate


def solve_simulated_annealing(
    orders: Sequence[dict],
    heatmap=None,
    node_to_idx=None,
    charging_stations=None,
    return_stats: bool = False,
    initial_temp: float = 20.0,
    cooling_rate: float = 0.85,
    iterations: int = 10,
):
    """
    SA baseline: perturb order sequence, rebuild with constrained Best Fit.
    """
    rng = random.Random(RANDOM_SEED)
    current_agvs, current_stats = _run_constructive(
        solve_best_fit,
        [dict(o) for o in orders],
        charging_stations=charging_stations,
    )
    current_cost = _solution_cost(current_agvs, current_stats)

    best_agvs, best_stats = current_agvs, dict(current_stats)
    best_cost = current_cost
    temperature = float(initial_temp)

    for _ in range(max(1, iterations)):
        neighbor_orders = _permute_orders(orders, rng, swap_count=6)
        neighbor_agvs, neighbor_stats = _run_constructive(
            solve_best_fit,
            neighbor_orders,
            charging_stations=charging_stations,
        )
        neighbor_cost = _solution_cost(neighbor_agvs, neighbor_stats)
        delta = neighbor_cost - current_cost

        accept = False
        if delta < 0:
            accept = True
        elif temperature > 1e-9:
            accept = rng.random() < math.exp(-delta / temperature)

        if accept:
            current_agvs, current_stats, current_cost = neighbor_agvs, neighbor_stats, neighbor_cost
            if current_cost < best_cost:
                best_agvs, best_stats, best_cost = current_agvs, dict(current_stats), current_cost

        temperature *= cooling_rate

    if return_stats:
        return best_agvs, best_stats
    return best_agvs


def solve_genetic_algorithm(
    orders: Sequence[dict],
    heatmap=None,
    node_to_idx=None,
    charging_stations=None,
    return_stats: bool = False,
    population_size: int = 4,
    generations: int = 4,
):
    """
    GA baseline: evolve order permutations, evaluate via constrained Best Fit.
    """
    rng = random.Random(RANDOM_SEED + 1)
    population: List[List[dict]] = []
    base = [dict(o) for o in orders]
    population.append(base)
    for _ in range(max(1, population_size - 1)):
        population.append(_permute_orders(base, rng, swap_count=10))

    best_agvs, best_stats = _run_constructive(
        solve_best_fit, population[0], charging_stations=charging_stations
    )
    best_cost = _solution_cost(best_agvs, best_stats)

    for _ in range(max(1, generations)):
        evaluated: List[Tuple[float, List[dict]]] = []
        for genome in population:
            agvs, stats = _run_constructive(
                solve_best_fit, genome, charging_stations=charging_stations
            )
            cost = _solution_cost(agvs, stats)
            evaluated.append((cost, genome))
            if cost < best_cost:
                best_cost = cost
                best_agvs, best_stats = agvs, dict(stats)

        evaluated.sort(key=lambda x: x[0])
        elites = [evaluated[0][1], evaluated[1][1] if len(evaluated) > 1 else evaluated[0][1]]
        new_population = [list(g) for g in elites]

        while len(new_population) < population_size:
            parent = list(rng.choice(elites))
            child = _permute_orders(parent, rng, swap_count=5)
            new_population.append(child)
        population = new_population

    if return_stats:
        return best_agvs, best_stats
    return best_agvs


def solve_tabu_search(
    orders: Sequence[dict],
    heatmap=None,
    node_to_idx=None,
    charging_stations=None,
    return_stats: bool = False,
    max_iterations: int = 12,
    tabu_tenure: int = 5,
):
    """
    TS baseline: neighborhood over order permutations with short tabu memory.
    """
    rng = random.Random(RANDOM_SEED + 2)
    current = [dict(o) for o in orders]
    current_agvs, current_stats = _run_constructive(
        solve_best_fit, current, charging_stations=charging_stations
    )
    current_cost = _solution_cost(current_agvs, current_stats)

    best_agvs, best_stats, best_cost = current_agvs, dict(current_stats), current_cost
    tabu: List[Tuple[str, str]] = []

    for _ in range(max(1, max_iterations)):
        candidates = []
        for _ in range(4):
            proposal = _permute_orders(current, rng, swap_count=4)
            if len(proposal) >= 2:
                move = (proposal[0].get("id", ""), proposal[-1].get("id", ""))
            else:
                move = ("", "")
            if move in tabu:
                continue
            agvs, stats = _run_constructive(
                solve_best_fit, proposal, charging_stations=charging_stations
            )
            cost = _solution_cost(agvs, stats)
            candidates.append((cost, proposal, move, agvs, stats))

        if not candidates:
            continue

        candidates.sort(key=lambda x: x[0])
        current_cost, current, move, cand_agvs, cand_stats = candidates[0]
        tabu.append(move)
        if len(tabu) > max(1, tabu_tenure):
            tabu.pop(0)

        if current_cost < best_cost:
            best_cost = current_cost
            best_agvs, best_stats = cand_agvs, dict(cand_stats)

    if return_stats:
        return best_agvs, best_stats
    return best_agvs


def solve_ant_colony_optimization(
    orders: Sequence[dict],
    heatmap=None,
    node_to_idx=None,
    charging_stations=None,
    return_stats: bool = False,
    num_ants: int = 6,
    iterations: int = 6,
    rho: float = 0.3,
):
    """
    ACO baseline: sequence construction on order ids + constrained Best Fit evaluator.
    """
    rng = random.Random(RANDOM_SEED + 3)
    if not orders:
        agvs, stats = _run_constructive(solve_best_fit, [], charging_stations=charging_stations)
        if return_stats:
            return agvs, stats
        return agvs

    order_pool = [dict(o) for o in orders]
    pheromone: Dict[str, float] = {str(o.get("id", i)): 1.0 for i, o in enumerate(order_pool)}

    best_agvs = None
    best_stats = None
    best_cost = float("inf")

    for _ in range(max(1, iterations)):
        ant_solutions = []
        for _ in range(max(1, num_ants)):
            remaining = [dict(o) for o in order_pool]
            sequence = []
            while remaining:
                weights = []
                for o in remaining:
                    oid = str(o.get("id", ""))
                    tau = pheromone.get(oid, 1.0)
                    weights.append(max(1e-6, tau))
                chosen = rng.choices(remaining, weights=weights, k=1)[0]
                sequence.append(chosen)
                remaining.remove(chosen)

            agvs, stats = _run_constructive(
                solve_best_fit, sequence, charging_stations=charging_stations
            )
            cost = _solution_cost(agvs, stats)
            ant_solutions.append((cost, sequence, agvs, stats))

            if cost < best_cost:
                best_cost = cost
                best_agvs = agvs
                best_stats = dict(stats)

        for key in pheromone:
            pheromone[key] *= (1.0 - rho)
            pheromone[key] = max(1e-6, pheromone[key])

        ant_solutions.sort(key=lambda x: x[0])
        top_k = ant_solutions[: max(1, len(ant_solutions) // 2)]
        for cost, seq, _, _ in top_k:
            reward = 1.0 / max(cost, 1e-6)
            for o in seq:
                oid = str(o.get("id", ""))
                pheromone[oid] = pheromone.get(oid, 1.0) + reward

    if best_agvs is None:
        best_agvs, best_stats = _run_constructive(
            solve_best_fit, order_pool, charging_stations=charging_stations
        )

    if return_stats:
        return best_agvs, best_stats
    return best_agvs

