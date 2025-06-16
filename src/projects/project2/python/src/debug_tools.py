"""
debug_tools.py

Modulo per funzioni di debug e visualizzazione.
"""

import cv2
import os
import numpy as np
from scipy.optimize import curve_fit
from .utils import parabola


def save_debug_visualization(filtered_profiles, mean_profile, std_profile, x_axis, x0, x_min, x_final, roi, debug_dir):
    """
    Salva le immagini di debug per l'analisi visiva.
    """
    import matplotlib.pyplot as plt
    os.makedirs(debug_dir, exist_ok=True)

    # Plot profili di luminosità e fit parabolico
    fig, (ax1, ax2) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [2, 1]}, figsize=(8, 6))
    for prof in filtered_profiles:
        ax1.plot(x_axis, prof, color='gray', linewidth=0.5, alpha=0.3)
    ax1.errorbar(x_axis, mean_profile, yerr=std_profile, color='red', ecolor='salmon',
                 linewidth=2, elinewidth=1, capsize=2, label='mean ± std')
    ax1.set_title('Brightness profiles (filtered)')
    ax1.set_ylabel('Gray value')
    ax1.grid(True)
    ax1.legend(fontsize='xx-small', loc='upper right', framealpha=0.6)
    ax2.imshow(roi, cmap='gray', aspect='auto')
    ax2.set_title('ROI preview')
    ax2.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, 'step_profiles.png'))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x_axis, mean_profile, label='Mean profile', alpha=0.5)
    smooth = cv2.GaussianBlur(mean_profile + std_profile, (11, 1), 0).flatten()
    ax.plot(x_axis, smooth, label='Smoothed', color='orange')
    ax.axvline(x0 + x_min, color='gray', linestyle='--', label='Min raw')
    ax.axvline(x_final, color='red', linestyle='--', label='Min refined')
    x_fit = np.arange(max(0, x_min-15), min(len(smooth), x_min+16))
    popt, _ = curve_fit(parabola, x_fit, smooth[x_fit])
    ax.plot(x0 + x_fit, parabola(x_fit, *popt), 'r:', label='Parabolic fit')
    ax.set_title('Profile + Fit')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, 'step_min_fit.png'))
    plt.close(fig)


def save_debug_line_visualization(img, x_fold, angle, a, b, output_path):
    """
    Salva un'immagine con la linea della piega visualizzata per debug.
    """
    h = img.shape[0]
    vis = img.copy()
    x0_line = int(a * 0 + b)
    x1_line = int(a * h + b)
    cv2.line(vis, (x0_line, 0), (x1_line, h), (0, 0, 255), 2)
    cv2.imwrite(output_path, vis)
