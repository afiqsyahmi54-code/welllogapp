# utils/file_utils.py
import lasio
import pandas as pd
import numpy as np
import os
from kivymd.toast import toast

def read_las_file(file_path):
    """Read LAS file and return formatted dataframe"""
    try:
        if not os.path.exists(file_path):
            toast("File does not exist")
            return None
        
        las = lasio.read(file_path)
        df = las.df().reset_index()

        # Rename common curves
        rename_dict = {}
        for col in df.columns:
            if "GR" in col.upper():
                rename_dict[col] = "Gamma Ray"
            elif "RHOB" in col.upper():
                rename_dict[col] = "Density"
            elif "NPHI" in col.upper():
                rename_dict[col] = "Neutron"
            elif "RES" in col.upper():
                rename_dict[col] = "Resistivity"
            elif "DEPT" in col.upper():
                rename_dict[col] = "Depth"

        df.rename(columns=rename_dict, inplace=True)

        # Check required columns
        required_cols = ["Depth", "Gamma Ray", "Neutron", "Density", "Resistivity"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            toast(f"Missing columns: {', '.join(missing_cols)}")
            return None
            
        return df
        
    except Exception as e:
        toast(f"Error reading LAS: {e}")
        return None