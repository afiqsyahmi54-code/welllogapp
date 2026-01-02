"""
Android-compatible LAS file reader
Falls back to pure Python if lasio is not available
"""
import os
import pandas as pd
import numpy as np
from kivymd.toast import toast

def read_las_file(file_path):
    """Read LAS file and return formatted dataframe - Android compatible"""
    try:
        if not os.path.exists(file_path):
            toast("File does not exist")
            return None
        
        # Try to use lasio first (works on desktop)
        try:
            import lasio
            las = lasio.read(file_path)
            df = las.df().reset_index()
        except (ImportError, ModuleNotFoundError):
            # Fallback: pure Python LAS reader for Android
            print("lasio not available, using fallback reader")
            df = read_las_pure_python(file_path)
            
        if df is None or df.empty:
            toast("Failed to read LAS file")
            return None

        # Rename common curves
        rename_dict = {}
        for col in df.columns:
            col_upper = col.upper().strip()
            if "GR" in col_upper:
                rename_dict[col] = "Gamma Ray"
            elif "RHOB" in col_upper:
                rename_dict[col] = "Density"
            elif "NPHI" in col_upper:
                rename_dict[col] = "Neutron"
            elif "RES" in col_upper:
                rename_dict[col] = "Resistivity"
            elif "DEPT" in col_upper:
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
        print(f"Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def read_las_pure_python(file_path):
    """
    Pure Python LAS file reader (fallback for Android)
    Reads basic LAS ASCII format
    """
    try:
        data_dict = {}
        current_section = None
        curves_info = []
        data_started = False
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Section markers
                if line.startswith('~'):
                    current_section = line.split()[0][1:]  # Remove ~
                    continue
                
                # Parse curves section
                if current_section == 'C':
                    if ':' in line:
                        parts = line.split(':')
                        mnemonic = parts[0].strip().split()[0]
                        curves_info.append(mnemonic)
                
                # Parse data section
                if current_section == 'A' or data_started:
                    data_started = True
                    # Skip non-numeric lines
                    try:
                        values = [float(x) for x in line.split()]
                        if len(values) == len(curves_info):
                            for i, curve in enumerate(curves_info):
                                if curve not in data_dict:
                                    data_dict[curve] = []
                                data_dict[curve].append(values[i])
                    except ValueError:
                        continue
        
        # Convert to DataFrame
        if data_dict:
            df = pd.DataFrame(data_dict)
            return df
        else:
            return None
            
    except Exception as e:
        print(f"Error in pure Python LAS reader: {e}")
        return None