"""Load the campus graph and calculate shortest walking routes."""

import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Node:
    name: str
    x: float
    y: float
    landmark: bool


@dataclass(frozen=True)
class Edge:
    start: str
    end: str
    distance_m: float


@dataclass(frozen=True)
class Area:
    name: str
    kind: str
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class CampusMap:
    nodes: dict[str, Node]
    edges: tuple[Edge, ...]
    walking_speed_m_per_min: float
    estimated: bool
    map_width: int
    map_height: int
    areas: tuple[Area, ...]


@dataclass(frozen=True)
class Route:
    node_ids: tuple[str, ...]
    leg_distances_m: tuple[float, ...]
    distance_m: float
    walking_time_min: float


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number.")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{label} must be finite.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite.")
    return result


def _name(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")
    return value.strip()


def _load_nodes(raw: object, width: int, height: int) -> dict[str, Node]:
    if not isinstance(raw, dict) or not raw:
        raise ValueError("nodes must be a non-empty object keyed by node ID.")

    nodes = {}
    landmark_names: set[str] = set()
    for node_id, item in raw.items():
        if not node_id.strip() or not isinstance(item, dict):
            raise ValueError("Each node needs an ID and an object of properties.")

        name = _name(item.get("name"), f"Node {node_id} name")
        x = _number(item.get("x"), f"Node {node_id} x")
        y = _number(item.get("y"), f"Node {node_id} y")
        if not (0 <= x <= width and 0 <= y <= height):
            raise ValueError(f"Node {node_id} is outside the map.")

        landmark = item.get("landmark")
        if not isinstance(landmark, bool):
            raise ValueError(f"Node {node_id} landmark must be true or false.")
        if landmark:
            if name.casefold() in landmark_names:
                raise ValueError(f"Duplicate landmark name: {name}.")
            landmark_names.add(name.casefold())
        nodes[node_id] = Node(name, x, y, landmark)

    if len(landmark_names) < 2:
        raise ValueError("The map needs at least two selectable landmarks.")
    return nodes


def _load_edges(raw: object, nodes: dict[str, Node]) -> tuple[Edge, ...]:
    if not isinstance(raw, list):
        raise ValueError("edges must be a list.")

    edges = []
    seen: set[frozenset[str]] = set()
    for index, item in enumerate(raw, start=1):
        label = f"Edge {index}"
        if not isinstance(item, dict):
            raise ValueError(f"{label} must be an object.")
        start = _name(item.get("start"), f"{label} start")
        end = _name(item.get("end"), f"{label} end")
        if start not in nodes or end not in nodes or start == end:
            raise ValueError(f"{label} must connect two different, existing nodes.")
        pair = frozenset((start, end))
        if pair in seen:
            raise ValueError(f"{label} repeats a connection between {start} and {end}.")
        seen.add(pair)

        distance = _number(item.get("distance_m"), f"{label} distance_m")
        if distance <= 0:
            raise ValueError(f"{label} distance_m must be positive.")
        edges.append(Edge(start, end, distance))
    return tuple(edges)


def _load_areas(raw: object, width: int, height: int) -> tuple[Area, ...]:
    if not isinstance(raw, list):
        raise ValueError("areas must be a list.")

    areas = []
    for index, item in enumerate(raw, start=1):
        label = f"Area {index}"
        if not isinstance(item, dict):
            raise ValueError(f"{label} must be an object.")
        name = _name(item.get("name"), f"{label} name")
        kind = _name(item.get("kind"), f"{label} kind")
        if kind not in {"building", "sport", "parking", "ground", "shop"}:
            raise ValueError(f"{label} has an unsupported kind: {kind}.")
        x1 = _number(item.get("x1"), f"{label} x1")
        y1 = _number(item.get("y1"), f"{label} y1")
        x2 = _number(item.get("x2"), f"{label} x2")
        y2 = _number(item.get("y2"), f"{label} y2")
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise ValueError(f"{label} needs valid rectangular bounds inside the map.")
        areas.append(Area(name, kind, x1, y1, x2, y2))
    return tuple(areas)


def load_map(path: Path) -> CampusMap:
    """Read validated map data. Raise ValueError for invalid data."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("The map JSON must contain an object.")

    width = data.get("map_width")
    height = data.get("map_height")
    if type(width) is not int or width <= 0:
        raise ValueError("map_width must be a positive integer.")
    if type(height) is not int or height <= 0:
        raise ValueError("map_height must be a positive integer.")

    speed = _number(data.get("walking_speed_m_per_min"), "walking_speed_m_per_min")
    if speed <= 0:
        raise ValueError("walking_speed_m_per_min must be positive.")
    estimated = data.get("estimated")
    if not isinstance(estimated, bool):
        raise ValueError("estimated must be true or false.")

    nodes = _load_nodes(data.get("nodes"), width, height)
    edges = _load_edges(data.get("edges"), nodes)
    areas = _load_areas(data.get("areas"), width, height)
    return CampusMap(nodes, edges, speed, estimated, width, height, areas)


def shortest_route(campus_map: CampusMap, start_id: str, end_id: str) -> Route | None:
    """Find a minimum-distance route using Dijkstra's algorithm."""
    for node_id in (start_id, end_id):
        if node_id not in campus_map.nodes:
            raise ValueError(f"Unknown campus node: {node_id}.")

    adjacency: dict[str, list[tuple[str, float]]] = {
        node_id: [] for node_id in campus_map.nodes
    }
    for edge in campus_map.edges:
        adjacency[edge.start].append((edge.end, edge.distance_m))
        adjacency[edge.end].append((edge.start, edge.distance_m))

    best = {start_id: 0.0}
    previous: dict[str, tuple[str, float]] = {}
    queue = [(0.0, start_id)]

    while queue:
        distance, node_id = heapq.heappop(queue)
        if distance > best[node_id]:
            continue  # A better entry for this node was added later.
        if node_id == end_id:
            break
        for neighbor, leg_distance in adjacency[node_id]:
            candidate = distance + leg_distance
            if candidate < best.get(neighbor, math.inf):
                best[neighbor] = candidate
                previous[neighbor] = (node_id, leg_distance)
                heapq.heappush(queue, (candidate, neighbor))

    if end_id not in best:
        return None

    path = [end_id]
    leg_distances = []
    while path[-1] != start_id:
        predecessor, leg_distance = previous[path[-1]]
        path.append(predecessor)
        leg_distances.append(leg_distance)

    total_distance = best[end_id]
    return Route(
        tuple(reversed(path)),
        tuple(reversed(leg_distances)),
        total_distance,
        total_distance / campus_map.walking_speed_m_per_min,
    )
