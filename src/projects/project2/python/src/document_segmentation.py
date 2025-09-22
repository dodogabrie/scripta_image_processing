"""
document_segmentation.py

Document Page Segmentation and Border Detection
==============================================

This module provides functionality for detecting document boundaries, analyzing page
structure, and segmenting different regions within scanned documents. It serves as
a foundation for both fold detection and metadata analysis.

Key Features:
- Document boundary detection via brightness gradient analysis
- Page plateau identification using brightness profiles
- Background region classification
- Multi-format document support (A4, Letter, etc.)
- Edge margin calculation for cropping

Author: [Generated Documentation]
Version: 1.0
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional, List


def analyze_background_page_brightness(img: np.ndarray) -> Optional[Dict]:
    """
    Detect background/page regions by analyzing plateau borders via gradient analysis.

    This function analyzes horizontal brightness profiles to identify major transitions
    between background and document page regions using gradient-based detection.

    Args:
        img (np.ndarray): Input BGR image (H, W, 3)

    Returns:
        Dict or None: Background and page brightness statistics with region boundaries.
                     Returns None if no clear regions can be detected.

    Dict Contents:
        - background_mean (float): Mean brightness of background region
        - background_std (float): Standard deviation of background
        - page_mean (float): Mean brightness of page region
        - page_std (float): Standard deviation of page
        - background_side (str): Which side background is on ('left' or 'right')
        - bg_region (tuple): Background region boundaries (start, end)
        - page_region (tuple): Page plateau boundaries (start, end)
        - profile (np.ndarray): Original brightness profile
        - smooth_profile (np.ndarray): Smoothed brightness profile
        - gradient (np.ndarray): Gradient array for transition detection
        - rises (np.ndarray): Positions of background→page transitions
        - drops (np.ndarray): Positions of page→background transitions
        - gradient_threshold (float): Threshold used for transition detection
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Get horizontal brightness profile (mean across height)
    profile = np.mean(gray, axis=0)

    # Heavy smoothing to eliminate local variations and focus on major transitions
    kernel_size = max(200, len(profile) // 200)  # Adaptive kernel size
    if kernel_size % 2 == 0:
        kernel_size += 1
    smooth_profile = cv2.GaussianBlur(
        profile.reshape(1, -1), (kernel_size, 1), 0
    ).flatten()

    # Calculate gradient to find transitions (rises/drops)
    gradient = np.gradient(smooth_profile)

    # Find significant transitions
    gradient_threshold = (
        np.std(gradient) * 2.0
    )  # Strong threshold for major transitions

    # Find positive transitions (background -> page)
    rises = np.where(gradient > gradient_threshold)[0]
    # Find negative transitions (page -> background)
    drops = np.where(gradient < -gradient_threshold)[0]

    # Determine plateau boundaries
    plateau_start = 0
    plateau_end = len(smooth_profile) - 1

    # Find first significant rise (left boundary)
    if len(rises) > 0:
        plateau_start = rises[0]

    # Find last significant drop (right boundary)
    if len(drops) > 0:
        plateau_end = drops[-1]

    # Ensure plateau_start < plateau_end
    if plateau_start >= plateau_end:
        # Fallback: use middle 60% as plateau
        plateau_start = int(0.2 * len(smooth_profile))
        plateau_end = int(0.8 * len(smooth_profile))

    # Define background regions
    left_bg_end = max(20, plateau_start - 10)  # Small margin before plateau
    right_bg_start = min(
        len(smooth_profile) - 20, plateau_end + 10
    )  # Small margin after plateau

    # Extract regions from image
    left_bg_region = gray[:, :left_bg_end] if left_bg_end > 20 else None
    right_bg_region = (
        gray[:, right_bg_start:] if right_bg_start < len(smooth_profile) - 20 else None
    )
    page_region = gray[:, plateau_start:plateau_end]

    # Choose primary background (darkest)
    left_brightness = (
        np.mean(left_bg_region) if left_bg_region is not None else float("inf")
    )
    right_brightness = (
        np.mean(right_bg_region) if right_bg_region is not None else float("inf")
    )

    if left_brightness < right_brightness and left_bg_region is not None:
        bg_region = left_bg_region
        bg_bounds = (0, left_bg_end)
        bg_side = "left"
    elif right_bg_region is not None:
        bg_region = right_bg_region
        bg_bounds = (right_bg_start, len(smooth_profile))
        bg_side = "right"
    else:
        return None  # No background detected

    return {
        "background_mean": float(np.mean(bg_region)),
        "background_std": float(np.std(bg_region)),
        "page_mean": float(np.mean(page_region)),
        "page_std": float(np.std(page_region)),
        "background_side": bg_side,
        "bg_region": bg_bounds,
        "page_region": (plateau_start, plateau_end),
        "profile": profile,
        "smooth_profile": smooth_profile,
        "gradient": gradient,
        "rises": rises,
        "drops": drops,
        "gradient_threshold": gradient_threshold,
    }


def find_brightness_drop(profiles: List[Tuple[int, float]], side: str, image_width: int) -> int:
    """
    Document Edge Detection via Brightness Gradient Analysis.

    Detects document boundaries by analyzing brightness gradients to find
    significant luminosity drops that indicate transitions from document
    to background.

    Args:
        profiles (List[Tuple[int, float]]): List of (position, brightness) tuples
        side (str): Fold side for margin calculation ('left', 'right')
        image_width (int): Total image width for position conversion

    Returns:
        int: Detected margin distance in pixels (0 if no significant drop found)
    """
    # Input validation: ensure sufficient data for reliable analysis
    if not profiles or len(profiles) < 5:
        return 0  # Cannot detect edges with insufficient samples

    # Separate brightness values and spatial positions
    brightnesses = [b for _, b in profiles]  # Brightness measurements
    positions = [pos for pos, _ in profiles]  # Corresponding pixel positions

    # Adaptive smoothing window calculation
    window_size = min(8, len(brightnesses) // 3)  # Max 8, or 1/3 of data length
    if window_size < 3:
        window_size = min(3, len(brightnesses))

    # Apply windowed smoothing to reduce measurement noise
    smoothed = []
    for i in range(len(brightnesses)):
        start = max(0, i - window_size // 2)
        end = min(len(brightnesses), i + window_size // 2 + 1)
        avg = sum(brightnesses[start:end]) / (end - start)
        smoothed.append(avg)

    # Optional secondary Gaussian smoothing for profiles with sufficient points
    if len(smoothed) >= 5:
        kernel_size = min(5, len(smoothed) // 2)
        if kernel_size % 2 == 0:
            kernel_size += 1

        smoothed = (
            cv2.GaussianBlur(np.array(smoothed).reshape(1, -1), (kernel_size, 1), 1.0)
            .flatten()
            .tolist()
        )

    # Brightness threshold: 75% of maximum brightness
    threshold = max(smoothed) * 0.75

    # Initialize edge detection variables
    max_drop, best_position = 0, 0

    # Derivative calculation window
    derivative_window = min(3, len(smoothed) // 4)

    # Scan through smoothed profile to find maximum brightness drop
    for i in range(derivative_window, len(smoothed) - derivative_window):
        left_avg = sum(smoothed[i - derivative_window : i]) / derivative_window
        right_avg = sum(smoothed[i + 1 : i + derivative_window + 1]) / derivative_window

        current_drop = left_avg - right_avg

        if current_drop > max_drop and smoothed[i] < threshold:
            max_drop = current_drop
            best_position = positions[i]

    # Apply significance threshold and convert position to margin distance
    if max_drop > 3:  # Minimum drop threshold
        if side == "left":
            return max(0, best_position)
        elif side == "right":
            return max(0, image_width - best_position)

    return 0


def detect_document_edge(img: np.ndarray, side: str, x_fold: int,
                        debug: bool = False, debug_dir: Optional[str] = None) -> int:
    """
    Intelligent Document Margin Detection for Smart Cropping.

    Detects document boundaries by analyzing brightness profiles in search
    regions adjacent to the detected fold.

    Args:
        img (np.ndarray): Input BGR image
        side (str): Fold side ('left', 'right', 'center')
        x_fold (int): Detected fold position
        debug (bool): Whether to generate debug visualizations
        debug_dir (str): Directory for debug output files

    Returns:
        int or tuple: Detected margin distance(s)
                     - Single int for 'left'/'right' sides
                     - Tuple (left_margin, right_margin) for 'center'
    """
    # Convert to grayscale and apply noise reduction
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1.0)
    h, w = blur.shape

    if side == "left":
        # Left fold: search rightward from fold to find right document edge
        search_start, search_end = min(w - 10, x_fold + 50), w - 5
        edge_profiles = [
            (x, np.mean(blur[:, x])) for x in range(search_start, search_end)
        ]
        margin = find_brightness_drop(edge_profiles, "right", w)

    elif side == "right":
        # Right fold: search leftward from fold to find left document edge
        search_start, search_end = max(5, x_fold - 50), 5
        edge_profiles = [
            (x, np.mean(blur[:, x])) for x in range(search_start, search_end, -1)
        ]
        margin = find_brightness_drop(edge_profiles, "left", w)

    elif side == "center":
        # Center fold: search both directions for document edges
        left_profiles = [
            (x, np.mean(blur[:, x])) for x in range(max(5, x_fold - 50), 5, -1)
        ]
        right_profiles = [
            (x, np.mean(blur[:, x])) for x in range(min(w - 10, x_fold + 50), w - 5)
        ]
        left_margin = find_brightness_drop(left_profiles, "left", w)
        right_margin = find_brightness_drop(right_profiles, "right", w)
        margin = (left_margin, right_margin)
    else:
        raise ValueError(f"Unsupported fold side: {side}")

    # Generate debug visualizations if requested
    if debug and debug_dir:
        from . import fold_debug

        if side == "center":
            fold_debug.save_edge_detection_debug_center(
                left_profiles,
                right_profiles,
                margin[0],
                margin[1],
                x_fold,
                debug_dir,
                gray,
            )
        else:
            fold_debug.save_edge_detection_debug(
                edge_profiles,
                side,
                margin,
                x_fold,
                search_start,
                search_end,
                debug_dir,
                gray,
            )

    return margin


def get_document_boundaries(img: np.ndarray) -> Dict:
    """
    Comprehensive document boundary analysis.

    Combines brightness analysis and edge detection to provide complete
    document boundary information.

    Args:
        img (np.ndarray): Input BGR image

    Returns:
        Dict: Complete boundary analysis results including:
              - background analysis results
              - page dimensions
              - content boundaries
              - quality metrics
    """
    # Get background/page analysis
    bg_analysis = analyze_background_page_brightness(img)

    if bg_analysis is None:
        # Fallback: return basic image dimensions
        h, w = img.shape[:2]
        return {
            "success": False,
            "page_boundaries": (0, w),
            "background_boundaries": None,
            "page_width": w,
            "page_height": h,
            "background_side": None,
            "quality": "POOR"
        }

    # Extract key information
    page_region = bg_analysis["page_region"]
    bg_region = bg_analysis["bg_region"]
    page_width = page_region[1] - page_region[0]

    # Calculate quality metrics
    contrast = bg_analysis["page_mean"] - bg_analysis["background_mean"]
    if contrast > 50:
        quality = "EXCELLENT"
    elif contrast > 30:
        quality = "GOOD"
    else:
        quality = "POOR"

    return {
        "success": True,
        "page_boundaries": page_region,
        "background_boundaries": bg_region,
        "page_width": page_width,
        "page_height": img.shape[0],
        "background_side": bg_analysis["background_side"],
        "contrast": contrast,
        "quality": quality,
        "full_analysis": bg_analysis
    }