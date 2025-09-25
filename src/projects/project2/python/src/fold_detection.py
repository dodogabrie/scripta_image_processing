"""
fold_detection.py

Simplified Book Fold Detection System
====================================

This module implements a simplified fold detection algorithm using brightness profile
analysis and parabolic curve fitting. The fold is always assumed to be in the center.

Key Functions:
- find_fold_center: Main function for detecting fold position in center ROI
- extract_simple_brightness_profiles: Extract brightness profiles with basic statistics

Author: [Generated Documentation]
Version: 3.0 (Simplified)
"""

import cv2
import numpy as np
from scipy.optimize import curve_fit

from .utils import parabola


def extract_simple_brightness_profiles(roi, num_samples=60):
    """
    Simple Brightness Profile Extraction
    ===================================

    Extracts horizontal brightness profiles from random row positions
    and applies basic statistical filtering.

    Args:
        roi (np.ndarray): Region of Interest grayscale image
        num_samples (int): Number of horizontal profiles to extract

    Returns:
        tuple: (mean_profile, std_profile)
               - mean_profile (np.ndarray): Mean brightness profile
               - std_profile (np.ndarray): Standard deviation profile
    """
    h = roi.shape[0]

    # Generate random row indices
    if h <= num_samples:
        rows = np.arange(h)
    else:
        rows = np.random.choice(h, size=num_samples, replace=False)

    # Extract brightness profiles
    profiles = [roi[r, :] for r in rows]
    avg_ints = [prof.mean() for prof in profiles]

    # Simple outlier filtering using 1.5 sigma rule
    mean_int = np.mean(avg_ints)
    std_int = np.std(avg_ints)

    filtered_profiles = [
        prof
        for prof, avg in zip(profiles, avg_ints)
        if abs(avg - mean_int) <= 1.5 * std_int
    ]

    # Fallback if all profiles filtered out
    if not filtered_profiles:
        filtered_profiles = profiles

    # Calculate ensemble statistics
    arr = np.array(filtered_profiles)
    mean_profile = arr.mean(axis=0)
    std_profile = arr.std(axis=0)

    return mean_profile, std_profile


def find_fold_center(img=None, roi=None):
    """
    Find Fold Center Position
    ========================

    Main function to detect fold position using parabolic curve fitting.
    Can work with either full image (uses center ROI) or custom ROI.

    Args:
        img (np.ndarray): Full BGR image (will extract center ROI)
        roi (np.ndarray): Custom ROI grayscale image (optional)

    Returns:
        int: Fold x-position in global image coordinates
    """
    if roi is not None:
        # Use provided ROI
        gray_roi = roi if len(roi.shape) == 2 else cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        x_offset = 0  # No offset needed for custom ROI
    elif img is not None:
        # Extract center ROI from full image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        # Use center 40% of image
        x_start = int(0.3 * w)
        x_end = int(0.7 * w)
        gray_roi = gray[:, x_start:x_end]
        x_offset = x_start
    else:
        raise ValueError("Either img or roi must be provided")

    # Apply noise reduction
    blur_roi = cv2.GaussianBlur(gray_roi, (5, 5), 0)

    # Extract brightness profiles
    mean_profile, std_profile = extract_simple_brightness_profiles(blur_roi)

    # Enhance fold contrast by combining mean brightness with uncertainty
    enhanced_profile = mean_profile + std_profile

    # Apply smoothing
    smooth = cv2.GaussianBlur(enhanced_profile, (11, 1), 0).flatten()

    # Find approximate minimum position
    x_min = np.argmin(smooth)

    # Define fitting window around minimum
    x_fit = np.arange(max(0, x_min - 15), min(len(smooth), x_min + 16))
    y_fit = smooth[x_fit]

    # Fit parabolic curve
    try:
        popt, _ = curve_fit(parabola, x_fit, y_fit)
        # Calculate exact parabola vertex (minimum) position
        x_refined = -popt[1] / (2 * popt[0])
        x_final = int(round(x_offset + x_refined))
    except:
        # Fallback to simple minimum if curve fitting fails
        x_final = x_offset + x_min

    return x_final


def detect_fold_brightness_profile(img, side, debug=False, debug_dir=None):
    """
    Main Fold Detection Function (Legacy Interface)
    ==============================================

    Maintains compatibility with existing code while using simplified algorithm.
    Always assumes center fold regardless of side parameter.

    Args:
        img (np.ndarray): Input BGR image
        side (str): Fold side (ignored - always uses center)
        debug (bool): Debug flag (ignored in simplified version)
        debug_dir (str): Debug directory (ignored in simplified version)

    Returns:
        tuple: (x_final, angle, slope, intercept, confidence)
               - x_final (int): Fold position
               - angle (float): Always 0.0 (angle estimation removed)
               - slope (float): Always 0.0 (slope estimation removed)
               - intercept (float): Always 0.0 (intercept estimation removed)
               - confidence (float): Always 1.0 (confidence calculation removed)
    """
    # Use simplified fold detection (ignores side parameter)
    x_final = find_fold_center(img=img)

    # Return dummy values for compatibility
    return x_final, 0.0, 0.0, 0.0, 1.0
