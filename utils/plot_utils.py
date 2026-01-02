# utils/plot_utils.py - Plotting utilities with consistent grids
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from utils.constants import COLORS

# ========== HELPER FUNCTIONS FOR CONSISTENT STYLING ==========

def apply_consistent_grid(ax):
    """Apply consistent grid styling to an axis"""
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7, color=COLORS['grid'])
    ax.set_axisbelow(True)  # Grid behind data
    
    # Add minor grid
    ax.minorticks_on()
    ax.grid(True, which='minor', linestyle=':', linewidth=0.3, alpha=0.4, color=COLORS['grid'])
    
    return ax

def apply_consistent_style(ax):
    """Apply consistent styling to an axis"""
    # Set background
    ax.set_facecolor(COLORS['background'])
    
    # Add border
    for spine in ax.spines.values():
        spine.set_linewidth(1)
        spine.set_color('#333333')
    
    return ax

# ========== MAIN PLOTTING FUNCTIONS ==========

def create_consistent_plot(df, depth_min, depth_max, fig_height_inches, show_reservoir=False, cut_off=None, intervals=None):
    """Create plots with consistent styling"""
    fig_gr, ax_gr = plt.subplots(figsize=(4, fig_height_inches))
    fig_nd, ax_nd = plt.subplots(figsize=(4, fig_height_inches))
    fig_res, ax_res = plt.subplots(figsize=(4, fig_height_inches))

    plt.style.use('default')
    
    # ========== GAMMA RAY PLOT ==========
    ax_gr.plot(df["Gamma Ray"], df["Depth"], 
              color=COLORS['gamma_ray'], 
              linewidth=1.5, 
              label="Gamma Ray")
    
    if cut_off is not None:
        ax_gr.axvline(x=cut_off, color=COLORS['cutoff_line'], 
                     linestyle='--', linewidth=2, 
                     label=f"Cut-off: {cut_off:.1f} gAPI")
    
    if intervals:
        for top, bottom, min_g, max_g in intervals:
            ax_gr.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4, 
                         label='Reservoir' if top == intervals[0][0] else "")
    
    ax_gr.set_xlabel("")
    ax_gr.set_title("Gamma Ray\n(gAPI)", fontsize=11, fontweight='bold', pad=10, color=COLORS['text'])
    ax_gr.set_ylabel("Depth (m)", fontsize=10, fontweight='bold')
    ax_gr.set_ylim(depth_max, depth_min)
    
    # Set Gamma Ray axis range and ticks
    ax_gr.set_xlim(0, 200)
    ax_gr.set_xticks([0, 50, 100, 150, 200])
    ax_gr.set_xticklabels(["0", "50", "100", "150", "200"])
    
    # Apply consistent styling
    ax_gr = apply_consistent_style(ax_gr)
    ax_gr = apply_consistent_grid(ax_gr)
    
    if not show_reservoir and not intervals:
        gr_median = df["Gamma Ray"].median()
        ax_gr.fill_betweenx(df["Depth"], 0, df["Gamma Ray"], 
                          where=df["Gamma Ray"] < gr_median,
                          color=COLORS['sand'], alpha=0.3, 
                          label='Low GR (Potential Sand)')
    
    ax_gr.legend(loc="upper right", fontsize=8, framealpha=0.9)

    # ========== NEUTRON-DENSITY PLOT ==========
    ax_nd.plot(df["Density"], df["Depth"], 
              color=COLORS['density'], 
              linewidth=1.5, 
              label="Density (RHOB)")
    
    if intervals:
        for top, bottom, min_g, max_g in intervals:
            ax_nd.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4)
    
    ax_nd.set_xlabel("")
    ax_nd.set_title("Density / Neutron\n(g/cm³)    (v/v)", 
                   fontsize=11, fontweight='bold', pad=10, color=COLORS['text'])
    ax_nd.set_ylim(depth_max, depth_min)
    
    # Set Density axis range and ticks
    ax_nd.set_xlim(1.85, 2.85)
    ax_nd.set_xticks([1.85, 2.0, 2.2, 2.4, 2.6, 2.85])
    ax_nd.set_xticklabels(["1.85", "2.0", "2.2", "2.4", "2.6", "2.85"])
    
    ax_nd.set_ylabel("Depth (m)", fontsize=10, fontweight='bold')
    
    # Apply consistent styling
    ax_nd = apply_consistent_style(ax_nd)
    ax_nd = apply_consistent_grid(ax_nd)

    # Neutron plot on twin axis
    twin_ax = ax_nd.twiny()
    twin_ax.plot(df["Neutron"], df["Depth"], 
                color=COLORS['neutron'], 
                linewidth=1.5, 
                linestyle="-", 
                label="Neutron (NPHI)")
    
    twin_ax.set_xlabel("")
    
    # Set Neutron axis range and ticks
    twin_ax.set_xlim(0, 0.45)
    twin_ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.45])
    twin_ax.set_xticklabels(["0", "0.1", "0.2", "0.3", "0.4", "0.45"])
    
    # Style the twin axis
    twin_ax.spines['top'].set_color(COLORS['neutron'])
    twin_ax.xaxis.label.set_color(COLORS['neutron'])
    twin_ax.tick_params(axis='x', colors=COLORS['neutron'])
    twin_ax.grid(False)  # Don't grid the twin axis

    handles1, labels1 = ax_nd.get_legend_handles_labels()
    handles2, labels2 = twin_ax.get_legend_handles_labels()
    all_handles = handles1 + handles2
    all_labels = labels1 + labels2
    ax_nd.legend(all_handles, all_labels, loc="upper right", fontsize=8, framealpha=0.9)

    # ========== RESISTIVITY PLOT ==========
    ax_res.semilogx(df["Resistivity"], df["Depth"], 
                   color=COLORS['resistivity'], 
                   linewidth=1.5, 
                   label="Resistivity")
    
    if intervals:
        for top, bottom, min_g, max_g in intervals:
            ax_res.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4)
    
    ax_res.set_xscale("log")
    ax_res.set_xlabel("")
    ax_res.set_title("Resistivity\n(ohm.m)", fontsize=11, fontweight='bold', pad=10, color=COLORS['text'])
    ax_res.set_ylabel("Depth (m)", fontsize=10, fontweight='bold')
    ax_res.set_ylim(depth_max, depth_min)
    
    # Set Resistivity axis range and ticks
    ax_res.set_xlim(0.2, 200)
    ax_res.set_xticks([0.2, 1, 10, 100, 200])
    ax_res.set_xticklabels(["0.2", "1", "10", "100", "200"])
    
    # Apply consistent styling
    ax_res = apply_consistent_style(ax_res)
    ax_res = apply_consistent_grid(ax_res)
    
    # Add resistivity reference lines with consistent style
    ax_res.axvline(x=10, color='blue', linestyle=':', 
                  linewidth=1, alpha=0.5, label='Water Baseline')
    ax_res.axvline(x=50, color='green', linestyle=':', 
                  linewidth=1, alpha=0.5, label='Pay Indicator')
    
    ax_res.legend(loc="upper right", fontsize=8, framealpha=0.9)

    return fig_gr, ax_gr, fig_nd, ax_nd, fig_res, ax_res

def create_depth_track(depth_min, depth_max, fig_height_inches, intervals=None):
    """Create depth track with units and consistent styling"""
    fig_depth, ax_depth = plt.subplots(figsize=(1.5, fig_height_inches))
    
    ax_depth.set_ylim(depth_max, depth_min)
    ax_depth.set_xlim(0, 1)
    ax_depth.set_ylabel("")
    ax_depth.yaxis.tick_right()
    ax_depth.yaxis.set_label_position("right")
    ax_depth.set_xticks([])
    ax_depth.set_xticklabels([])
    
    # Apply consistent styling
    ax_depth = apply_consistent_style(ax_depth)
    
    # Set specific grid for depth track (vertical only)
    ax_depth.grid(True, axis='y', which='major', 
                 linestyle='--', linewidth=0.5, alpha=0.3)
    ax_depth.grid(True, axis='y', which='minor', 
                 linestyle=':', linewidth=0.3, alpha=0.2)
    
    # Shade reservoir intervals if provided
    if intervals:
        for top, bottom, min_g, max_g in intervals:
            ax_depth.axhspan(top, bottom, color=COLORS['sand'], alpha=0.4)
    
    ax_depth.set_title("Depth\n(m)", fontsize=12, fontweight='bold', pad=15, color=COLORS['text'])
    
    # Add depth markers every 20m
    depth_interval = 20
    for depth_marker in range(int(depth_min), int(depth_max) + 1, depth_interval):
        if depth_min <= depth_marker <= depth_max:
            ax_depth.text(0.5, depth_marker, f"{depth_marker}", 
                        ha='center', va='center', 
                        fontsize=8, color=COLORS['depth_marker'],
                        fontweight='bold')
    
    # Set y-axis minor ticks every 5m
    ax_depth.yaxis.set_minor_locator(plt.MultipleLocator(5))

    return fig_depth, ax_depth

# ========== BACKWARD COMPATIBILITY FUNCTIONS ==========

def create_welllog_plots(df, depth_min, depth_max, fig_height_inches, show_reservoir=False, cut_off=None, intervals=None):
    """Legacy function - uses new consistent styling"""
    return create_consistent_plot(df, depth_min, depth_max, fig_height_inches, show_reservoir, cut_off, intervals)