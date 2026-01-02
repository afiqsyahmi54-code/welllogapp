# screens/interpretation_screen.py - Updated with working cards
from kivy.uix.screenmanager import Screen
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.app import MDApp
from kivymd.toast import toast

class InterpretationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def on_enter(self):
        """Update info when entering screen"""
        self.update_well_info()
    
    def update_well_info(self):
        """Update well information from welllog screen"""
        app = MDApp.get_running_app()
        try:
            well_screen = app.root.get_screen("welllog")
            well_name = well_screen.ids.well_name.text or "-"
            location = well_screen.ids.location.text or "-"
            depth_range = well_screen.ids.depth_range.text or "-"
            
            # Update info label if it exists
            if hasattr(self.ids, 'info_label'):
                self.ids.info_label.text = (
                    f"Well Name: {well_name}\n"
                    f"Location: {location}\n"
                    f"Depth Range: {depth_range}"
                )
        except Exception as e:
            print(f"Error updating well info: {e}")
    
    def show_vshale_info(self):
        app = MDApp.get_running_app()
        app.change_screen("vshale")
    
    def show_porosity_info(self):
        app = MDApp.get_running_app()
        app.change_screen("porosity")
    
    def show_water_saturation_info(self):
        app = MDApp.get_running_app()
        app.change_screen("watersaturation")
    
    def navigate_back(self):
        """Navigate back to welllog screen"""
        app = MDApp.get_running_app()
        app.change_screen("welllog")