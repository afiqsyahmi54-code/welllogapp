# main.py - Main application entry point
import sys
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.filemanager import MDFileManager
import os
from datetime import datetime

# Debug: Print Python paths
print("Python executable:", sys.executable)  # Now this will work
print("Python version:", sys.version)
print("Current directory:", os.getcwd())

# Try to find the correct Python path
venv_python = r"C:\Users\afiqs\Degree\FYPII\backup\k_venv\Scripts\python.exe"
if os.path.exists(venv_python):
    print(f"Virtual environment Python found at: {venv_python}")
else:
    print("Virtual environment Python NOT found!")
    # Try to use current Python
    print(f"Using system Python: {sys.executable}")

# Import screen classes
from screens.start_screen import StartScreen
from screens.welllog_screen import WellLogScreen
from screens.viewlog_screen import ViewLogScreen
from screens.reservoir_screen import ReservoirScreen
from screens.interpretation_screen import InterpretationScreen
from screens.vshale_screen import VshaleScreen
from screens.porosity_screen import PorosityScreen
from screens.water_saturation_screen import WaterSaturationScreen

# Load all KV files
Builder.load_file("kv_files/start_screen.kv")
Builder.load_file("kv_files/welllog_screen.kv")
Builder.load_file("kv_files/viewlog_screen.kv")
Builder.load_file("kv_files/reservoir_screen.kv")
Builder.load_file("kv_files/interpretation_screen.kv")
Builder.load_file("kv_files/vshale_screen.kv")
Builder.load_file("kv_files/porosity_screen.kv")  
Builder.load_file("kv_files/water_saturation_screen.kv")      

class WellLogApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_file = None
        
        # Initialize file managers
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path
        )
        self.save_file_manager = MDFileManager(
            exit_manager=self.exit_save_manager,
            select_path=self.select_save_path,
            selector='folder'
        )
    
    def build(self):
        # Create screen manager
        sm = ScreenManager()
        
        # Add screens
        sm.add_widget(StartScreen(name="start"))
        sm.add_widget(WellLogScreen(name="welllog"))
        sm.add_widget(ViewLogScreen(name="viewlog"))
        sm.add_widget(ReservoirScreen(name="reservoir"))
        sm.add_widget(InterpretationScreen(name="interpretation"))
        sm.add_widget(VshaleScreen(name="vshale"))  
        sm.add_widget(PorosityScreen(name="porosity"))
        sm.add_widget(WaterSaturationScreen(name="water_saturation"))   
        
        return sm
    
    # ========== COMMON APP METHODS ==========
    
    def change_screen(self, screen_name):
        """Navigate to a different screen"""
        self.root.current = screen_name
    
    def goto_start(self, instance, touch):
        """Navigate to start screen on label click"""
        if instance.collide_point(*touch.pos):
            self.root.current = "start"
    
    def open_file_manager(self):
        """Open file picker for LAS files"""
        self.file_manager.show(os.path.expanduser("~"))
    
    def select_path(self, path):
        """Handle file selection"""
        self.selected_file = path
        from kivymd.toast import toast
        toast(f"Selected: {os.path.basename(path)}")
        
        # Update the file label in welllog screen
        screen = self.root.get_screen("welllog")
        screen.ids.selected_file_label.text = f"Selected: {os.path.basename(path)}"
        self.exit_manager()
    
    def exit_manager(self, *args):
        """Close file manager"""
        self.file_manager.close()
    
    def exit_save_manager(self, *args):
        """Close save file manager"""
        self.save_file_manager.close()
    
    def select_save_path(self, path):
        """Handle save folder selection"""
        self.save_pdf_to_path(path)
        self.exit_save_manager()
    
    def reset_fields(self):
        """Reset input fields in welllog screen"""
        screen = self.root.get_screen("welllog")
        screen.ids.well_name.text = ""
        screen.ids.location.text = ""
        screen.ids.depth_range.text = ""
        screen.ids.selected_file_label.text = "No file selected"
        self.selected_file = None
        from kivymd.toast import toast
        toast("Fields cleared")
    
    def view_log(self):
        """Navigate to view log screen"""
        well_screen = self.root.get_screen("welllog")
        view_screen = self.root.get_screen("viewlog")

        well_name = well_screen.ids.well_name.text or "-"
        location = well_screen.ids.location.text or "-"
        depth_range = well_screen.ids.depth_range.text or "-"

        view_screen.ids.info_label.text = (
            f"Well Name: {well_name}\n"
            f"Location: {location}\n"
            f"Depth Range: {depth_range}"
        )

        self.change_screen("viewlog")

    def open_interpretation(self):
        """Navigate to interpretation hub screen"""
        if not self.selected_file:
            from kivymd.toast import toast
            toast("Please upload a LAS file first")
            return

        # Just navigate — no info_label anymore
        self.change_screen("interpretation")

    def open_vshale(self):
        self.root.current = "vshale"

    def open_porosity(self):
        self.root.current = "porosity"
    
    def open_reservoir(self):
        """Navigate directly to ReservoirScreen"""
        if not self.selected_file:
            from kivymd.toast import toast
            toast("Please upload a LAS file first")
            return
            
        well_screen = self.root.get_screen("welllog")
        res_screen = self.root.get_screen("reservoir")
        well_name = well_screen.ids.well_name.text or "-"
        location = well_screen.ids.location.text or "-"
        depth_range = well_screen.ids.depth_range.text or "-"
        res_screen.ids.reservoir_info_label.text = (
            f"Well Name: {well_name}\nLocation: {location}\nDepth Range: {depth_range}"
        )
        self.change_screen("reservoir")
    
    def reinterpret_reservoir(self):
        """Call the reinterpret method in ReservoirScreen"""
        res_screen = self.root.get_screen("reservoir")
        res_screen.reinterpret_with_new_parameters()
    
    def save_as_pdf(self):
        """Save current screen plots as PDF"""
        current_screen_name = self.root.current
        screen_obj = self.root.get_screen(current_screen_name)

        if not hasattr(screen_obj, "current_figures") or not screen_obj.current_figures:
            from kivymd.toast import toast
            toast("No plots to save!")
            return

        self.save_file_manager.show(os.path.expanduser("~"))
        from kivymd.toast import toast
        toast("Select folder to save PDF")
    
    def save_pdf_to_path(self, folder_path):
        """Save PDF with 3 data tracks per page including all petrophysical elements"""
        current_screen_name = self.root.current
        screen_obj = self.root.get_screen(current_screen_name)

        if not hasattr(screen_obj, "current_figures") or not screen_obj.current_figures:
            from kivymd.toast import toast
            toast("No plots to save!")
            return

        try:
            well_screen = self.root.get_screen("welllog")
            well_name = well_screen.ids.well_name.text or "Unknown"
            location = well_screen.ids.location.text or "Unknown"
            depth_range = well_screen.ids.depth_range.text or "Unknown"

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"WellLog_{well_name}_{timestamp}.pdf"
            filepath = os.path.join(folder_path, filename)

            from matplotlib.backends.backend_pdf import PdfPages
            import matplotlib.pyplot as plt
            import numpy as np
            
            with PdfPages(filepath) as pdf:
                # Title page
                fig_title = plt.figure(figsize=(8.27, 11.69))  # A4 size in inches
                fig_title.text(0.5, 0.7, "WellLog Insight Report",
                              ha='center', va='center', fontsize=24, weight='bold')
                fig_title.text(0.5, 0.6, f"Well Name: {well_name}",
                              ha='center', va='center', fontsize=16)
                fig_title.text(0.5, 0.55, f"Location: {location}",
                              ha='center', va='center', fontsize=16)
                fig_title.text(0.5, 0.5, f"Depth Range: {depth_range}",
                              ha='center', va='center', fontsize=16)
                fig_title.text(0.5, 0.45, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                              ha='center', va='center', fontsize=12, style='italic')
                pdf.savefig(fig_title)
                plt.close(fig_title)

                # Get all figures from the screen
                all_figures = screen_obj.current_figures
                
                # Filter out depth track if present
                data_figures = []
                for fig in all_figures:
                    if fig.axes and "Depth" in fig.axes[0].get_title():
                        continue
                    data_figures.append(fig)
                
                if not data_figures:
                    data_figures = all_figures
                
                # Also get reservoir intervals if available (for shading)
                reservoir_intervals = []
                if hasattr(screen_obj, 'intervals') and screen_obj.intervals:
                    reservoir_intervals = screen_obj.intervals
                
                # Group data figures by 3 per page
                figures_per_page = 3
                
                for page_num in range(0, len(data_figures), figures_per_page):
                    # Create a new figure for this page
                    page_fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
                    
                    # Get the figures for this page
                    page_figures = data_figures[page_num:page_num + figures_per_page]
                    num_figures = len(page_figures)
                    
                    # Create 3 subplots for this page
                    for i in range(figures_per_page):
                        # Calculate position for this subplot
                        left = 0.07 + (i * 0.31)
                        width = 0.28
                        
                        if i < num_figures:
                            # Get the original figure
                            orig_fig = page_figures[i]
                            
                            if not orig_fig.axes:
                                continue
                                
                            orig_ax = orig_fig.axes[0]
                            
                            # Create new axis in the page figure
                            ax = page_fig.add_axes([left, 0.12, width, 0.75])
                            
                            # Get the original y-limits (depth increases downward)
                            y_min, y_max = orig_ax.get_ylim()
                            
                            # ===== EXTRACT AND RECREATE ALL VISUAL ELEMENTS =====
                            
                            # 1. First, add reservoir interval shading if applicable
                            if reservoir_intervals:
                                # Determine if this is Gamma Ray track
                                title = orig_ax.get_title()
                                is_gamma_ray = "Gamma Ray" in title
                                is_any_log = any(log_name in title for log_name in 
                                               ["Gamma Ray", "Density", "Neutron", "Resistivity", 
                                                "Porosity", "Shale Volume", "Water Saturation"])
                                
                                if is_any_log:
                                    # Add sand shading for reservoir intervals
                                    for top, bottom, min_gr, max_gr in reservoir_intervals:
                                        # FIX: Make sure shading respects y-axis orientation
                                        if y_min < y_max:  # Normal orientation
                                            ax.axhspan(top, bottom, color='#FFD166', alpha=0.3, label='_Reservoir' if top == reservoir_intervals[0][0] else "")
                                        else:  # Inverted orientation
                                            ax.axhspan(bottom, top, color='#FFD166', alpha=0.3, label='_Reservoir' if top == reservoir_intervals[0][0] else "")
                            
                            # 2. Extract and recreate lines (main data lines)
                            for line in orig_ax.get_lines():
                                x_data = line.get_xdata().copy()
                                y_data = line.get_ydata().copy()
                                
                                # Plot the line - FIX: Keep original orientation
                                ax.plot(x_data, y_data,
                                       color=line.get_color(),
                                       linewidth=line.get_linewidth(),
                                       label=line.get_label(),
                                       linestyle=line.get_linestyle())
                            
                            # 3. Extract and recreate vertical/horizontal lines
                            for line in orig_ax.get_lines():
                                x_data = line.get_xdata()
                                y_data = line.get_ydata()
                                
                                # Check if vertical line (cut-off lines)
                                if len(x_data) > 1 and np.allclose(x_data, x_data[0]):
                                    ax.axvline(x=x_data[0], 
                                              color=line.get_color(),
                                              linestyle=line.get_linestyle(),
                                              linewidth=line.get_linewidth(),
                                              label=line.get_label())
                            
                            # 4. Copy fill between areas (shale zones, hydrocarbon zones)
                            for collection in orig_ax.collections:
                                paths = collection.get_paths()
                                if paths:
                                    vertices = paths[0].vertices
                                    if len(vertices) > 0:
                                        # Sort vertices
                                        sorted_idx = vertices[:, 1].argsort()
                                        sorted_vertices = vertices[sorted_idx]
                                        x_fill = sorted_vertices[:, 0]
                                        y_fill = sorted_vertices[:, 1]
                                        
                                        facecolor = collection.get_facecolor()[0] if len(collection.get_facecolor()) > 0 else [0.5, 0.5, 0.5, 0.3]
                                        alpha = collection.get_alpha() or 0.3
                                        
                                        ax.fill_betweenx(y_fill, 0, x_fill,
                                                        facecolor=facecolor,
                                                        alpha=alpha,
                                                        label=collection.get_label())
                            
                            # 5. Copy title and labels
                            ax.set_title(orig_ax.get_title(), fontsize=11, fontweight='bold', pad=10)
                            ax.set_xlabel(orig_ax.get_xlabel(), fontsize=9)
                            ax.set_ylabel(orig_ax.get_ylabel(), fontsize=9)
                            
                            # ===== FIX DENSITY AXIS LIMIT (CRITICAL) =====
                            title = orig_ax.get_title().lower()

                            ax.set_ylim(y_min, y_max)

                            # Density–Neutron track
                            if "density" in title and len(orig_fig.axes) > 1:
                                ax.set_xlim(orig_ax.get_xlim())   # density scale (LEFT)
                            else:
                                ax.set_xlim(orig_ax.get_xlim())

                            if orig_ax.get_xscale() == 'log':
                                ax.set_xscale('log')
                                ax.set_xlim(orig_ax.get_xlim())   # IMPORTANT for resistivity

                            
                            # 7. Copy background color and grid
                            ax.set_facecolor(orig_ax.get_facecolor())
                            ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.3)
                            
                            # 8. DO NOT invert y-axis - keep original orientation
                            # The original already has correct depth orientation
                            # ===== FORCE DENSITY AXIS SCALE (LEFT) =====
                            title = orig_ax.get_title()

                            if "Density" in title:
                                ax.set_xlim(1.95, 2.95)        # RHOB scale
                                ax.set_xlabel("Density (g/cm³)", fontsize=9)

                            elif "Gamma Ray" in title:
                                ax.set_xlim(orig_ax.get_xlim())

                            elif "Resistivity" in title:
                                ax.set_xscale("log")
                                ax.set_xlim(orig_ax.get_xlim())

                            # 9. Add legend if exists
                            if orig_ax.get_legend():
                                handles, labels = ax.get_legend_handles_labels()
                                if handles and labels:
                                    # Remove duplicate labels
                                    unique_labels = []
                                    unique_handles = []
                                    seen_labels = set()
                                    for handle, label in zip(handles, labels):
                                        if label not in seen_labels and label and not label.startswith('_'):
                                            unique_labels.append(label)
                                            unique_handles.append(handle)
                                            seen_labels.add(label)
                                    
                                    if unique_handles:
                                        ax.legend(unique_handles, unique_labels, 
                                                 loc='upper right', fontsize=8, framealpha=0.9)
                            
                            # ===== HANDLE DENSITY–NEUTRON TWIN AXIS (FIXED & SEPARATE) =====
                            if len(orig_fig.axes) > 1:
                                twin_orig = orig_fig.axes[1]
                                twin_ax = ax.twinx()

                                # Plot neutron
                                for line in twin_orig.get_lines():
                                    twin_ax.plot(
                                        line.get_xdata(),
                                        line.get_ydata(),
                                        color=line.get_color(),
                                        linewidth=line.get_linewidth(),
                                        linestyle=line.get_linestyle(),
                                        label=line.get_label()
                                    )

                                # Match depth orientation
                                twin_ax.set_ylim(ax.get_ylim())

                                # Neutron scale (RIGHT)
                                twin_ax.set_xlim(twin_orig.get_xlim())
                                twin_ax.set_xlabel(twin_orig.get_xlabel(), fontsize=9)
                                twin_ax.grid(False)

                            # ===== LEGEND (MERGED, AFTER BOTH AXES EXIST) =====
                            h1, l1 = ax.get_legend_handles_labels()
                            h2, l2 = twin_ax.get_legend_handles_labels() if len(orig_fig.axes) > 1 else ([], [])

                            handles = h1 + h2
                            labels = l1 + l2

                            unique = dict(zip(labels, handles))
                            if unique:
                                ax.legend(
                                    unique.values(),
                                    unique.keys(),
                                    loc="upper right",
                                    fontsize=8,
                                    framealpha=0.9
                                )
                        else:
                            # Empty track for alignment
                            ax = page_fig.add_axes([left, 0.12, width, 0.75])
                            ax.axis('off')
                            ax.text(0.5, 0.5, "No Data", 
                                   transform=ax.transAxes,
                                   ha='center', va='center', fontsize=12,
                                   style='italic', color='gray')
                    
                    # Add page information
                    page_num_display = (page_num // figures_per_page) + 1
                    total_pages = (len(data_figures) + figures_per_page - 1) // figures_per_page
                    
                    # Add petrophysical parameters if available
                    if hasattr(screen_obj, 'm_value') and hasattr(screen_obj, 'n_value'):
                        params_text = f"Archie Parameters: m={screen_obj.m_value:.1f}, n={screen_obj.n_value:.1f}"
                        page_fig.text(0.5, 0.06, params_text,
                                     ha='center', fontsize=9, style='italic')
                    
                    # Add reservoir interval info if available
                    if reservoir_intervals and page_num == 0:  # Only on first page
                        interval_text = f"Reservoir Intervals Detected: {len(reservoir_intervals)}"
                        page_fig.text(0.5, 0.04, interval_text,
                                     ha='center', fontsize=9, style='italic')
                    
                    page_fig.text(0.5, 0.02, f"Page {page_num_display} of {total_pages}", 
                                 ha='center', fontsize=10, style='italic')
                    page_fig.text(0.02, 0.98, f"Well: {well_name}", 
                                 ha='left', fontsize=9, style='italic', fontweight='bold')
                    
                    # Add track numbers
                    start_track = page_num + 1
                    end_track = min(page_num + figures_per_page, len(data_figures))
                    page_fig.text(0.98, 0.98, f"Tracks {start_track}-{end_track}", 
                                 ha='right', fontsize=9, style='italic')
                    
                    # Save page to PDF
                    pdf.savefig(page_fig, bbox_inches='tight')
                    plt.close(page_fig)
                
                # ===== ADD IMPROVED PETROPHYSICAL SUMMARY PAGE =====
                summary_fig = plt.figure(figsize=(8.5, 11))
                
                # Title
                summary_fig.text(0.5, 0.95, "PETROPHYSICAL ANALYSIS REPORT",
                                ha='center', va='center', fontsize=22, weight='bold')
                
                # Well Information Section
                summary_fig.text(0.1, 0.88, "WELL INFORMATION", fontsize=14, weight='bold')
                summary_fig.text(0.15, 0.85, f"• Well Name: {well_name}", fontsize=11)
                summary_fig.text(0.15, 0.82, f"• Location: {location}", fontsize=11)
                summary_fig.text(0.15, 0.79, f"• Depth Range: {depth_range}", fontsize=11)
                summary_fig.text(0.15, 0.76, f"• Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fontsize=11)
                
                # Analysis Parameters Section
                y_pos = 0.72
                summary_fig.text(0.1, y_pos, "ANALYSIS PARAMETERS", fontsize=14, weight='bold')
                y_pos -= 0.03
                
                # Archie Parameters
                if hasattr(screen_obj, 'm_value') and hasattr(screen_obj, 'n_value'):
                    summary_fig.text(0.15, y_pos, "Archie Equation Parameters:", fontsize=12, weight='bold')
                    y_pos -= 0.025
                    summary_fig.text(0.2, y_pos, f"• Cementation factor (m) = {screen_obj.m_value:.2f}", fontsize=11)
                    y_pos -= 0.025
                    summary_fig.text(0.2, y_pos, f"• Saturation exponent (n) = {screen_obj.n_value:.2f}", fontsize=11)
                    y_pos -= 0.025
                    summary_fig.text(0.2, y_pos, f"• Formation water resistivity (Rw) = 0.1 ohm.m", fontsize=11)
                    y_pos -= 0.04
                
                # Cut-off Parameters
                summary_fig.text(0.15, y_pos, "Cut-off Values:", fontsize=12, weight='bold')
                y_pos -= 0.025
                summary_fig.text(0.2, y_pos, "• Gamma Ray cut-off: Automatic (50th percentile)", fontsize=11)
                y_pos -= 0.025
                summary_fig.text(0.2, y_pos, "• Porosity cut-off: >10% (Good), 5-10% (Fair)", fontsize=11)
                y_pos -= 0.025
                summary_fig.text(0.2, y_pos, "• Vshale cut-off: <10% (Clean), 10-50% (Shaly), >50% (Shale)", fontsize=11)
                y_pos -= 0.025
                summary_fig.text(0.2, y_pos, "• Water Saturation cut-off: <50% (Hydrocarbon)", fontsize=11)
                y_pos -= 0.04
                
                # Reservoir Analysis Section
                if reservoir_intervals:
                    summary_fig.text(0.1, y_pos, "RESERVOIR ANALYSIS", fontsize=14, weight='bold')
                    y_pos -= 0.03
                    
                    summary_fig.text(0.15, y_pos, f"Total Reservoir Intervals Detected: {len(reservoir_intervals)}", 
                                    fontsize=12, weight='bold')
                    y_pos -= 0.03
                    
                    # Show first 8 intervals
                    max_intervals = min(8, len(reservoir_intervals))
                    for idx, (top, bottom, min_gr, max_gr) in enumerate(reservoir_intervals[:max_intervals]):
                        thickness = bottom - top
                        gr_range = f"GR: {min_gr:.0f}-{max_gr:.0f} gAPI" if min_gr and max_gr else ""
                        summary_fig.text(0.2, y_pos, 
                                       f"{idx+1}. Depth: {top:.1f}-{bottom:.1f} m | Thickness: {thickness:.1f} m | {gr_range}",
                                       fontsize=10)
                        y_pos -= 0.025
                    
                    if len(reservoir_intervals) > max_intervals:
                        summary_fig.text(0.2, y_pos, 
                                       f"... and {len(reservoir_intervals) - max_intervals} more intervals",
                                       fontsize=10, style='italic')
                        y_pos -= 0.03
                    
                    # Calculate statistics
                    total_thickness = sum(bottom - top for top, bottom, _, _ in reservoir_intervals)
                    avg_thickness = total_thickness / len(reservoir_intervals) if reservoir_intervals else 0
                    summary_fig.text(0.15, y_pos, 
                                   f"Total Net Pay: {total_thickness:.1f} m | Average Thickness: {avg_thickness:.1f} m",
                                   fontsize=11, weight='bold')
                    y_pos -= 0.04
                
                # Methodology Section
                summary_fig.text(0.1, y_pos, "METHODOLOGY", fontsize=14, weight='bold')
                y_pos -= 0.03
                
                methodology_points = [
                    "1. Gamma Ray Analysis:",
                    "   • Reservoir intervals identifiedusing statistical cut-off (50th percentile)",
                    "   • Clean sand: GR < cut-off, Shale: GR > cut-off",
                    "",
                    "2. Porosity Calculation:",
                    "   • Density-Neutron crossplot method",
                    "   • Matrix density: 2.65 g/cm³ (sandstone)",
                    "   • Fluid density: 1.0 g/cm³ (fresh water)",
                    "",
                    "3. Shale Volume (Vshale):",
                    "   • Linear method from Gamma Ray",
                    "   • GR_clean: 10th percentile, GR_shale: 90th percentile",
                    "",
                    "4. Water Saturation (Sw):",
                    "   • Archie's equation: Sw = (a*Rw/(Φ^m*Rt))^(1/n)",
                    "   • Where a=0.62, Rw=0.1 ohm.m",
                    "",
                    "5. Hydrocarbon Identification:",
                    "   • Sw < 50%: Potential hydrocarbon zone",
                    "   • Sw > 90%: Water zone",
                    "   • 50% < Sw < 90%: Transition zone"
                ]
                
                for point in methodology_points:
                    if point:
                        if point.startswith("   •"):
                            summary_fig.text(0.2, y_pos, point, fontsize=9)
                        elif point.endswith(":"):
                            summary_fig.text(0.15, y_pos, point, fontsize=10, weight='bold')
                        else:
                            summary_fig.text(0.15, y_pos, point, fontsize=9)
                    y_pos -= 0.025
                
                # Quality Control Section
                y_pos -= 0.02
                summary_fig.text(0.1, y_pos, "QUALITY CONTROL NOTES", fontsize=14, weight='bold')
                y_pos -= 0.03
                
                qc_notes = [
                    "• All calculations based on provided LAS file data",
                    "• Check for missing or erroneous log data before analysis",
                ]
                
                for note in qc_notes:
                    summary_fig.text(0.15, y_pos, note, fontsize=9)
                    y_pos -= 0.025
                
                pdf.savefig(summary_fig, bbox_inches='tight')
                plt.close(summary_fig)

            
            from kivymd.toast import toast
            toast(f"PDF report generated successfully!")
            
        except Exception as e:
            from kivymd.toast import toast
            toast(f"Error saving PDF: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    WellLogApp().run()