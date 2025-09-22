
"""
fold_debug.py

Funzioni di debug e visualizzazione per fold_detection.py.
Contiene plotting e stampe diagnostiche.
"""

import matplotlib.pyplot as plt
import numpy as np
import os


def save_fold_profile_debug(filtered_profiles, mean_profile, std_profile, x_axis, x_final, roi, debug_dir, accumulated_std_profile=None, detection_method=None, second_derivative=None):
    """Enhanced fold profile visualization with anomaly detection analysis."""
    os.makedirs(debug_dir, exist_ok=True)

    # Create multi-panel plot if we have anomaly data
    if accumulated_std_profile is not None:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # Panel 1: Traditional profile analysis
        for prof in filtered_profiles:
            ax1.plot(x_axis, prof, alpha=0.3, color="gray", linewidth=0.5)
        ax1.plot(x_axis, mean_profile, "r-", linewidth=2, label="Mean Profile")
        ax1.fill_between(x_axis, mean_profile - std_profile, mean_profile + std_profile,
                        color="red", alpha=0.2, label="±1σ Uncertainty")
        ax1.axvline(x_final, color="blue", linestyle="--", linewidth=2, label=f"Final Fold @ {x_final}")
        ax1.set_title(f"Traditional Profile Analysis ({len(filtered_profiles)} samples)")
        ax1.set_xlabel("X Position (pixels)")
        ax1.set_ylabel("Brightness")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Panel 2: ANOMALY PROFILES PLOT WITH SECOND DERIVATIVE!
        ax2_twin = ax2.twinx()  # Create twin axis for second derivative

        # Plot accumulated std profile
        line1 = ax2.plot(x_axis, accumulated_std_profile, "purple", linewidth=3, label="Accumulated Std Profile")
        ax2.axhline(np.mean(accumulated_std_profile), color="orange", linestyle=":",
                   label=f"Average: {np.mean(accumulated_std_profile):.2f}")

        # Plot second derivative on twin axis
        if second_derivative is not None:
            line2 = ax2_twin.plot(x_axis, second_derivative, "cyan", linewidth=2, alpha=0.8, label="2nd Derivative")
            ax2_twin.axhline(0, color="gray", linestyle="-", alpha=0.5, label="Zero Line")

            # Mark zero crossings
            if zero_crossings is not None and len(zero_crossings) > 0:
                crossing_x = [x_axis[0] + zc for zc in zero_crossings if 0 <= zc < len(x_axis)]
                crossing_y = [second_derivative[zc] for zc in zero_crossings if 0 <= zc < len(second_derivative)]
                ax2_twin.scatter(crossing_x, [0] * len(crossing_x), color="red", s=80, zorder=10,
                               marker="x", linewidths=3, label=f"Zero Crossings ({len(zero_crossings)})")

        if x_anomaly is not None:
            ax2.axvline(x_anomaly, color="magenta", linestyle="-", linewidth=3,
                       label=f"Selected Crossing @ {x_anomaly}")
            # Highlight the anomaly region
            anomaly_pos = x_anomaly - x_axis[0]
            if 0 <= anomaly_pos < len(accumulated_std_profile):
                ax2.scatter([x_anomaly], [accumulated_std_profile[anomaly_pos]],
                          color="magenta", s=100, zorder=5)

        ax2.set_title(f"🔍 ANOMALY DETECTION: Accumulated Std + Zero Crossings")
        ax2.set_xlabel("X Position (pixels)")
        ax2.set_ylabel("Accumulated Std (Anomaly Strength)", color="purple")
        ax2_twin.set_ylabel("2nd Derivative (Curvature)", color="cyan")

        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=8)
        ax2.grid(True, alpha=0.3)

        # Panel 3: Method comparison
        ax3.plot(x_axis, mean_profile, "b-", linewidth=2, alpha=0.7, label="Mean Profile")
        ax3.axvline(x_final, color="blue", linestyle="--", linewidth=3,
                   label=f"Final Detection @ {x_final}")

        if x_anomaly is not None and x_anomaly != x_final:
            ax3.axvline(x_anomaly, color="magenta", linestyle=":", linewidth=2,
                       label=f"Anomaly Method @ {x_anomaly}")

        ax3.set_title(f"Detection Method: {detection_method.upper() if detection_method else 'Unknown'}")
        ax3.set_xlabel("X Position (pixels)")
        ax3.set_ylabel("Brightness")
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Panel 4: Statistics and analysis
        ax4.axis('off')
        stats_text = f"""
        FOLD DETECTION ANALYSIS
        ═══════════════════════════════

        Detection Method: {detection_method.upper() if detection_method else 'Unknown'}
        Final Position: {x_final} px

        Anomaly Analysis:
        • Anomaly Position: {x_anomaly if x_anomaly else 'None'} px
        • Anomaly Strength: {anomaly_strength:.2f}x if anomaly_strength else 'N/A'
        • Threshold: 3.0x average
        • Decision: {'ANOMALY' if anomaly_strength and anomaly_strength > 3.0 else 'PARABOLIC'}

        Profile Statistics:
        • Total Samples: {len(filtered_profiles)}
        • Mean Brightness: {np.mean(mean_profile):.1f} ± {np.std(mean_profile):.1f}
        • Std Range: {np.min(std_profile):.2f} - {np.max(std_profile):.2f}
        • Accumulated Std Range: {np.min(accumulated_std_profile):.2f} - {np.max(accumulated_std_profile):.2f}

        Method Comparison:
        • Anomaly vs Parabolic Diff: {abs(x_anomaly - x_final) if x_anomaly else 'N/A'} px
        • Agreement: {'HIGH' if x_anomaly and abs(x_anomaly - x_final) < 5 else 'LOW' if x_anomaly else 'N/A'}
        """

        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

        plt.tight_layout()
        plt.savefig(os.path.join(debug_dir, "fold_profile_anomaly_debug.png"), dpi=150, bbox_inches='tight')
        plt.close(fig)

    # Always save the simple version for compatibility
    fig_simple, ax = plt.subplots(figsize=(10, 5))
    for prof in filtered_profiles:
        ax.plot(x_axis, prof, alpha=0.3, color="gray")
    ax.plot(x_axis, mean_profile, "r-", label="Mean")
    ax.fill_between(x_axis, mean_profile - std_profile, mean_profile + std_profile,
                    color="red", alpha=0.2, label="Std")
    ax.axvline(x_final, color="blue", linestyle="--", linewidth=2, label=f"Fold @ {x_final}")
    ax.legend()
    ax.set_title("Fold profile detection")
    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, "fold_profile_debug.png"), dpi=150)
    plt.close(fig_simple)

    # Save candidates analysis plot if debug info available
    if candidate_debug_info is not None:
        save_candidates_debug(candidate_debug_info, x_axis, accumulated_std_profile, debug_dir)


def save_candidates_debug(candidate_debug_info, x_axis, accumulated_std_profile, debug_dir):
    """Debug visualization for stability-based ROI detection."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))

    # Panel 1: Variance analysis for lateral boundary detection
    mean_profile = candidate_debug_info.get('mean_profile', np.zeros(len(x_axis)))
    profile_variance = candidate_debug_info.get('profile_variance', np.zeros(len(x_axis)))
    smoothed_variance = candidate_debug_info.get('smoothed_variance', np.zeros(len(x_axis)))
    variance_threshold = candidate_debug_info.get('variance_threshold', 0)
    lateral_boundaries = candidate_debug_info.get('lateral_boundaries', (0, len(x_axis)))

    ax1.plot(x_axis, mean_profile, 'red', linewidth=2, label='Mean Profile')
    ax1_twin = ax1.twinx()
    ax1_twin.plot(x_axis, profile_variance, 'gray', linewidth=1, alpha=0.5, label='Raw Variance')
    ax1_twin.plot(x_axis, smoothed_variance, 'blue', linewidth=2, label='Smoothed Variance')
    ax1_twin.axhline(variance_threshold, color='orange', linestyle='--',
                     label=f'Variance Threshold: {variance_threshold:.1f}')

    # Mark low variance regions and selected stable region
    left_boundary, right_boundary = lateral_boundaries
    low_variance_regions = candidate_debug_info.get('low_variance_regions', [])

    # Mark all low variance regions
    for i, (start, end) in enumerate(low_variance_regions):
        color = 'green' if (start, end) == (left_boundary, right_boundary) else 'lightgreen'
        alpha = 0.5 if (start, end) == (left_boundary, right_boundary) else 0.3
        label = f'Selected Stable ({start}-{end})' if (start, end) == (left_boundary, right_boundary) else (
            'Other Low-Variance' if i == 0 and (start, end) != (left_boundary, right_boundary) else '')
        ax1.axvspan(x_axis[0] + start, x_axis[0] + end, alpha=alpha, color=color, label=label)

    # Mark high variance regions (outside all low variance regions)
    if low_variance_regions:
        # Mark high variance at start if first region doesn't start at 0
        if low_variance_regions[0][0] > 0:
            ax1.axvspan(x_axis[0], x_axis[0] + low_variance_regions[0][0], alpha=0.2, color='red',
                       label='High Variance')

        # Mark high variance between regions
        for i in range(len(low_variance_regions) - 1):
            end_current = low_variance_regions[i][1]
            start_next = low_variance_regions[i + 1][0]
            if start_next > end_current:
                ax1.axvspan(x_axis[0] + end_current, x_axis[0] + start_next, alpha=0.2, color='red')

        # Mark high variance at end if last region doesn't end at roi_length
        if low_variance_regions[-1][1] < len(x_axis):
            ax1.axvspan(x_axis[0] + low_variance_regions[-1][1], x_axis[-1], alpha=0.2, color='red')

    ax1.set_ylabel('Mean Brightness', color='red')
    ax1_twin.set_ylabel('Profile Variance', color='blue')
    ax1.set_title('Lateral Boundary Detection via Variance Analysis')

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    ax1.grid(True, alpha=0.3)

    # Panel 2: Refined ROI and valley detection
    refined_roi = candidate_debug_info.get('refined_roi', (0, len(accumulated_std_profile)))
    valley_pos = candidate_debug_info.get('valley_pos')
    valley_value = candidate_debug_info.get('valley_value')
    roi_avg_value = candidate_debug_info.get('roi_avg_value', 0)

    ax2.plot(x_axis, accumulated_std_profile, 'purple', linewidth=2, label='Accumulated Std')

    # Mark refined ROI
    search_start, search_end = refined_roi
    ax2.axvspan(x_axis[0] + search_start, x_axis[0] + search_end,
                alpha=0.3, color='cyan', label=f'Refined ROI ({search_start}-{search_end})')

    # Mark valley and peak candidates
    valley_pos = candidate_debug_info.get('valley_pos')
    valley_value = candidate_debug_info.get('valley_value')
    peak_pos = candidate_debug_info.get('peak_pos')
    peak_value = candidate_debug_info.get('peak_value')
    selected = candidate_debug_info.get('selected_position')
    detection_type = candidate_debug_info.get('detection_type', 'unknown')

    if valley_pos is not None:
        ax2.scatter([x_axis[0] + valley_pos], [valley_value], color='blue', s=100,
                   marker='v', label=f'Valley @ {valley_pos} (val={valley_value:.1f})', zorder=5)
    if peak_pos is not None:
        ax2.scatter([x_axis[0] + peak_pos], [peak_value], color='red', s=100,
                   marker='^', label=f'Peak @ {peak_pos} (val={peak_value:.1f})', zorder=5)

    # Mark selected position with different color
    if selected is not None:
        color = 'orange' if detection_type == 'valley' else 'magenta'
        marker = 'v' if detection_type == 'valley' else '^'
        ax2.scatter([x_axis[0] + selected], [candidate_debug_info.get('chosen_value', 0)],
                   color=color, s=200, marker=marker, edgecolors='black', linewidths=2,
                   label=f'SELECTED {detection_type.upper()} @ {selected}', zorder=10)

    # Mark ROI average and significance threshold
    ax2.axhline(roi_avg_value, color='gray', linestyle=':', label=f'ROI Average: {roi_avg_value:.1f}')

    valley_threshold = candidate_debug_info.get('valley_significance_threshold', 0)
    ax2.axhline(roi_avg_value + valley_threshold, color='pink', linestyle='--', alpha=0.7,
               label=f'Valley significance: ±{valley_threshold:.1f}')
    ax2.axhline(roi_avg_value - valley_threshold, color='pink', linestyle='--', alpha=0.7)

    ax2.set_title('Refined ROI & Valley Detection')
    ax2.set_ylabel('Accumulated Std')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Panel 3: Algorithm summary
    ax3.axis('off')
    roi_length = candidate_debug_info.get('roi_length', 0)
    detection_type = candidate_debug_info.get('detection_type', 'unknown')
    selected = candidate_debug_info.get('selected_position', 0)
    valley_dev = candidate_debug_info.get('valley_deviation', 0)
    peak_dev = candidate_debug_info.get('peak_deviation', 0)
    valley_threshold = candidate_debug_info.get('valley_significance_threshold', 0)
    lateral_boundaries = candidate_debug_info.get('lateral_boundaries', (0, roi_length))
    variance_threshold = candidate_debug_info.get('variance_threshold', 0)

    left_boundary, right_boundary = lateral_boundaries
    stable_width = right_boundary - left_boundary

    stats_text = f"""
    LATERAL BOUNDARY + VALLEY/SPIKE DETECTION
    ═══════════════════════════════════════════

    Step 1: Variance Analysis
    • Smoothing window: {min(20, len(mean_profile) // 15)} pixels
    • Variance threshold: {variance_threshold:.2f} (75th percentile)
    • High variance detected at edges

    Step 2: Low-Variance Region Detection
    • Original ROI: 0-{roi_length}
    • Low-variance regions found: {len(candidate_debug_info.get('low_variance_regions', []))}
    • Selected largest region: {left_boundary}-{right_boundary} ({stable_width}px)
    • Method: Contiguous regions below threshold

    Step 3: Side-based ROI Refinement
    • Final search ROI: {search_start}-{search_end}
    • Search width: {search_end - search_start} pixels

    Step 4: Valley vs Spike Decision
    • ROI average: {roi_avg_value:.2f}
    • Valley significance: {valley_threshold:.2f} (10% of avg)
    • Valley: pos={valley_pos}, dev={valley_dev:.2f}
    • Peak: pos={peak_pos}, dev={peak_dev:.2f}

    Decision Logic (Choose Spike if):
    • Valley insignificant? {valley_dev < valley_threshold}
    • OR Spike 50% stronger? {peak_dev > valley_dev * 1.5} ({peak_dev:.2f} > {valley_dev * 1.5:.2f})
    • → Use spike: {detection_type == 'spike'}

    RESULT: {detection_type.upper()} at position {selected}
    """

    ax3.text(0.05, 0.95, stats_text, transform=ax3.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    # Panel 4: Low variance regions analysis
    low_variance_regions = candidate_debug_info.get('low_variance_regions', [])

    if low_variance_regions:
        # Bar chart of low variance region sizes
        region_sizes = [end - start for start, end in low_variance_regions]
        region_labels = [f'{start}-{end}' for start, end in low_variance_regions]

        bars = ax4.bar(range(len(low_variance_regions)), region_sizes, alpha=0.7,
                      color=['green' if (start, end) == (left_boundary, right_boundary) else 'lightgreen'
                             for start, end in low_variance_regions])

        # Highlight selected region
        for i, (start, end) in enumerate(low_variance_regions):
            if (start, end) == (left_boundary, right_boundary):
                bars[i].set_edgecolor('black')
                bars[i].set_linewidth(2)

        ax4.set_title(f'Low Variance Regions ({len(low_variance_regions)} found)')
        ax4.set_xlabel('Region Index')
        ax4.set_ylabel('Region Size (pixels)')
        ax4.set_xticks(range(len(low_variance_regions)))
        ax4.set_xticklabels(region_labels, rotation=45, fontsize=8)

        # Add size labels on bars
        for i, size in enumerate(region_sizes):
            ax4.text(i, size + max(region_sizes) * 0.02, f'{size}px', ha='center', fontsize=8)

        ax4.grid(True, alpha=0.3)
    else:
        ax4.text(0.5, 0.5, 'No low variance regions found\n(Using entire ROI)',
                ha='center', va='center', transform=ax4.transAxes, fontsize=12)
        ax4.set_title('Low Variance Regions: NONE FOUND')

    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, "candidates_debug.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)


def save_edge_detection_debug(edge_profiles, side, margin, x_fold, search_start, search_end, debug_dir, gray_img):
    """Salva visualizzazione per il rilevamento del bordo documento (lato singolo)."""
    os.makedirs(debug_dir, exist_ok=True)
    positions = [pos for pos, _ in edge_profiles]
    brightnesses = [b for _, b in edge_profiles]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    ax1.plot(positions, brightnesses, "b-", linewidth=2)
    ax1.axvline(x_fold, color="red", linestyle="--", linewidth=2, label=f"Fold @ {x_fold}")
    if margin > 0:
        edge_pos = margin if side == "left" else gray_img.shape[1] - margin
        ax1.axvline(edge_pos, color="green", linestyle="--", linewidth=2, label=f"Edge @ {edge_pos}")
    ax1.axvspan(search_start, search_end, alpha=0.2, color="yellow", label="Search area")
    ax1.legend()
    ax1.set_title(f"Edge detection - {side}")

    ax2.imshow(gray_img, cmap="gray")
    ax2.axvline(x_fold, color="red", linewidth=2)
    if margin > 0:
        ax2.axvline(edge_pos, color="green", linewidth=2)
    ax2.axvspan(search_start, search_end, alpha=0.2, color="yellow")
    ax2.set_title("Image overlay")

    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, f"edge_detection_{side}.png"), dpi=150)
    plt.close(fig)


def save_edge_detection_debug_center(left_profiles, right_profiles, left_margin, right_margin, x_fold, debug_dir, gray_img):
    """Salva visualizzazione per rilevamento bordi in caso di piega centrale."""
    os.makedirs(debug_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    if left_profiles:
        lp, lb = zip(*left_profiles)
        ax1.plot(lp, lb, "b-", label="Left profile")
    if right_profiles:
        rp, rb = zip(*right_profiles)
        ax1.plot(rp, rb, "orange", label="Right profile")

    ax1.axvline(x_fold, color="red", linestyle="--", label=f"Fold @ {x_fold}")
    ax1.legend()
    ax1.set_title(f"Center edge detection - left={left_margin}, right={right_margin}")

    ax2.imshow(gray_img, cmap="gray")
    ax2.axvline(x_fold, color="red", linewidth=2)
    if left_margin > 0:
        ax2.axvline(left_margin, color="green", linewidth=2)
    if right_margin > 0:
        ax2.axvline(gray_img.shape[1] - right_margin, color="purple", linewidth=2)
    ax2.set_title("Image overlay (center edges)")

    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, "edge_detection_center.png"), dpi=150)
    plt.close(fig)


def save_background_analysis_debug(analysis_result, debug_dir, gray_img):
    """Visualize background/page brightness analysis procedure."""
    if analysis_result is None:
        return

    os.makedirs(debug_dir, exist_ok=True)

    profile = analysis_result['profile']
    smooth_profile = analysis_result['smooth_profile']
    gradient = analysis_result['gradient']
    bg_region = analysis_result['bg_region']
    page_region = analysis_result['page_region']
    rises = analysis_result['rises']
    drops = analysis_result['drops']
    gradient_threshold = analysis_result['gradient_threshold']

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Panel 1: Original vs Smoothed profile
    x_axis = np.arange(len(profile))
    ax1.plot(x_axis, profile, 'b-', linewidth=1, alpha=0.5, label='Original Profile')
    ax1.plot(x_axis, smooth_profile, 'r-', linewidth=2, label='Smoothed Profile')
    ax1.set_xlabel('X Position (pixels)')
    ax1.set_ylabel('Mean Brightness')
    ax1.set_title('Brightness Profile with Heavy Smoothing')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Panel 2: Gradient analysis with transitions
    ax2.plot(x_axis, gradient, 'purple', linewidth=1, label='Gradient')
    ax2.axhline(gradient_threshold, color='orange', linestyle='--', label=f'Rise Threshold: {gradient_threshold:.3f}')
    ax2.axhline(-gradient_threshold, color='red', linestyle='--', label=f'Drop Threshold: {-gradient_threshold:.3f}')

    # Mark rises and drops
    if len(rises) > 0:
        ax2.scatter(rises, gradient[rises], color='green', s=50, label='Rises (BG→Page)', zorder=5)
    if len(drops) > 0:
        ax2.scatter(drops, gradient[drops], color='red', s=50, label='Drops (Page→BG)', zorder=5)

    ax2.set_xlabel('X Position (pixels)')
    ax2.set_ylabel('Gradient')
    ax2.set_title('Gradient Analysis & Transition Detection')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Panel 3: Detected regions
    ax3.plot(x_axis, smooth_profile, 'b-', linewidth=1, alpha=0.7, label='Smoothed Profile')

    # Mark background and page regions
    ax3.axvspan(bg_region[0], bg_region[1], alpha=0.5, color='red', label=f'Background ({analysis_result["background_side"]})')
    ax3.axvspan(page_region[0], page_region[1], alpha=0.3, color='green', label='Page Plateau')

    # Mark transitions
    if len(rises) > 0:
        for rise in rises:
            ax3.axvline(rise, color='green', linestyle=':', alpha=0.7)
    if len(drops) > 0:
        for drop in drops:
            ax3.axvline(drop, color='red', linestyle=':', alpha=0.7)

    ax3.set_xlabel('X Position (pixels)')
    ax3.set_ylabel('Mean Brightness')
    ax3.set_title('Detected Page Plateau & Background Regions')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Panel 4: Statistics summary
    ax4.axis('off')
    stats_text = f"""
    BACKGROUND/PAGE ANALYSIS (Gradient-Based)
    ═══════════════════════════════════════════

    Algorithm Parameters:
    • Smoothing Kernel: {max(51, len(profile) // 50)} px
    • Gradient Threshold: ±{gradient_threshold:.3f}

    Detected Transitions:
    • Rises (BG→Page): {len(rises)} at positions {list(rises[:3])}{'...' if len(rises) > 3 else ''}
    • Drops (Page→BG): {len(drops)} at positions {list(drops[:3])}{'...' if len(drops) > 3 else ''}

    Background Region ({analysis_result['background_side']} side):
    • Position: {bg_region[0]}-{bg_region[1]} px
    • Mean: {analysis_result['background_mean']:.1f} ± {analysis_result['background_std']:.1f}
    • Width: {bg_region[1] - bg_region[0]} px

    Page Plateau:
    • Position: {page_region[0]}-{page_region[1]} px
    • Mean: {analysis_result['page_mean']:.1f} ± {analysis_result['page_std']:.1f}
    • Width: {page_region[1] - page_region[0]} px

    Quality Assessment:
    • Contrast: {'EXCELLENT' if analysis_result['page_mean'] - analysis_result['background_mean'] > 50 else 'GOOD' if analysis_result['page_mean'] - analysis_result['background_mean'] > 30 else 'POOR'}
    • Background Uniformity: {'GOOD' if analysis_result['background_std'] < 15 else 'POOR'}
    • Page Uniformity: {'GOOD' if analysis_result['page_std'] < 20 else 'POOR'}
    """

    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=9,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, "background_analysis_debug.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # Create additional image overlay visualization
    fig2, ax = plt.subplots(figsize=(16, 10))

    # Show the original image
    ax.imshow(gray_img, cmap='gray', aspect='auto')

    # Overlay detected boundaries with thick colored lines
    bg_start, bg_end = bg_region
    page_start, page_end = page_region

    # Background region - RED with transparency
    ax.axvline(bg_start, color='red', linewidth=4, alpha=0.7, label=f'BG Start: {bg_start}px')
    ax.axvline(bg_end, color='red', linewidth=4, linestyle='--', alpha=0.7, label=f'BG End: {bg_end}px')

    # Page plateau region - GREEN with transparency
    ax.axvline(page_start, color='lime', linewidth=4, alpha=0.7, label=f'Page Start: {page_start}px')
    ax.axvline(page_end, color='lime', linewidth=4, linestyle='--', alpha=0.7, label=f'Page End: {page_end}px')

    # Mark transitions with different colors and transparency
    if len(rises) > 0:
        for i, rise in enumerate(rises):
            ax.axvline(rise, color='yellow', linewidth=3, alpha=0.6,
                      label='Rise (BG→Page)' if i == 0 else '')
    if len(drops) > 0:
        for i, drop in enumerate(drops):
            ax.axvline(drop, color='orange', linewidth=3, alpha=0.6,
                      label='Drop (Page→BG)' if i == 0 else '')

    ax.set_title(f'Detected Boundaries Overlay\nPage: {page_start}-{page_end}px | Background ({analysis_result["background_side"]}): {bg_start}-{bg_end}px',
                fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.set_xlabel('X Position (pixels)')
    ax.set_ylabel('Y Position (pixels)')

    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, "boundaries_overlay.png"), dpi=150, bbox_inches='tight')
    plt.close(fig2)
