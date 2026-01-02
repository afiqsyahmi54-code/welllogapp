# screens/porosity_screen.py
from kivy.uix.screenmanager import Screen
from kivy_garden.matplotlib import FigureCanvasKivyAgg
from kivymd.app import MDApp
from kivymd.toast import toast

import numpy as np
import matplotlib.pyplot as plt

from utils.android_file_utils import read_las_file
from utils.plot_utils import create_depth_track
from utils.constants import COLORS


class PorosityScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_figures = []   # ✅ REQUIRED FOR PDF
        self.intervals = []

    def on_enter(self):
        app = MDApp.get_running_app()

        try:
            well = app.root.get_screen("welllog")
            self.ids.info_label.text = (
                f"Well Name: {well.ids.well_name.text or '-'}\n"
                f"Location: {well.ids.location.text or '-'}\n"
                f"Depth Range: {well.ids.depth_range.text or '-'}"
            )
        except Exception:
            pass

        self.plot_porosity(app.selected_file)

    def plot_porosity(self, file_path):
        if not file_path:
            toast("No LAS file selected")
            return

        df = read_las_file(file_path)
        if df is None:
            return

        # ========= CLEAR OLD =========
        box = self.ids.box_area
        box.clear_widgets()

        for fig in self.current_figures:
            try:
                plt.close(fig)
            except Exception:
                pass
        self.current_figures = []

        # ========= DEPTH =========
        depth = df["Depth"]
        depth_min = depth.min()
        depth_max = depth.max()
        depth_range = depth_max - depth_min

        pixels_per_meter = 2
        canvas_height = int(depth_range * pixels_per_meter)
        canvas_height = max(800, min(canvas_height, 20000))
        fig_height = max(8, min(canvas_height / 100, 100))

        # ========= GR CUTOFF =========
        gr_series = df["Gamma Ray"].dropna()
        if gr_series.empty:
            toast("No Gamma Ray data")
            return

        gr_min = gr_series.min()
        gr_max = gr_series.max()
        cut_off = (gr_max - gr_min) / 2 + gr_min

        # ========= INTERVALS =========
        intervals = []
        in_zone = False
        start_depth = None
        min_gr = max_gr = None
        prev_depth = None

        for _, row in df.iterrows():
            d = row["Depth"]
            gr = row["Gamma Ray"]

            if np.isnan(gr):
                if in_zone:
                    intervals.append((start_depth, prev_depth, min_gr, max_gr))
                    in_zone = False
                prev_depth = d
                continue

            if gr < cut_off:
                if not in_zone:
                    in_zone = True
                    start_depth = d
                    min_gr = max_gr = gr
                else:
                    min_gr = min(min_gr, gr)
                    max_gr = max(max_gr, gr)
            else:
                if in_zone:
                    intervals.append((start_depth, prev_depth, min_gr, max_gr))
                    in_zone = False

            prev_depth = d

        if in_zone:
            intervals.append((start_depth, prev_depth, min_gr, max_gr))

        self.intervals = intervals

        # ========= POROSITY =========
        porosity = None
        if "Density" in df.columns:
            rho_matrix = 2.65
            rho_fluid = 1.0
            phi_d = (rho_matrix - df["Density"]) / (rho_matrix - rho_fluid)
            phi_d = np.clip(phi_d, 0, 1)

            if "Neutron" in df.columns:
                neutron = df["Neutron"]
                if neutron.max() > 1:
                    neutron = neutron / 100
                porosity = (phi_d + neutron) / 2
            else:
                porosity = phi_d

        # ========= DEPTH TRACK =========
        fig_depth, ax_depth = create_depth_track(
            depth_min, depth_max, fig_height, intervals
        )

         # ========= GR TRACK =========
        fig_gr, ax_gr = plt.subplots(figsize=(3.5, fig_height))

        ax_gr.plot(
            df["Gamma Ray"], depth,
            color=COLORS["gamma_ray"],
            linewidth=1.5,
            label="Gamma Ray"
        )

        ax_gr.axvline(
            cut_off,
            color=COLORS["cutoff_line"],
            linestyle="--",
            linewidth=2,
            label=f"Cut-off: {cut_off:.1f} gAPI"
        )

        for idx, (top, bottom, _, _) in enumerate(intervals):
            ax_gr.axhspan(
                top, bottom,
                color=COLORS["sand"],
                alpha=0.4,
                label="Reservoir" if idx == 0 else ""
            )

        ax_gr.set_ylim(depth_max, depth_min)
        ax_gr.set_xlim(0, 200)
        ax_gr.set_xticks([0, 50, 100, 150, 200])
        ax_gr.set_title("Gamma Ray\n(gAPI)", fontsize=10, fontweight="bold")

        ax_gr.legend(loc="upper right", fontsize=7, framealpha=0.9)


         # ========= NEUTRON–DENSITY =========
        fig_nd, ax_nd = plt.subplots(figsize=(3.5, fig_height))

        ax_nd.plot(
            df["Density"], depth,
            color=COLORS["density"],
            linewidth=1.5,
            label="Density (RHOB)"
        )

        for top, bottom, _, _ in intervals:
            ax_nd.axhspan(top, bottom, color=COLORS["sand"], alpha=0.4)

        twin = ax_nd.twiny()
        twin.plot(
            df["Neutron"], depth,
            color=COLORS["neutron"],
            linewidth=1.5,
            label="Neutron (NPHI)"
        )

        ax_nd.set_ylim(depth_max, depth_min)
        ax_nd.set_xlim(1.85, 2.85)
        twin.set_xlim(0, 0.45)

        ax_nd.set_title("Density / Neutron\n(g/cm³)    (v/v)",
                        fontsize=10, fontweight="bold")

        # ---- COMBINED LEGEND (IMPORTANT) ----
        h1, l1 = ax_nd.get_legend_handles_labels()
        h2, l2 = twin.get_legend_handles_labels()
        ax_nd.legend(h1 + h2, l1 + l2,
                     loc="upper right", fontsize=7, framealpha=0.9)


         # ========= POROSITY TRACK =========
        fig_phi, ax_phi = plt.subplots(figsize=(3.5, fig_height))

        if porosity is not None:
            ax_phi.plot(
                porosity * 100, depth,
                color=COLORS["porosity"],
                linewidth=1.5,
                label="Porosity (Φ)"
            )

            for top, bottom, _, _ in intervals:
                ax_phi.axhspan(top, bottom, color=COLORS["sand"], alpha=0.4)

            ax_phi.axvline(
                10, color="green", linestyle=":",
                linewidth=1, alpha=0.5,
                label="Good (>10%)"
            )
            ax_phi.axvline(
                5, color="orange", linestyle=":",
                linewidth=1, alpha=0.5,
                label="Fair (5–10%)"
            )

            ax_phi.legend(loc="upper right", fontsize=7, framealpha=0.9)

        ax_phi.set_ylim(depth_max, depth_min)
        ax_phi.set_xlim(0, 40)
        ax_phi.set_xticks([0, 10, 20, 30, 40])
        ax_phi.set_title("Porosity\n(%)", fontsize=10, fontweight="bold")


        # ========= STORE FIGURES (🔥 FIX) =========
        self.current_figures = [
            fig_depth,
            fig_gr,
            fig_nd,
            fig_phi
        ]

        # ========= ADD CANVASES =========
        for fig, width in [
            (fig_depth, 0.15),
            (fig_gr, 0.25),
            (fig_nd, 0.30),
            (fig_phi, 0.30),
        ]:
            canvas = FigureCanvasKivyAgg(fig)
            canvas.size_hint_y = None
            canvas.height = canvas_height
            canvas.size_hint_x = width
            box.add_widget(canvas)

    def navigate_back(self):
        MDApp.get_running_app().change_screen("interpretation")
