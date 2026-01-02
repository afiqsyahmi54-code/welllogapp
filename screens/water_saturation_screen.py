# screens/water_saturation_screen.py
from kivy.uix.screenmanager import Screen
from kivy_garden.matplotlib import FigureCanvasKivyAgg
from kivymd.app import MDApp
from kivymd.toast import toast

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from utils.android_file_utils import read_las_file
from utils.plot_utils import create_depth_track
from utils.constants import COLORS


class WaterSaturationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_figures = []
        self.current_axes = []
        self.current_canvases = []

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

        self.plot_water_saturation(app.selected_file)

    # =========================================================
    # CORE PLOTTING METHOD (MATCHES RESERVOIR STYLE)
    # =========================================================
    def plot_water_saturation(self, file_path):

        if not file_path:
            toast("No LAS file selected")
            return

        df = read_las_file(file_path)
        if df is None:
            return

        box = self.ids.box_area
        box.clear_widgets()

        for fig in self.current_figures:
            try:
                plt.close(fig)
            except Exception:
                pass
        self.current_figures = []
        # ================= DEPTH =================
        depth = df["Depth"]
        depth_min = depth.min()
        depth_max = depth.max()
        depth_range = depth_max - depth_min

        pixels_per_meter = 1.8
        canvas_height = int(depth_range * pixels_per_meter)
        canvas_height = max(800, min(canvas_height, 20000))
        fig_height = max(8, min(canvas_height / 100, 100))

        # ================= GAMMA RAY CUTOFF =================
        gr_series = df["Gamma Ray"].dropna()
        if gr_series.empty:
            toast("No Gamma Ray data")
            return

        gr_min = gr_series.min()
        gr_max = gr_series.max()
        cut_off = (gr_max - gr_min) / 2 + gr_min

        # ================= RESERVOIR INTERVALS =================
        intervals = []
        in_zone = False
        start_depth = None
        min_gr = max_gr = None
        prev_depth = None

        for _, row in df.iterrows():
            d = row["Depth"]
            gr = row["Gamma Ray"]

            if pd.isna(gr):
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

        # ================= POROSITY =================
        porosity = None
        if "Density" in df.columns:
            rho_matrix = 2.65
            rho_fluid = 1.0
            phi_d = (rho_matrix - df["Density"]) / (rho_matrix - rho_fluid)
            phi_d = np.clip(phi_d, 0.01, 1)

            if "Neutron" in df.columns:
                neutron = df["Neutron"]
                if neutron.max() > 1:
                    neutron = neutron / 100
                porosity = (phi_d + neutron) / 2
            else:
                porosity = phi_d

        # ================= WATER SATURATION (ARCHIE) =================
        sw = None
        if porosity is not None and "Resistivity" in df.columns:
            rw, m, n = 0.1, 2.0, 2.0
            rt = np.clip(df["Resistivity"], 0.1, 10000)
            sw = (0.62 * rw / (porosity ** m * rt)) ** (1 / n)
            sw = np.clip(sw, 0, 1)

        # ================= DEPTH TRACK =================
        fig_depth, ax_depth = create_depth_track(
            depth_min, depth_max, fig_height, intervals
        )

        # ================= GAMMA RAY TRACK =================
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

        self._style_axis(ax_gr, depth_min, depth_max)
        ax_gr.set_xlim(0, 200)
        ax_gr.set_xticks([0, 50, 100, 150, 200])
        ax_gr.set_title("Gamma Ray\n(gAPI)", fontsize=10, fontweight="bold")

        ax_gr.legend(loc="upper right", fontsize=7, framealpha=0.9)


        # ================= NEUTRON–DENSITY (RESERVOIR STYLE) =================
        fig_nd, ax_nd = plt.subplots(figsize=(3.5, fig_height))

        ax_nd.plot(df["Density"], depth,
                   color=COLORS["density"],
                   linewidth=1.5,
                   label="Density (RHOB)")

        for top, bottom, _, _ in intervals:
            ax_nd.axhspan(top, bottom, color=COLORS["sand"], alpha=0.4)

        self._style_axis(ax_nd, depth_min, depth_max)
        ax_nd.set_xlim(1.85, 2.85)
        ax_nd.set_xticks([1.85, 2.0, 2.2, 2.4, 2.6, 2.85])
        ax_nd.set_xticklabels(["1.85", "2.0", "2.2", "2.4", "2.6", "2.85"])
        ax_nd.set_title("Density / Neutron\n(g/cm³)    (v/v)", fontsize=10, fontweight="bold")

        twin = ax_nd.twiny()
        twin.plot(df["Neutron"], depth,
                  color=COLORS["neutron"],
                  linewidth=1.5,
                  label="Neutron (NPHI)")

        twin.set_xlim(0, 0.45)
        twin.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.45])
        twin.set_xticklabels(["0", "0.1", "0.2", "0.3", "0.4", "0.45"])
        twin.tick_params(axis="x", colors=COLORS["neutron"])
        twin.spines["top"].set_color(COLORS["neutron"])

        h1, l1 = ax_nd.get_legend_handles_labels()
        h2, l2 = twin.get_legend_handles_labels()
        ax_nd.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=7, framealpha=0.9)

        # ================= RESISTIVITY (RESERVOIR STYLE) =================
        fig_res, ax_res = plt.subplots(figsize=(3.5, fig_height))

        ax_res.semilogx(df["Resistivity"], depth,
                        color=COLORS["resistivity"],
                        linewidth=1.5,
                        label="Resistivity")

        for top, bottom, _, _ in intervals:
            ax_res.axhspan(top, bottom, color=COLORS["sand"], alpha=0.4)

        self._style_axis(ax_res, depth_min, depth_max)
        ax_res.set_xscale("log")
        ax_res.set_xlim(0.2, 200)
        ax_res.set_xticks([0.2, 1, 10, 100, 200])
        ax_res.set_xticklabels(["0.2", "1", "10", "100", "200"])
        ax_res.set_title("Resistivity\n(ohm.m)", fontsize=10, fontweight="bold")

        ax_res.axvline(10, color="blue", linestyle=":", linewidth=1, alpha=0.5, label="Water Baseline")
        ax_res.axvline(50, color="green", linestyle=":", linewidth=1, alpha=0.5, label="Pay Indicator")
        ax_res.legend(loc="upper right", fontsize=7, framealpha=0.9)

         # ================= WATER SATURATION =================
        fig_sw, ax_sw = plt.subplots(figsize=(3.5, fig_height))

        if sw is not None:
            ax_sw.plot(
                sw * 100, depth,
                color=COLORS["water_saturation"],
                linewidth=1.5,
                label="Sw (m=2.0, n=2.0)"
            )

            for top, bottom, _, _ in intervals:
                ax_sw.axhspan(top, bottom, color=COLORS["sand"], alpha=0.4)

            ax_sw.axvline(
                50, color="green", linestyle=":",
                linewidth=1, alpha=0.5,
                label="Hydrocarbon (Sw < 50%)"
            )
            ax_sw.axvline(
                70, color="orange", linestyle=":",
                linewidth=1, alpha=0.5,
                label="Transition (50–70%)"
            )
            ax_sw.axvline(
                90, color="red", linestyle=":",
                linewidth=1, alpha=0.5,
                label="Water (Sw > 90%)"
            )

            # Hydrocarbon fill zone (same logic as Reservoir screen)
            ax_sw.fill_betweenx(
                depth, 0, sw * 100,
                where=(sw * 100) < 50,
                color="lightgreen",
                alpha=0.3,
                label="Hydrocarbon Zone"
            )

            ax_sw.legend(loc="upper right", fontsize=7, framealpha=0.9)

        self._style_axis(ax_sw, depth_min, depth_max)
        ax_sw.set_xlim(0, 100)
        ax_sw.set_xticks([0, 20, 40, 60, 80, 100])
        ax_sw.set_title("Water Saturation\n(%)", fontsize=10, fontweight="bold")

        # ================= STORE FIGURES FOR PDF EXPORT =================
        self.current_figures = [
            fig_depth,
            fig_gr,
            fig_nd,
            fig_res,
            fig_sw
        ]

        # store intervals so PDF can shade reservoirs
        self.intervals = intervals

        # ================= ADD CANVASES =================
        for fig, width in [
            (fig_depth, 0.10),
            (fig_gr, 0.18),
            (fig_nd, 0.18),
            (fig_res, 0.18),
            (fig_sw, 0.26),
        ]:
            canvas = FigureCanvasKivyAgg(fig)
            canvas.size_hint_y = None
            canvas.height = canvas_height
            canvas.size_hint_x = width
            box.add_widget(canvas)

    # =========================================================
    # COMMON AXIS STYLING (IDENTICAL TO RESERVOIR)
    # =========================================================
    def _style_axis(self, ax, depth_min, depth_max):
        ax.set_facecolor(COLORS["background"])
        ax.grid(True, which="both", linestyle="--",
                linewidth=0.5, alpha=0.7, color=COLORS["grid"])
        ax.set_axisbelow(True)
        ax.set_ylim(depth_max, depth_min)
        ax.set_ylabel("Depth (m)", fontsize=9, fontweight="bold")

        for spine in ax.spines.values():
            spine.set_linewidth(1)
            spine.set_color("#333333")

    def navigate_back(self):
        MDApp.get_running_app().change_screen("interpretation")
