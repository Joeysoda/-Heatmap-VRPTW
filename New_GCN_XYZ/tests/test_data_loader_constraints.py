import random

from core.data_loader import load_all_data


def test_data_loader_maps_true_node_coordinates_and_time_windows():
    nodes, _, orders, charging_stations = load_all_data(order_limit=300)
    assert nodes, "nodes should not be empty"
    assert orders, "orders should not be empty"
    assert charging_stations, "charging stations should not be empty"

    node_map = {node["node_code"]: (node["x"], node["y"], node["z"]) for node in nodes}
    sample_size = min(40, len(orders))
    sampled = random.sample(orders, sample_size)

    for order in sampled:
        assert "pickup_tw_start" in order
        assert "pickup_tw_end" in order
        assert "delivery_tw_start" in order
        assert "delivery_tw_end" in order
        assert "final_deadline" in order
        assert "pickup_tw_start_sec" in order
        assert "delivery_tw_end_sec" in order
        assert order.get("time_window_valid", False) is True

        if order["start_node"] in node_map:
            x, y, z = node_map[order["start_node"]]
            assert abs(order["start_x"] - x) < 1e-6
            assert abs(order["start_y"] - y) < 1e-6
            assert int(order["start_z"]) == int(z)

        if order["end_node"] in node_map:
            x, y, z = node_map[order["end_node"]]
            assert abs(order["end_x"] - x) < 1e-6
            assert abs(order["end_y"] - y) < 1e-6
            assert int(order["end_z"]) == int(z)

