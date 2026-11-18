# Campus Route Navigator

A BCA AI & DS Semester 3 mini-project for finding the shortest walking route between landmarks at the GEHU Haldwani campus. Pick a start and destination to see the route on a schematic map, the distance, and the estimated walking time.

## Run on Windows

Install Python 3.10 or newer with Tkinter, then open PowerShell in this folder and run:

```powershell
py main.py
```

You can also use `python main.py`. The app runs offline with the Python standard library.

## How it works

1. `campus_map.json` stores landmarks, junctions, and the walking distance for each connection in metres.
2. `routing.py` puts those connections in an adjacency list. A connection is walkable in both directions.
3. Dijkstra's algorithm uses Python's `heapq` to visit the closest node found so far. It remembers the previous node on each best path so it can rebuild the route once it reaches the destination.
4. `main.py` highlights that route in Tkinter. It estimates walking time by dividing total distance by the walking pace in the JSON file.

Try Entry Gate to Basketball Court. Use **Swap** to check the route in reverse. Picking the same start and destination displays a zero-length route.

## Campus data

The starter map is based on a hand-drawn sketch. The distances and exact entrance connections are provisional. To update the data, list every direct walkable segment between two places or junctions and measure it in metres. If a crossing or bend matters for choosing a route, give it its own junction. Update `distance_m` and the relevant endpoints in `campus_map.json`. Keep `estimated` set to `true` until the segments and distances have been checked on campus.

## Self-check

```powershell
py -m unittest discover
```
