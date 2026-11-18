import json
import math
import tempfile
import unittest
from pathlib import Path

from routing import load_map, shortest_route


MAP_PATH = Path(__file__).with_name("campus_map.json")


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.campus = load_map(MAP_PATH)
        cls.landmarks = [key for key, node in cls.campus.nodes.items() if node.landmark]

    def test_all_landmark_pairs_match_independent_shortest_distances(self) -> None:
        nodes = self.campus.nodes
        self.assertEqual(len(self.landmarks), 7)
        self.assertTrue(self.campus.estimated)

        # Floyd-Warshall computes shortest distances without using the route finder.
        distances = {(a, b): 0.0 if a == b else math.inf for a in nodes for b in nodes}
        steps = {}
        for edge in self.campus.edges:
            for pair in ((edge.start, edge.end), (edge.end, edge.start)):
                steps[pair] = edge.distance_m
                distances[pair] = edge.distance_m
        for via in nodes:
            for start in nodes:
                for end in nodes:
                    pair = (start, end)
                    distances[pair] = min(distances[pair], distances[start, via] + distances[via, end])

        for start in self.landmarks:
            for end in self.landmarks:
                with self.subTest(start=start, end=end):
                    route = shortest_route(self.campus, start, end)
                    self.assertIsNotNone(route)
                    self.assertEqual((route.node_ids[0], route.node_ids[-1]), (start, end))
                    self.assertEqual(len(set(route.node_ids)), len(route.node_ids))
                    expected_legs = tuple(steps[pair] for pair in zip(route.node_ids, route.node_ids[1:]))
                    self.assertEqual(route.leg_distances_m, expected_legs)
                    self.assertAlmostEqual(route.distance_m, sum(expected_legs))
                    self.assertAlmostEqual(route.distance_m, distances[start, end])
                    self.assertAlmostEqual(route.distance_m, distances[end, start])
                    self.assertAlmostEqual(
                        route.walking_time_min,
                        route.distance_m / self.campus.walking_speed_m_per_min,
                    )
                    if start == end:
                        self.assertEqual(route.node_ids, (start,))

    def test_unreachable_landmark_returns_no_route(self) -> None:
        data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        data["edges"] = [data["edges"][0]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "disconnected.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            campus = load_map(path)

        edge = campus.edges[0]
        isolated = next(key for key in self.landmarks if key not in (edge.start, edge.end))
        self.assertIsNone(shortest_route(campus, edge.start, isolated))

    def test_malformed_map_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_map(path)


if __name__ == "__main__":
    unittest.main()
