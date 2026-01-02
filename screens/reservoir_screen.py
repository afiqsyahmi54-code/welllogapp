# screens/reservoir_screen.py - Reservoir identification screen
from kivy.uix.screenmanager import Screen
from kivy_garden.matplotlib import FigureCanvasKivyAgg
from kivymd.uix.label import MDLabel
from kivymd.toast import toast
from kivymd.app import MDApp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.android_file_utils import read_las_file
from utils.constants import COLORS
from utils.plot_utils import create_depth_track

class ReservoirScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_figures = []
        self.current_axes = []
        self.current_canvases = []
        self.detected_intervals = []
        self.df = None
        self.cut_off = None
        self.intervals = []
        self.m_value = 2.0
        self.n_value = 2.0
        
    def on_enter(self):
        """Update info when entering screen"""
        app = MDApp.get_running_app()
        try:
            well_screen = app.root.get_screen("welllog")
            well_name = well_screen.ids.well_name.text or "-"
            location = well_screen.ids.location.text or "-"
            depth_range = well_screen.ids.depth_range.text or "-"
            self.ids.reservoir_info_label.text = f"Well Name: {well_name}\nLocation: {location}\nDepth Range: {depth_range}"
        except Exception:
            pass

        # Get initial m and n values
        try:
            self.m_value = float(self.ids.m_value.text)
        except:
            self.m_value = 2.0
            
        try:
            self.n_value = float(self.ids.n_value.text)
        except:
            self.n_value = 2.0

        # Plot the reservoir identification
        self.plot_and_identify(app.selected_file)

    def clear_previous(self):
        """Clear only the plot widgets, NOT the interval list"""
        box = self.ids.reservoir_box
        box.clear_widgets()
        
        # Close matplotlib figures
        for fig in getattr(self, "current_figures", []):
            try:
                plt.close(fig)
            except Exception:
                pass
        self.current_figures = []
        self.current_axes = []
        self.current_canvases = []

    def update_interval_display(self):
        """Update the interval display in the UI"""
        intervals_box = self.ids.reservoir_intervals_box
        intervals_box.clear_widgets()
        
        if not self.intervals:
            intervals_box.add_widget(MDLabel(
                text="No reservoir intervals detected (GR cut-off method).", 
                size_hint_y=None, 
                height="28dp",
                theme_text_color="Secondary"
            ))
        else:
            for idx, (top, bottom, min_g, max_g) in enumerate(self.intervals, start=1):
                label_text = f"Interval {idx}: {top:.1f} - {bottom:.1f} m"
                label_widget = MDLabel(
                    text=label_text, 
                    size_hint_y=None, 
                    height="24dp", 
                    theme_text_color="Secondary"
                )
                intervals_box.add_widget(label_widget)

    # ========== PETROPHYSICAL CALCULATION METHODS ==========
    
    def calculate_porosity(self, df):
        """Calculate porosity from density-neutron crossplot"""
        try:
            # Density porosity calculation
            rho_matrix = 2.65  # g/cm³ (sandstone matrix)
            rho_fluid = 1.0    # g/cm³ (fresh water)
            
            if "Density" not in df.columns:
                return None
            
            phi_density = (rho_matrix - df["Density"]) / (rho_matrix - rho_fluid)
            phi_density = np.clip(phi_density, 0, 1)
            
            # If we have neutron porosity, calculate average
            if "Neutron" in df.columns:
                neutron = df["Neutron"]
                if neutron.max() > 1:
                    neutron = neutron / 100
                phi_total = (phi_density + neutron) / 2
            else:
                phi_total = phi_density
            
            return phi_total
            
        except Exception as e:
            print(f"Error calculating porosity: {e}")
            return None

    def calculate_vshale(self, df):
        """Calculate shale volume (Vshale) from Gamma Ray"""
        try:
            if "Gamma Ray" not in df.columns:
                return None, None, None
            
            gr = df["Gamma Ray"]
            gr_clean = gr.quantile(0.10)
            gr_shale = gr.quantile(0.90)
            
            vsh = (gr - gr_clean) / (gr_shale - gr_clean)
            vsh = np.clip(vsh, 0, 1)
            
            return vsh, gr_clean, gr_shale
            
        except Exception as e:
            print(f"Error calculating Vshale: {e}")
            return None, None, None

    def calculate_water_saturation(self, df, porosity, m, n, rw=0.1, rt=None):
        """Calculate water saturation using Archie's equation"""
        try:
            if porosity is None:
                return None
            
            if rt is None:
                if "Resistivity" in df.columns:
                    rt = df["Resistivity"]
                else:
                    return None
            
            phi = np.clip(porosity, 0.01, 1.0)
            rt_clipped = np.clip(rt, 0.1, 10000)
            
            sw = (0.62 * rw / (phi**m * rt_clipped))**(1/n)
            sw = np.clip(sw, 0, 1)
            
            return sw
            
        except Exception as e:
            print(f"Error calculating water saturation: {e}")
            return None

    # ========== ENHANCED PLOTTING METHOD WITH NEW TRACKS ==========
    
    def create_reservoir_plots(self, df, depth_min, depth_max, fig_height_inches, cut_off, intervals):
        """Create enhanced plots with reservoir highlighting and new tracks"""
        # Create all figures
        fig_gr, ax_gr = plt.subplots(figsize=(3.5, fig_height_inches))
        fig_nd, ax_nd = plt.subplots(figsize=(3.5, fig_height_inches))
        fig_res, ax_res = plt.subplots(figsize=(3.5, fig_height_inches))
        fig_phi, ax_phi = plt.subplots(figsize=(3.5, fig_height_inches))
        fig_vsh, ax_vsh = plt.subplots(figsize=(3.5, fig_height_inches))
        fig_sw, ax_sw = plt.subplots(figsize=(3.5, fig_height_inches))

        # Set professional styling
        plt.style.use('default')
        
        # Store figures and axes
        self.current_figures = [fig_gr, fig_nd, fig_res, fig_phi, fig_vsh, fig_sw]
        self.current_axes = [ax_gr, ax_nd, ax_res, ax_phi, ax_vsh, ax_sw]

        # ========== GAMMA RAY PLOT WITH RESERVOIR HIGHLIGHTING ==========
        ax_gr.plot(df["Gamma Ray"], df["Depth"], 
                  color=COLORS['gamma_ray'], 
                  linewidth=1.5, 
                  label="Gamma Ray")
        
        # Add cutoff line
        ax_gr.axvline(x=cut_off, color=COLORS['cutoff_line'], 
                     linestyle='--', linewidth=2, 
                     label=f"Cut-off: {cut_off:.1f} gAPI")
        
        # Shade reservoir intervals
        for top, bottom, min_g, max_g in intervals:
            ax_gr.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4, 
                         label='Reservoir' if top == intervals[0][0] else "")
        
        ax_gr.set_facecolor(COLORS['background'])
        ax_gr.grid(True, which='both', linestyle='--', 
                  linewidth=0.5, alpha=0.7, color=COLORS['grid'])
        ax_gr.set_axisbelow(True)
        ax_gr.set_xlabel("")
        ax_gr.set_title("Gamma Ray\n(gAPI)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
        ax_gr.set_ylabel("Depth (m)", fontsize=9, fontweight='bold')
        ax_gr.set_ylim(depth_max, depth_min)
        
        # Set axis range and bottom numbers like Porosity
        ax_gr.set_xlim(0, 200)
        ax_gr.set_xticks([0, 50, 100, 150, 200])
        ax_gr.set_xticklabels(["0", "50", "100", "150", "200"])
        
        ax_gr.legend(loc="upper right", fontsize=7, framealpha=0.9)
        for spine in ax_gr.spines.values():
            spine.set_linewidth(1)
            spine.set_color('#333333')

        # ========== NEUTRON-DENSITY PLOT ==========
        ax_nd.plot(df["Density"], df["Depth"], 
                  color=COLORS['density'], 
                  linewidth=1.5, 
                  label="Density (RHOB)")
        
        # Shade reservoir intervals
        for top, bottom, min_g, max_g in intervals:
            ax_nd.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4)
        
        ax_nd.set_facecolor(COLORS['background'])
        ax_nd.grid(True, which='both', linestyle='--', 
                  linewidth=0.5, alpha=0.7, color=COLORS['grid'])
        ax_nd.set_axisbelow(True)
        ax_nd.set_xlabel("")
        ax_nd.set_title("Density / Neutron\n(g/cm³)    (v/v)", 
                       fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
        ax_nd.set_ylim(depth_max, depth_min)
        
        # Set density axis range and bottom numbers
        ax_nd.set_xlim(1.85, 2.85)
        ax_nd.set_xticks([1.85, 2.0, 2.2, 2.4, 2.6, 2.85])
        ax_nd.set_xticklabels(["1.85", "2.0", "2.2", "2.4", "2.6", "2.85"])
        ax_nd.set_ylabel("Depth (m)", fontsize=9, fontweight='bold')

        # Neutron plot on twin axis
        twin_ax = ax_nd.twiny()
        twin_ax.plot(df["Neutron"], df["Depth"], 
                    color=COLORS['neutron'], 
                    linewidth=1.5, 
                    linestyle="-", 
                    label="Neutron (NPHI)")
        
        # Set neutron axis range and bottom numbers
        twin_ax.set_xlim(0, 0.45)
        twin_ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.45])
        twin_ax.set_xticklabels(["0", "0.1", "0.2", "0.3", "0.4", "0.45"])
        
        twin_ax.set_xlabel("")
        twin_ax.spines['top'].set_color(COLORS['neutron'])
        twin_ax.xaxis.label.set_color(COLORS['neutron'])
        twin_ax.tick_params(axis='x', colors=COLORS['neutron'])

        handles1, labels1 = ax_nd.get_legend_handles_labels()
        handles2, labels2 = twin_ax.get_legend_handles_labels()
        all_handles = handles1 + handles2
        all_labels = labels1 + labels2
        ax_nd.legend(all_handles, all_labels, loc="upper right", fontsize=7, framealpha=0.9)
        
        for spine in ax_nd.spines.values():
            spine.set_linewidth(1)
            spine.set_color('#333333')

        # ========== RESISTIVITY PLOT ==========
        ax_res.semilogx(df["Resistivity"], df["Depth"], 
                       color=COLORS['resistivity'], 
                       linewidth=1.5, 
                       label="Resistivity")
        
        # Shade reservoir intervals
        for top, bottom, min_g, max_g in intervals:
            ax_res.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4)
        
        ax_res.set_facecolor(COLORS['background'])
        ax_res.grid(True, which='both', linestyle='--', 
                   linewidth=0.5, alpha=0.7, color=COLORS['grid'])
        ax_res.set_axisbelow(True)
        ax_res.set_xscale("log")
        ax_res.set_xlabel("")
        ax_res.set_title("Resistivity\n(ohm.m)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
        ax_res.set_ylabel("Depth (m)", fontsize=9, fontweight='bold')
        ax_res.set_ylim(depth_max, depth_min)
        
        # Set resistivity axis range and bottom numbers
        ax_res.set_xlim(0.2, 200)
        ax_res.set_xticks([0.2, 1, 10, 100, 200])
        ax_res.set_xticklabels(["0.2", "1", "10", "100", "200"])
        
        ax_res.axvline(x=10, color='blue', linestyle=':', 
                      linewidth=1, alpha=0.5, label='Water Baseline')
        ax_res.axvline(x=50, color='green', linestyle=':', 
                      linewidth=1, alpha=0.5, label='Pay Indicator')
        ax_res.legend(loc="upper right", fontsize=7, framealpha=0.9)
        
        for spine in ax_res.spines.values():
            spine.set_linewidth(1)
            spine.set_color('#333333')

        # ========== POROSITY TRACK ==========
        porosity = self.calculate_porosity(df)
        
        if porosity is not None:
            ax_phi.plot(porosity * 100, df["Depth"],
                       color=COLORS['porosity'], 
                       linewidth=1.5, 
                       label="Porosity (Φ)")
            
            for top, bottom, min_g, max_g in intervals:
                ax_phi.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4)
            
            ax_phi.set_facecolor(COLORS['background'])
            ax_phi.grid(True, which='both', linestyle='--', 
                       linewidth=0.5, alpha=0.7, color=COLORS['grid'])
            ax_phi.set_axisbelow(True)
            ax_phi.set_xlabel("")
            ax_phi.set_title("Porosity\n(%)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
            ax_phi.set_ylabel("Depth (m)", fontsize=9, fontweight='bold')
            ax_phi.set_ylim(depth_max, depth_min)
            ax_phi.set_xlim(0, 40)
            
            # Set porosity axis ticks
            ax_phi.set_xticks([0, 10, 20, 30, 40])
            ax_phi.set_xticklabels(["0", "10", "20", "30", "40"])
            
            ax_phi.axvline(x=10, color='green', linestyle=':', 
                          linewidth=1, alpha=0.5, label='Good Porosity (>10%)')
            ax_phi.axvline(x=5, color='orange', linestyle=':', 
                          linewidth=1, alpha=0.5, label='Fair Porosity (5-10%)')
            ax_phi.legend(loc="upper right", fontsize=7, framealpha=0.9)
        else:
            ax_phi.text(0.5, 0.5, "Porosity\nData\nUnavailable", 
                       transform=ax_phi.transAxes, 
                       ha='center', va='center', fontsize=10)
            ax_phi.set_title("Porosity\n(%)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
        
        for spine in ax_phi.spines.values():
            spine.set_linewidth(1)
            spine.set_color('#333333')

        # ========== VSHALE TRACK ==========
        vshale, gr_clean, gr_shale = self.calculate_vshale(df)
        
        if vshale is not None:
            ax_vsh.plot(vshale * 100, df["Depth"],
                       color=COLORS['vshale'], 
                       linewidth=1.5, 
                       label="Vshale (Vsh)")
            
            for top, bottom, min_g, max_g in intervals:
                ax_vsh.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4)
            
            ax_vsh.set_facecolor(COLORS['background'])
            ax_vsh.grid(True, which='both', linestyle='--', 
                       linewidth=0.5, alpha=0.7, color=COLORS['grid'])
            ax_vsh.set_axisbelow(True)
            ax_vsh.set_xlabel("")
            ax_vsh.set_title("Shale Volume\n(%)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
            ax_vsh.set_ylabel("Depth (m)", fontsize=9, fontweight='bold')
            ax_vsh.set_ylim(depth_max, depth_min)
            ax_vsh.set_xlim(0, 100)
            
            # Set vshale axis ticks
            ax_vsh.set_xticks([0, 20, 40, 60, 80, 100])
            ax_vsh.set_xticklabels(["0", "20", "40", "60", "80", "100"])
            
            ax_vsh.axvline(x=50, color='red', linestyle=':', 
                          linewidth=1, alpha=0.5, label='Shale (>50%)')
            ax_vsh.axvline(x=30, color='orange', linestyle=':', 
                          linewidth=1, alpha=0.5, label='Sandy Shale (30-50%)')
            ax_vsh.axvline(x=10, color='green', linestyle=':', 
                          linewidth=1, alpha=0.5, label='Clean Sand (<10%)')
            
            ax_vsh.fill_betweenx(df["Depth"], 0, vshale * 100, 
                                where=(vshale * 100) > 50,
                                color=COLORS['shale_zone'], alpha=0.3, 
                                label='Shale Zone')
            ax_vsh.legend(loc="upper right", fontsize=7, framealpha=0.9)
        else:
            ax_vsh.text(0.5, 0.5, "Vshale\nData\nUnavailable", 
                       transform=ax_vsh.transAxes, 
                       ha='center', va='center', fontsize=10)
            ax_vsh.set_title("Shale Volume\n(%)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
        
        for spine in ax_vsh.spines.values():
            spine.set_linewidth(1)
            spine.set_color('#333333')

        # ========== WATER SATURATION TRACK ==========
        if porosity is not None:
            water_saturation = self.calculate_water_saturation(df, porosity, self.m_value, self.n_value)
            
            if water_saturation is not None:
                ax_sw.plot(water_saturation * 100, df["Depth"],
                          color=COLORS['water_saturation'], 
                          linewidth=1.5, 
                          label=f"Sw (m={self.m_value}, n={self.n_value})")
                
                for top, bottom, min_g, max_g in intervals:
                    ax_sw.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4)
                
                ax_sw.set_facecolor(COLORS['background'])
                ax_sw.grid(True, which='both', linestyle='--', 
                          linewidth=0.5, alpha=0.7, color=COLORS['grid'])
                ax_sw.set_axisbelow(True)
                ax_sw.set_xlabel("")
                ax_sw.set_title("Water Saturation\n(%)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
                ax_sw.set_ylabel("Depth (m)", fontsize=9, fontweight='bold')
                ax_sw.set_ylim(depth_max, depth_min)
                ax_sw.set_xlim(0, 100)
                
                # Set water saturation axis ticks
                ax_sw.set_xticks([0, 20, 40, 60, 80, 100])
                ax_sw.set_xticklabels(["0", "20", "40", "60", "80", "100"])
                
                ax_sw.axvline(x=50, color='green', linestyle=':', 
                            linewidth=1, alpha=0.5, label='Hydrocarbon (Sw<50%)')
                ax_sw.axvline(x=70, color='orange', linestyle=':', 
                            linewidth=1, alpha=0.5, label='Transition (50-70%)')
                ax_sw.axvline(x=90, color='red', linestyle=':', 
                            linewidth=1, alpha=0.5, label='Water (Sw>90%)')
                
                ax_sw.fill_betweenx(df["Depth"], 0, water_saturation * 100, 
                                   where=(water_saturation * 100) < 50,
                                   color='lightgreen', alpha=0.3, 
                                   label='Hydrocarbon Zone')
                ax_sw.legend(loc="upper right", fontsize=7, framealpha=0.9)
            else:
                ax_sw.text(0.5, 0.5, "Sw\nData\nUnavailable", 
                          transform=ax_sw.transAxes, 
                          ha='center', va='center', fontsize=10)
                ax_sw.set_title("Water Saturation\n(%)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
        else:
            ax_sw.text(0.5, 0.5, "Need Porosity\nfor Sw", 
                      transform=ax_sw.transAxes, 
                      ha='center', va='center', fontsize=10)
            ax_sw.set_title("Water Saturation\n(%)", fontsize=10, fontweight='bold', pad=8, color=COLORS['text'])
        
        for spine in ax_sw.spines.values():
            spine.set_linewidth(1)
            spine.set_color('#333333')

        # Create depth track
        fig_depth, ax_depth = create_depth_track(depth_min, depth_max, fig_height_inches, intervals)
        self.current_figures.append(fig_depth)
        self.current_axes.append(ax_depth)

        return (fig_depth, ax_depth, fig_gr, ax_gr, fig_nd, ax_nd, 
                fig_res, ax_res, fig_phi, ax_phi, fig_vsh, ax_vsh, fig_sw, ax_sw)

    def plot_and_identify(self, file_path):
        """Main method to plot and identify reservoirs"""
        self.clear_previous()

        if not file_path:
            toast("No file selected")
            return

        # Read LAS file
        df = read_las_file(file_path)
        if df is None:
            return
            
        self.df = df  # Store for later use

        # Prepare depth and range
        depth = df["Depth"]
        depth_min = depth.min()
        depth_max = depth.max()
        depth_range = depth_max - depth_min

        # Calculate cut-off
        gr_series = df["Gamma Ray"].dropna()
        if gr_series.empty:
            toast("No valid Gamma Ray data found.")
            return
        gr_min = gr_series.min()
        gr_max = gr_series.max()
        cut_off = (gr_max - gr_min) / 2.0 + gr_min
        self.cut_off = cut_off

        # Detect intervals
        in_zone = False
        start_depth = None
        end_depth = None
        min_gr = None
        max_gr = None
        intervals = []
        prev_depth = None
        
        for _, row in df.iterrows():
            d = row["Depth"]
            gr = row["Gamma Ray"]
            if pd.isna(gr):
                if in_zone:
                    in_zone = False
                    intervals.append((start_depth, prev_depth, min_gr, max_gr))
                continue

            if gr < cut_off:
                if not in_zone:
                    in_zone = True
                    start_depth = d
                    min_gr = gr
                    max_gr = gr
                else:
                    min_gr = min(min_gr, gr)
                    max_gr = max(max_gr, gr)
            else:
                if in_zone:
                    in_zone = False
                    intervals.append((start_depth, prev_depth, min_gr, max_gr))
            prev_depth = d

        # If ended while in zone
        if in_zone:
            intervals.append((start_depth, prev_depth, min_gr, max_gr))

        # Save detected intervals
        self.detected_intervals = intervals
        self.intervals = intervals

        # Update interval display
        self.update_interval_display()

        # Create enhanced plots
        pixels_per_meter = 1.8
        canvas_height = int(depth_range * pixels_per_meter)
        canvas_height = max(800, min(canvas_height, 20000))
        fig_height_inches = canvas_height / 100
        fig_height_inches = max(8, min(fig_height_inches, 100))

        # Create plots
        (fig_depth, ax_depth, fig_gr, ax_gr, fig_nd, ax_nd, 
         fig_res, ax_res, fig_phi, ax_phi, fig_vsh, ax_vsh, fig_sw, ax_sw) = \
            self.create_reservoir_plots(df, depth_min, depth_max, fig_height_inches, cut_off, intervals)

        # Create canvases
        box = self.ids.reservoir_box

        canvas_depth = FigureCanvasKivyAgg(fig_depth)
        canvas_depth.size_hint_y = None
        canvas_depth.height = canvas_height
        canvas_depth.size_hint_x = 0.10

        canvas_gr = FigureCanvasKivyAgg(fig_gr)
        canvas_gr.size_hint_y = None
        canvas_gr.height = canvas_height
        canvas_gr.size_hint_x = 0.15

        canvas_nd = FigureCanvasKivyAgg(fig_nd)
        canvas_nd.size_hint_y = None
        canvas_nd.height = canvas_height
        canvas_nd.size_hint_x = 0.15

        canvas_res = FigureCanvasKivyAgg(fig_res)
        canvas_res.size_hint_y = None
        canvas_res.height = canvas_height
        canvas_res.size_hint_x = 0.15

        canvas_phi = FigureCanvasKivyAgg(fig_phi)
        canvas_phi.size_hint_y = None
        canvas_phi.height = canvas_height
        canvas_phi.size_hint_x = 0.15

        canvas_vsh = FigureCanvasKivyAgg(fig_vsh)
        canvas_vsh.size_hint_y = None
        canvas_vsh.height = canvas_height
        canvas_vsh.size_hint_x = 0.15

        canvas_sw = FigureCanvasKivyAgg(fig_sw)
        canvas_sw.size_hint_y = None
        canvas_sw.height = canvas_height
        canvas_sw.size_hint_x = 0.15

        self.current_canvases = [canvas_depth, canvas_gr, canvas_nd, canvas_res, 
                                 canvas_phi, canvas_vsh, canvas_sw]

        # Add widgets
        box.clear_widgets()
        box.add_widget(canvas_depth)
        box.add_widget(canvas_gr)
        box.add_widget(canvas_nd)
        box.add_widget(canvas_res)
        box.add_widget(canvas_phi)
        box.add_widget(canvas_vsh)
        box.add_widget(canvas_sw)

    def reinterpret_with_new_parameters(self):
        """Re-plot with new m and n values WITHOUT clearing intervals"""
        if self.df is None:
            toast("No data loaded. Please upload a file first.")
            return
        
        # Get new m and n values
        try:
            self.m_value = float(self.ids.m_value.text)
        except:
            self.m_value = 2.0
            self.ids.m_value.text = "2.0"
            toast("Invalid m value. Using default: 2.0")
            
        try:
            self.n_value = float(self.ids.n_value.text)
        except:
            self.n_value = 2.0
            self.ids.n_value.text = "2.0"
            toast("Invalid n value. Using default: 2.0")
        
        # Re-plot with the same data but new parameters
        if self.df is not None and self.cut_off is not None and self.intervals:
            depth_min = self.df["Depth"].min()
            depth_max = self.df["Depth"].max()
            depth_range = depth_max - depth_min
            
            pixels_per_meter = 1.8
            canvas_height = int(depth_range * pixels_per_meter)
            canvas_height = max(800, min(canvas_height, 20000))
            fig_height_inches = canvas_height / 100
            fig_height_inches = max(8, min(fig_height_inches, 100))
            
            # Clear only plot widgets
            box = self.ids.reservoir_box
            box.clear_widgets()
            
            # Close matplotlib figures
            for fig in getattr(self, "current_figures", []):
                try:
                    plt.close(fig)
                except Exception:
                    pass
            self.current_figures = []
            self.current_axes = []
            self.current_canvases = []
            
            # Recreate plots with new parameters
            (fig_depth, ax_depth, fig_gr, ax_gr, fig_nd, ax_nd, 
             fig_res, ax_res, fig_phi, ax_phi, fig_vsh, ax_vsh, fig_sw, ax_sw) = \
                self.create_reservoir_plots(self.df, depth_min, depth_max, fig_height_inches, 
                                          self.cut_off, self.intervals)
            
            # Recreate canvases
            canvas_depth = FigureCanvasKivyAgg(fig_depth)
            canvas_depth.size_hint_y = None
            canvas_depth.height = canvas_height
            canvas_depth.size_hint_x = 0.10
            
            canvas_gr = FigureCanvasKivyAgg(fig_gr)
            canvas_gr.size_hint_y = None
            canvas_gr.height = canvas_height
            canvas_gr.size_hint_x = 0.15
            
            canvas_nd = FigureCanvasKivyAgg(fig_nd)
            canvas_nd.size_hint_y = None
            canvas_nd.height = canvas_height
            canvas_nd.size_hint_x = 0.15
            
            canvas_res = FigureCanvasKivyAgg(fig_res)
            canvas_res.size_hint_y = None
            canvas_res.height = canvas_height
            canvas_res.size_hint_x = 0.15
            
            canvas_phi = FigureCanvasKivyAgg(fig_phi)
            canvas_phi.size_hint_y = None
            canvas_phi.height = canvas_height
            canvas_phi.size_hint_x = 0.15
            
            canvas_vsh = FigureCanvasKivyAgg(fig_vsh)
            canvas_vsh.size_hint_y = None
            canvas_vsh.height = canvas_height
            canvas_vsh.size_hint_x = 0.15
            
            canvas_sw = FigureCanvasKivyAgg(fig_sw)
            canvas_sw.size_hint_y = None
            canvas_sw.height = canvas_height
            canvas_sw.size_hint_x = 0.15
            
            self.current_canvases = [canvas_depth, canvas_gr, canvas_nd, canvas_res, 
                                     canvas_phi, canvas_vsh, canvas_sw]
            
            # Add widgets back
            box.add_widget(canvas_depth)
            box.add_widget(canvas_gr)
            box.add_widget(canvas_nd)
            box.add_widget(canvas_res)
            box.add_widget(canvas_phi)
            box.add_widget(canvas_vsh)
            box.add_widget(canvas_sw)
            
            toast(f"Replotted with m={self.m_value}, n={self.n_value}")
        else:
            toast("Cannot reinterpret. Please load data first.")