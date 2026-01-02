# screens/viewlog_screen.py - View log screen implementation
from kivy.uix.screenmanager import Screen
from kivy_garden.matplotlib import FigureCanvasKivyAgg
from utils.android_file_utils import read_las_file
import matplotlib.pyplot as plt
from kivymd.app import MDApp
from kivymd.toast import toast
import importlib

class ViewLogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_figures = []
        self.current_axes = []
        self.current_canvases = []

    def on_enter(self):
        """Update info when entering screen"""
        app = MDApp.get_running_app()
        try:
            well_screen = app.root.get_screen("welllog")
            well_name = well_screen.ids.well_name.text or "-"
            location = well_screen.ids.location.text or "-"
            depth_range = well_screen.ids.depth_range.text or "-"
            self.ids.info_label.text = f"Well Name: {well_name}\nLocation: {location}\nDepth Range: {depth_range}"
        except Exception:
            pass

        self.plot_logs(app.selected_file)

    def plot_logs(self, file_path):
        """Plot well logs from LAS file"""
        # Force reload of plot_utils to get latest changes
        import utils.plot_utils
        importlib.reload(utils.plot_utils)
        
        # Now import the functions
        from utils.plot_utils import create_welllog_plots, create_depth_track
        
        box = self.ids.box_area
        box.clear_widgets()
        self.current_figures = []
        self.current_axes = []
        self.current_canvases = []

        if not file_path:
            toast("No file selected")
            return

        # Read LAS file
        df = read_las_file(file_path)
        if df is None:
            return

        # DEBUG: Print data ranges
        print("=== DEBUG: Data Ranges ===")
        print(f"Gamma Ray min: {df['Gamma Ray'].min():.2f}, max: {df['Gamma Ray'].max():.2f}")
        print(f"Density min: {df['Density'].min():.2f}, max: {df['Density'].max():.2f}")
        print(f"Neutron min: {df['Neutron'].min():.2f}, max: {df['Neutron'].max():.2f}")
        print(f"Resistivity min: {df['Resistivity'].min():.2f}, max: {df['Resistivity'].max():.2f}")

        # Prepare depth and range
        depth_min = df["Depth"].min()
        depth_max = df["Depth"].max()
        depth_range = depth_max - depth_min

        # Calculate figure size
        pixels_per_meter = 2
        canvas_height = int(depth_range * pixels_per_meter)
        canvas_height = max(800, min(canvas_height, 20000))
        fig_height_inches = canvas_height / 100
        fig_height_inches = max(8, min(fig_height_inches, 100))

        # Create plots
        print("=== DEBUG: Creating plots ===")
        fig_gr, ax_gr, fig_nd, ax_nd, fig_res, ax_res = create_welllog_plots(
            df, depth_min, depth_max, fig_height_inches
        )
        
        # DEBUG: Print axis limits
        print(f"Gamma Ray xlim: {ax_gr.get_xlim()}")
        print(f"Density xlim: {ax_nd.get_xlim()}")
        
        if len(fig_nd.axes) > 1:
            twin_ax = fig_nd.axes[1]
            print(f"Neutron xlim: {twin_ax.get_xlim()}")
        
        print(f"Resistivity xlim: {ax_res.get_xlim()}")
        
        fig_depth, ax_depth = create_depth_track(depth_min, depth_max, fig_height_inches)

        # Store figures
        self.current_figures = [fig_depth, fig_gr, fig_nd, fig_res]
        self.current_axes = [ax_depth, ax_gr, ax_nd, ax_res]

        # Create canvases
        canvas_depth = FigureCanvasKivyAgg(fig_depth)
        canvas_depth.size_hint_y = None
        canvas_depth.height = canvas_height
        canvas_depth.size_hint_x = 0.15

        canvas_gr = FigureCanvasKivyAgg(fig_gr)
        canvas_gr.size_hint_y = None
        canvas_gr.height = canvas_height
        canvas_gr.size_hint_x = 0.28

        canvas_nd = FigureCanvasKivyAgg(fig_nd)
        canvas_nd.size_hint_y = None
        canvas_nd.height = canvas_height
        canvas_nd.size_hint_x = 0.28

        canvas_res = FigureCanvasKivyAgg(fig_res)
        canvas_res.size_hint_y = None
        canvas_res.height = canvas_height
        canvas_res.size_hint_x = 0.28

        self.current_canvases = [canvas_depth, canvas_gr, canvas_nd, canvas_res]

        # Add widgets
        box.clear_widgets()
        box.add_widget(canvas_depth)
        box.add_widget(canvas_gr)
        box.add_widget(canvas_nd)
        box.add_widget(canvas_res)