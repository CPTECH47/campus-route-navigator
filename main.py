"""Tkinter interface for the Campus Route Navigator mini-project."""

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from routing import CampusMap, Route, load_map, shortest_route


MAP_FILE = Path(__file__).with_name("campus_map.json")
AREA_COLORS = {
    "building": "#dae7f4",
    "shop": "#f5e6c6",
    "sport": "#dcecda",
    "ground": "#dcecda",
    "parking": "#e9e2f3",
}
ROUTE_COLOR = "#174fa5"


class NavigatorApp:
    def __init__(self, root: tk.Tk, campus: CampusMap) -> None:
        self.campus = campus
        self.route: Route | None = None
        self.landmark_ids = {
            node.name: node_id for node_id, node in campus.nodes.items() if node.landmark
        }
        names = sorted(self.landmark_ids)
        self.start = tk.StringVar(value="Entry Gate" if "Entry Gate" in names else names[0])
        self.end = tk.StringVar(
            value="Basketball Court" if "Basketball Court" in names else names[-1]
        )
        self.summary = tk.StringVar()

        root.title("Campus Route Navigator | GEHU Haldwani")
        root.minsize(760, 570)
        width = max(760, min(950, root.winfo_screenwidth() - 70))
        height = max(570, min(700, root.winfo_screenheight() - 85))
        root.geometry(f"{width}x{height}")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        page = ttk.Frame(root, padding=16)
        page.grid(sticky="nsew")
        page.columnconfigure(0, weight=1)
        page.rowconfigure(2, weight=1)

        ttk.Label(page, text="Campus Route Navigator", font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(page, text="GEHU Haldwani  |  BCA AI & DS, Semester 3").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        map_panel = ttk.LabelFrame(page, text="Campus map", padding=8)
        map_panel.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        map_panel.columnconfigure(0, weight=1)
        map_panel.rowconfigure(0, weight=1)
        self.map_view = tk.Canvas(map_panel, background="#f7f8f3", highlightthickness=0)
        self.map_view.grid(row=0, column=0, sticky="nsew")
        self.map_view.bind("<Configure>", self.draw_map)
        ttk.Label(map_panel, text="Blue = selected route   |   Gray = other paths").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )

        controls = ttk.LabelFrame(page, text="Find shortest route", padding=12)
        controls.grid(row=2, column=1, sticky="nsew")
        controls.columnconfigure(0, weight=1)
        controls.rowconfigure(8, weight=1)

        for row, label, variable in [(0, "Start", self.start), (2, "Destination", self.end)]:
            ttk.Label(controls, text=label).grid(row=row, column=0, sticky="w")
            choice = ttk.Combobox(
                controls, textvariable=variable, values=names, state="readonly", width=28
            )
            choice.grid(row=row + 1, column=0, sticky="ew", pady=(3, 8))
            choice.bind("<<ComboboxSelected>>", self.find_route)

        buttons = ttk.Frame(controls)
        buttons.grid(row=4, column=0, sticky="ew")
        ttk.Button(buttons, text="Find route", command=self.find_route).pack(side="left")
        ttk.Button(buttons, text="Swap", command=self.swap_points).pack(side="left", padx=6)

        ttk.Separator(controls).grid(row=5, column=0, sticky="ew", pady=12)
        ttk.Label(
            controls, textvariable=self.summary, font=("Segoe UI", 12, "bold"),
            wraplength=235, justify="left",
        ).grid(row=6, column=0, sticky="w")
        ttk.Label(controls, text="Walking steps").grid(
            row=7, column=0, sticky="w", pady=(12, 5)
        )

        steps_panel = ttk.Frame(controls)
        steps_panel.grid(row=8, column=0, sticky="nsew")
        steps_panel.columnconfigure(0, weight=1)
        steps_panel.rowconfigure(0, weight=1)
        self.steps = tk.Text(
            steps_panel, width=26, height=8, wrap="word", state="disabled",
            background="white", foreground="#263646", font=("Segoe UI", 10),
            relief="solid", borderwidth=1, padx=8, pady=6,
        )
        self.steps.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(steps_panel, command=self.steps.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.steps.configure(yscrollcommand=scrollbar.set)

        data_note = "Sketch-based demo. Paths and distances are provisional."
        if not campus.estimated:
            data_note = "Distances are read from the campus map file."
        ttk.Label(
            controls, text=f"{data_note}\nWalking pace assumed: "
            f"{campus.walking_speed_m_per_min:g} m/min.",
            wraplength=238, justify="left",
        ).grid(row=9, column=0, sticky="w", pady=(10, 0))
        self.find_route()

    def swap_points(self) -> None:
        start_name, end_name = self.start.get(), self.end.get()
        self.start.set(end_name)
        self.end.set(start_name)
        self.find_route()

    def find_route(self, _event: tk.Event | None = None) -> None:
        start_id = self.landmark_ids[self.start.get()]
        end_id = self.landmark_ids[self.end.get()]
        self.route = shortest_route(self.campus, start_id, end_id)
        if self.route is None:
            self.summary.set("No route found")
            directions = "There is no connection between these locations in the campus map."
        else:
            route = self.route
            about = "~" if self.campus.estimated else ""
            self.summary.set(
                f"{about}{route.distance_m:g} m  |  ~{route.walking_time_min:.1f} min"
            )
            lines = [f"Start at {self.start.get()}."]
            for number, (node_id, distance) in enumerate(
                zip(route.node_ids[1:], route.leg_distances_m), start=1
            ):
                name = self.campus.nodes[node_id].name
                lines.append(f"{number}. Walk {about}{distance:g} m to {name}.")
            if start_id == end_id:
                lines.append("You are already at your destination.")
            else:
                lines.append(f"Arrive at {self.end.get()}.")
            directions = "\n\n".join(lines)

        self.steps.configure(state="normal")
        self.steps.delete("1.0", "end")
        self.steps.insert("1.0", directions)
        self.steps.configure(state="disabled")
        self.steps.yview_moveto(0)
        self.draw_map()

    def draw_map(self, _event: tk.Event | None = None) -> None:
        view = self.map_view
        width, height = view.winfo_width(), view.winfo_height()
        if width < 40 or height < 40:
            return
        view.delete("all")
        scale = min((width - 20) / self.campus.map_width,
                    (height - 20) / self.campus.map_height)
        offset_x = (width - self.campus.map_width * scale) / 2
        offset_y = (height - self.campus.map_height * scale) / 2

        def point(x: float, y: float) -> tuple[float, float]:
            return offset_x + x * scale, offset_y + y * scale

        area_names = {area.name for area in self.campus.areas}
        for area in self.campus.areas:
            left, top = point(area.x1, area.y1)
            right, bottom = point(area.x2, area.y2)
            view.create_rectangle(
                left, top, right, bottom, fill=AREA_COLORS.get(area.kind, "#e1e6ea"),
                outline="#a6b0b8",
            )
            view.create_text(
                (left + right) / 2, (top + bottom) / 2, text=area.name,
                fill="#253746", width=max(40, right - left - 8),
                font=("Segoe UI", 9, "bold"), justify="center",
            )

        nodes = self.campus.nodes
        positions = {node_id: point(node.x, node.y) for node_id, node in nodes.items()}
        for edge in self.campus.edges:
            view.create_line(*positions[edge.start], *positions[edge.end],
                             fill="#a0aab4", width=4, capstyle="round")

        stops = self.route.node_ids if self.route is not None else ()
        for start_id, end_id in zip(stops, stops[1:]):
            view.create_line(*positions[start_id], *positions[end_id],
                             fill=ROUTE_COLOR, width=5, capstyle="round")
        for node_id, node in nodes.items():
            x, y = positions[node_id]
            endpoint = bool(stops) and node_id in (stops[0], stops[-1])
            radius = 6 if endpoint else (4 if node.landmark else 3)
            color = ROUTE_COLOR if node_id in stops else "#516575"
            view.create_oval(x - radius, y - radius, x + radius, y + radius,
                             fill=color, outline="white")
            if node.landmark and node.name not in area_names:
                view.create_text(x, y + 10, text=node.name, anchor="n",
                                 fill="#253746", font=("Segoe UI", 9, "bold"))


def main() -> None:
    root = tk.Tk()
    try:
        campus = load_map(MAP_FILE)
    except (OSError, ValueError) as error:
        root.withdraw()
        messagebox.showerror("Campus map error", str(error), parent=root)
        root.destroy()
        return

    NavigatorApp(root, campus)
    root.mainloop()


if __name__ == "__main__":
    main()
