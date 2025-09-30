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


def extract_simple_brightness_profiles(roi, rows=None, num_samples=60):
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

    # Use provided rows or generate random row indices
    if rows is None:
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
    Find Fold Center Position with Quality Assessment
    ================================================

    Main function to detect fold position using parabolic curve fitting.
    Can work with either full image (uses center ROI) or custom ROI.
    Now includes position consistency analysis across iterations.

    Args:
        img (np.ndarray): Full BGR image (will extract center ROI)
        roi (np.ndarray): Custom ROI grayscale image (optional)

    Returns:
        tuple: (x_position, quality_score)
               - x_position (int): Fold x-position in global image coordinates
               - quality_score (float): Quality score based on position consistency (0.0-1.0)
    """
    if roi is not None:
        # Use provided ROI
        gray_roi = roi if len(roi.shape) == 2 else cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        x_offset = 0  # No offset needed for custom ROI
    elif img is not None:
        # Extract center ROI from full image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        # Use center 20% of image
        x_start = int(0.4 * w)
        x_end = int(0.6 * w)
        gray_roi = gray[:, x_start:x_end]
        x_offset = x_start
    else:
        raise ValueError("Either img or roi must be provided")

    # Apply noise reduction with adaptive kernel size
    roi_height, roi_width = gray_roi.shape

    # Calculate kernel size as percentage of ROI dimensions (must be odd)
    # Use smaller dimension to ensure kernel fits properly
    min_roi_size = min(roi_height, roi_width)
    kernel_size = max(3, int(min_roi_size * 0.02))  # 2% of smaller dimension, minimum 3
    if kernel_size % 2 == 0:  # Ensure odd number
        kernel_size += 1

    blur_roi = cv2.GaussianBlur(gray_roi, (kernel_size, kernel_size), 0)

    iterations = 20
    detected_positions = []
    profiles_sum = None

    # Pre-shuffle all rows to ensure different samples across iterations
    h = blur_roi.shape[0]
    all_rows = np.arange(h)
    np.random.shuffle(all_rows)

    profile_sum = None

    # Track position across all iterations
    for i in range(iterations):
        # Extract brightness profiles for this iteration using different row partitions
        rows_per_iteration = min(60, h // iterations)
        start_idx = (i * rows_per_iteration) % h
        end_idx = min(start_idx + rows_per_iteration, h)

        # Use different rows for each iteration
        iteration_rows = all_rows[start_idx:end_idx]
        if len(iteration_rows) < 10:  # Fallback if partition too small
            iteration_rows = all_rows[
                np.random.choice(h, size=min(10, h), replace=False)
            ]

        mean_profile, std_profile = extract_simple_brightness_profiles(
            blur_roi, iteration_rows
        )

        # Enhance fold contrast by combining mean brightness with uncertainty
        enhanced_profile = mean_profile + std_profile

        # Remove linear trend to focus on fold signal
        x_coords = np.arange(len(enhanced_profile))
        # Fast linear detrend: subtract linear fit
        linear_fit = np.polyfit(x_coords, enhanced_profile, 1)
        linear_trend = np.polyval(linear_fit, x_coords)
        enhanced_profile = enhanced_profile - linear_trend

        # Accumulate profiles for final average
        if profiles_sum is None:
            profiles_sum = enhanced_profile.copy()
        else:
            profiles_sum += enhanced_profile

        # Apply smoothing for this iteration with adaptive kernel size
        # For 1D smoothing, use smaller kernel (1% of profile width)
        profile_length = len(enhanced_profile)
        smooth_kernel_size = max(
            3, int(profile_length * 0.01)
        )  # 1% of profile width, minimum 3
        if smooth_kernel_size % 2 == 0:  # Ensure odd number
            smooth_kernel_size += 1

        smooth = cv2.GaussianBlur(
            enhanced_profile, (smooth_kernel_size, 1), 0
        ).flatten()

        # Find approximate minimum position for this iteration
        x_min = np.argmin(smooth)

        # Define fitting window around minimum
        x_fit = np.arange(max(0, x_min - 15), min(len(smooth), x_min + 16))
        y_fit = smooth[x_fit]

        # Fit parabolic curve for this iteration
        try:
            popt, _ = curve_fit(parabola, x_fit, y_fit)
            # Calculate exact parabola vertex (minimum) position
            x_refined = -popt[1] / (2 * popt[0])
            x_iteration = x_offset + x_refined
        except Exception as e:
            # Fallback to simple minimum if curve fitting fails
            print("Error in curve fitting:", e)
            x_iteration = x_offset + x_min

        detected_positions.append(x_iteration)

    # Calculate average and final result
    profiles_sum /= iterations

    # Detect multiple minima in the final averaged profile
    from scipy.signal import find_peaks

    # Find peaks in inverted profile (minima become peaks)
    inverted_profile = -profiles_sum
    peaks, properties = find_peaks(
        inverted_profile,
        height=np.std(inverted_profile) * 3,  # Minimum prominence
        distance=roi_width * 0.1,  # Minimum distance between peaks (10% of ROI width)
    )

    num_minima = len(peaks)
    print(
        f"Detected {num_minima} potential fold minima at positions: {peaks + x_offset}"
    )
    quality_score = 0
    if num_minima == 1:
        x_final = int(peaks[0] + x_offset)
        quality_score = 1
        print(f"Single minimum detected at x={x_final}")
    elif num_minima > 1 and num_minima <= 3:
        # Multiple minima detected - choose the most central one or most prominent
        center_roi = roi_width // 2
        distances_from_center = np.abs(peaks - center_roi)
        best_peak_idx = np.argmin(distances_from_center)
        x_final = int(peaks[best_peak_idx] + x_offset)
        print(f"Multiple minima detected! Using most central at x={x_final}")

        # Adjust quality score for multiple minima (indicates uncertainty)
        quality_score = 0.7
    else:
        # Use the mean position as final result (original behavior)
        x_final = int(round(np.mean(detected_positions)))
        quality_score = 0.5

    # Calculate position consistency quality score
    position_std = np.std(detected_positions)

    # Calculate ROI width to make thresholds relative to image size
    roi_width = gray_roi.shape[1]

    # Quality thresholds as percentage of ROI width
    # These percentages are based on typical fold detection accuracy expectations
    excellent_threshold = roi_width * 0.01  # 1% of ROI width (very tight)
    good_threshold = roi_width * 0.02  # 2% of ROI width (tight)
    acceptable_threshold = roi_width * 0.05  # 5% of ROI width (moderate)
    poor_threshold = roi_width * 0.1  # 10% of ROI width (loose)

    print(excellent_threshold, poor_threshold)
    print(position_std)

    # Quality score based on position stability relative to ROI size
    if position_std <= excellent_threshold:
        quality_score += 1.0  # Excellent consistency
    elif position_std <= good_threshold:
        quality_score += 0.8  # Good consistency
    elif position_std <= acceptable_threshold:
        quality_score += 0.6  # Acceptable consistency
    elif position_std <= poor_threshold:
        quality_score += 0.4  # Poor consistency
    else:
        quality_score += 0.2  # Very poor consistency

    quality_score /= 2.0  # Normalize quality score to [0, 1]
    # Quality score based on position stability relative to ROI size (assumption: pages are mainly stable)
    if quality_score >= 0.6:
        exclude_pixels = int(position_std * 2)

        # Create profile excluding pixels around fold position for cleaner variation measurement
        fold_center_roi = x_final - x_offset  # Convert to ROI coordinates
        profile_length = len(profiles_sum)

        # Exclude region around fold center
        exclude_start = max(0, fold_center_roi - exclude_pixels)
        exclude_end = min(profile_length, fold_center_roi + exclude_pixels)

        # Create mask excluding the fold region
        profile_excluded_pixels = (
            np.concatenate([profiles_sum[:exclude_start], profiles_sum[exclude_end:]])
            if exclude_start < exclude_end
            and exclude_start > 0
            and exclude_end < profile_length
            else profiles_sum
        )

        vertical_variations = np.std(profile_excluded_pixels)
        print("Excluding pixels of fit: ", vertical_variations)
        print(vertical_variations)
        if vertical_variations > 10:
            quality_score = quality_score - vertical_variations / 30
        if quality_score < 0:
            quality_score = 0

    import matplotlib.pyplot as plt

    plt.plot(profiles_sum)
    plt.title(
        f"Fold Detection - Quality: {quality_score:.2f} (std: {position_std:.1f}px)"
        + "\n"
        + f"Vertical variations: {np.std(profiles_sum):.3f}px"
    )
    plt.show()

    return x_final, quality_score


def detect_fold_brightness_profile(img, side, debug=False, debug_dir=None):
    """
    Main Fold Detection Function with Quality Assessment
    ===================================================

    Maintains compatibility with existing code while using simplified algorithm.
    Always assumes center fold regardless of side parameter.
    Now includes position consistency-based quality assessment.

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
               - confidence (float): Quality score based on position consistency (0.0-1.0)
    """
    # Use fold detection with quality assessment
    x_final, quality_score = find_fold_center(img=img)

    # Return quality score as confidence for compatibility
    return x_final, 0.0, 0.0, 0.0, quality_score
