"""
fold_detection.py

Advanced Book Fold Detection System
===================================

This module implements sophisticated computer vision algorithms for automatic detection
and analysis of book spine folds in scanned double-page documents. The system uses
multiple complementary approaches including brightness profile analysis, statistical
outlier filtering, parabolic curve fitting, and document edge detection.

Key Algorithms:
- Automatic fold side detection via brightness analysis
- Multi-scale brightness profile extraction with outlier filtering
- Parabolic curve fitting for precise fold localization
- Linear regression for fold angle estimation
- Document boundary detection via brightness gradient analysis

Design Principles:
- Pure numerical processing (no UI dependencies)
- Statistical robustness through outlier filtering
- Multi-modal detection supporting left/right/center folds
- Mathematically sound curve fitting and optimization
- Extensible architecture for different document types

Author: [Generated Documentation]
Version: 2.0
"""

import cv2
import numpy as np
from scipy.optimize import curve_fit

from .utils import parabola
from .document_segmentation import detect_document_edge, analyze_background_page_brightness


def auto_detect_side(img):
    """
    Automatic Fold Side Detection via Brightness Analysis
    ====================================================

    Determines the fold location (left, right, or center) by analyzing brightness
    patterns in vertical strips at strategic image positions. Uses comparative
    brightness analysis and statistical thresholds to classify fold type.

    Algorithm:
    1. Extract vertical strips from left edge, right edge, and center
    2. Calculate mean brightness for each strip
    3. Apply decision rules based on brightness comparisons:
       - Center fold: center significantly darker OR left/right brightness similar
       - Side fold: determined by brightness asymmetry

    Args:
        img (np.ndarray): Input BGR image (H, W, 3)

    Returns:
        str: Detected fold side ('left', 'right', 'center')

    Mathematical Foundation:
        - Uses 10px margins and 20px strip widths for robust sampling
        - Center detection threshold: 10 brightness units below minimum side
        - Symmetry threshold: 5 brightness units for left/right similarity
    """
    # Convert to grayscale for brightness analysis
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Define sampling parameters - optimized for typical book scans
    margin = 10  # Avoid edge artifacts and binding shadows
    strip_width = 20  # Wide enough for stable statistics, narrow enough for precision

    # Extract vertical brightness strips at strategic positions
    # Left strip: avoid binding edge but capture document area
    left_strip = gray[:, margin : margin + strip_width]
    # Right strip: symmetric positioning to left strip
    right_strip = gray[:, w - margin - strip_width : w - margin]
    # Center strip: positioned at image center for fold detection
    center_strip = gray[:, w // 2 - strip_width // 2 : w // 2 + strip_width // 2 + 1]

    # Calculate mean brightness for each strip (higher values = brighter regions)
    left_brightness = np.mean(left_strip)
    right_brightness = np.mean(right_strip)
    center_brightness = np.mean(center_strip)

    # Decision logic for fold side classification

    # Primary center fold detection: center significantly darker than both sides
    # Threshold of 10 units accounts for typical fold shadow depth
    if center_brightness < min(left_brightness, right_brightness) - 10:
        return "center"

    # Secondary center fold detection: left/right brightness symmetry
    # Threshold of 5 units handles minor lighting variations
    if np.abs(left_brightness - right_brightness) < 5:
        return "center"

    # Asymmetric brightness indicates side fold
    # Darker side typically contains the fold due to shadow/binding effects
    return "right" if left_brightness < right_brightness else "left"


def estimate_fold_angle_from_profile(gray, x_center, step=3):
    """
    Fold Angle Estimation via Parabolic Analysis and Linear Regression
    =================================================================

    Estimates fold angle by analyzing brightness minima along the fold line.
    Uses a two-stage approach: parabolic fitting to estimate fold width,
    then linear regression on sampled fold points to calculate angle.

    Algorithm:
    1. Extract vertical brightness profile at fold center
    2. Apply parabolic fitting to estimate fold characteristics
    3. Calculate optimal ROI width based on fold depth analysis
    4. Sample brightness minima at regular vertical intervals
    5. Apply linear regression to sampled points for angle calculation

    Args:
        gray (np.ndarray): Grayscale image (H, W)
        x_center (int): Horizontal fold center position
        step (int): Vertical sampling step size (default: 3)

    Returns:
        tuple: (angle_degrees, slope, intercept, estimated_width)
               - angle_degrees (float): Fold angle in degrees
               - slope (float): Linear regression slope coefficient
               - intercept (float): Linear regression intercept
               - estimated_width (int): Estimated fold width in pixels

    Mathematical Foundation:
        - Parabolic fitting: f(x) = ax² + bx + c
        - Width estimation: w = 2√(depth/|a|) where depth is brightness range
        - Angle calculation: θ = arctan(slope) converted to degrees
    """
    h = gray.shape[0]

    # Extract narrow vertical strip centered on fold for profile analysis
    # 5-pixel width balances noise reduction with spatial precision
    col_strip = gray[:, max(0, x_center - 2) : min(gray.shape[1], x_center + 3)]

    # Calculate mean brightness profile along fold line
    mean_profile = col_strip.mean(axis=1)

    # Apply Gaussian smoothing to reduce noise while preserving fold shape
    # Kernel (1,11): no horizontal smoothing, moderate vertical smoothing
    smoothed = cv2.GaussianBlur(mean_profile, (1, 11), 0)

    # Create coordinate array for curve fitting
    y = np.arange(len(smoothed))

    # Parabolic curve fitting for fold width estimation
    try:
        # Fit 2nd degree polynomial: f(y) = ay² + by + c
        popt = np.polyfit(y, smoothed, 2)
        a, b, c = popt

        # Calculate fold depth as half the brightness range
        # This represents the "darkness" of the fold shadow
        h_depth = (smoothed.max() - smoothed.min()) / 2

        # Estimate fold width using parabolic geometry
        # Formula derived from parabola properties: width = 2√(depth/curvature)
        # Ensures wider analysis for deeper folds, narrower for shallow folds
        width_est = int(2 * np.sqrt(h_depth / abs(a.item())))

        # Clamp width to reasonable bounds for book scans
        # Min 7px: ensures minimum sampling, Max 50px: prevents over-wide analysis
        width = np.clip(width_est, 7, 50)
    except Exception:
        # Fallback width for cases where parabolic fitting fails
        # 20px is empirically validated for typical book fold widths
        width = 20

    # Define Region of Interest (ROI) centered on fold with estimated width
    x_start = max(0, x_center - width // 2)
    x_end = min(gray.shape[1], x_center + width // 2 + 1)
    roi_strip = gray[:, x_start:x_end]

    # Sample fold points at regular vertical intervals
    xs, ys = [], []
    for y in range(0, h, step):
        # Find darkest point (fold minimum) in each horizontal slice
        col = roi_strip[y, :]
        x_local = np.argmin(col)  # Local minimum within ROI

        # Convert local coordinates back to global image coordinates
        xs.append(x_start + x_local)
        ys.append(y)

    # Linear regression on sampled fold points: x = ay + b
    # This gives us the fold line equation in global coordinates
    a, b = np.polyfit(ys, xs, 1)

    # Convert slope to angle in degrees
    # arctan(slope) gives radians, converted to degrees for intuitive interpretation
    angle = np.degrees(np.arctan(a))

    return angle, a, b, width


def get_roi_bounds(side, width, height):
    """
    ROI Boundary Calculation for Fold Detection
    ==========================================

    Calculates optimal Region of Interest boundaries based on detected fold side.
    Uses empirically validated ratios that balance detection accuracy with
    computational efficiency for typical book scan geometries.

    Args:
        side (str): Detected fold side ('left', 'right', 'center')
        width (int): Image width in pixels
        height (int): Image height in pixels (unused but kept for API consistency)

    Returns:
        tuple: (start_x, end_x) defining horizontal ROI boundaries

    ROI Strategy:
        - Right side: Focus on rightmost 20% where folds typically occur
        - Left side: Focus on leftmost 20% where folds typically occur
        - Center: Broader 40% range covering typical center fold positions
    """
    if side == "right":
        # Right fold: search in rightmost 20% of image
        # Typical binding position for right-bound books
        return int(0.8 * width), width
    elif side == "left":
        # Left fold: search in leftmost 20% of image
        # Typical binding position for left-bound books
        return 0, int(0.2 * width)
    elif side == "center":
        # Center fold: search in middle 40% of image
        # Covers typical spread of center binding positions
        return int(0.3 * width), int(0.7 * width)
    else:
        raise ValueError(f"Unsupported fold side: {side}")


def extract_brightness_profiles(roi, num_samples=40, num_rounds=10):
    """
    Multi-Round Statistical Brightness Profile Extraction with Enhanced Robustness
    ============================================================================

    Extracts horizontal brightness profiles using multiple random sampling rounds
    for superior statistical robustness. Each round samples different row positions,
    then all rounds are combined and filtered for optimal fold detection.

    Algorithm:
    1. Perform multiple random sampling rounds (default: 10)
    2. Each round extracts profiles from randomly selected vertical positions
    3. Combine all profiles and apply statistical outlier filtering (1.5σ rule)
    4. Compute ensemble statistics from all filtered profiles

    Args:
        roi (np.ndarray): Region of Interest grayscale image
        num_samples (int): Number of horizontal profiles per round (default: 40)
        num_rounds (int): Number of random sampling rounds (default: 10)

    Returns:
        tuple: (filtered_profiles, mean_profile, std_profile)
               - filtered_profiles (list): List of outlier-filtered brightness profiles
               - mean_profile (np.ndarray): Mean brightness profile across all samples
               - std_profile (np.ndarray): Standard deviation profile for uncertainty

    Statistical Foundation:
        - Total profiles: num_samples × num_rounds (default: 400 profiles)
        - Random sampling reduces spatial bias and improves coverage
        - Outlier threshold: 1.5 standard deviations from mean brightness
        - Enhanced robustness through larger statistical population
    """
    h = roi.shape[0]

    # Multiple rounds of random sampling for enhanced statistical robustness
    all_profiles = []

    for round_idx in range(num_rounds):
        # Generate random row indices for this sampling round
        # Ensures diverse spatial coverage and reduces sampling bias
        if h <= num_samples:
            # If ROI height <= num_samples, use all available rows
            rows = np.arange(h)
        else:
            # Random sampling without replacement for this round
            rows = np.random.choice(h, size=min(num_samples, h), replace=False)

        # Extract profiles for this round
        round_profiles = [(r, roi[r, :], roi[r, :].mean()) for r in rows]
        all_profiles.extend(round_profiles)

    # Calculate global statistics for outlier detection across all rounds
    avg_ints = np.array([t[2] for t in all_profiles])  # Extract mean brightness values
    mean_int = avg_ints.mean()  # Global mean brightness across all profiles
    std_int = avg_ints.std()  # Global brightness standard deviation

    # Statistical outlier filtering using 1.5σ rule across all profiles
    # Removes profiles with brightness significantly different from population mean
    # This eliminates scan artifacts, dust spots, or lighting irregularities
    filtered = [
        prof for (_, prof, avg) in all_profiles if abs(avg - mean_int) <= 1.5 * std_int
    ]

    # Safety fallback: if filtering removes all profiles, use unfiltered set
    # Ensures algorithm robustness in extreme cases
    if not filtered:
        filtered = [prof for (_, prof, _) in all_profiles]

    # Compute ensemble statistics from filtered profiles
    arr = np.array(filtered)
    mean_profile = arr.mean(axis=0)  # Mean brightness at each horizontal position
    std_profile = arr.std(axis=0)  # Brightness uncertainty at each position

    # ENHANCED: Round-by-round variance accumulation for anomaly detection
    # Calculate std for each individual round, then accumulate
    round_std_accumulator = np.zeros(arr.shape[1])
    profiles_per_round = len(filtered) // num_rounds

    for round_idx in range(num_rounds):
        start_idx = round_idx * profiles_per_round
        end_idx = (
            (round_idx + 1) * profiles_per_round
            if round_idx < num_rounds - 1
            else len(filtered)
        )

        if end_idx > start_idx:  # Ensure we have profiles for this round
            round_profiles = arr[start_idx:end_idx]
            round_std = np.std(round_profiles, axis=0)
            round_std_accumulator += round_std

    # Average the accumulated std across rounds
    # Areas with consistent anomalies (folds) will have high accumulated std
    # Areas with random noise will have low accumulated std
    accumulated_std_profile = round_std_accumulator / num_rounds

    # HEAVY SMOOTHING before derivative calculation to reduce noise
    # Use adaptive kernel size based on profile length
    kernel_size = max(15, len(accumulated_std_profile) // 20)
    if kernel_size % 2 == 0:
        kernel_size += 1  # Ensure odd kernel size

    # Apply strong Gaussian smoothing
    smoothed_profile = cv2.GaussianBlur(
        accumulated_std_profile.reshape(1, -1), (kernel_size, 1), sigmaX=3.0
    ).flatten()

    # Calculate second derivative on smoothed profile for clean zero-crossing detection
    # First derivative (gradient)
    first_derivative = np.gradient(smoothed_profile)
    # Second derivative (curvature) - zero crossings indicate fold peaks/valleys
    second_derivative = np.gradient(first_derivative)

    return filtered, mean_profile, std_profile, accumulated_std_profile, second_derivative, smoothed_profile 


def find_fold_position(mean_profile, std_profile, x0):
    """
    Precise Fold Position Localization via Parabolic Curve Fitting
    =============================================================

    Determines precise fold position by fitting a parabolic curve to the
    combined mean+std brightness profile. Uses curve optimization to find
    the exact minimum position with sub-pixel accuracy.

    Algorithm:
    1. Combine mean and std profiles for enhanced fold contrast
    2. Apply Gaussian smoothing for noise reduction
    3. Find approximate minimum position
    4. Define local fitting window around minimum
    5. Fit parabolic curve to windowed data
    6. Calculate exact vertex position (true minimum)
    7. Convert back to global image coordinates

    Args:
        mean_profile (np.ndarray): Mean brightness profile from statistical analysis
        std_profile (np.ndarray): Standard deviation profile for uncertainty weighting
        x0 (int): ROI starting x-coordinate for coordinate transformation

    Returns:
        tuple: (x_final, confidence_data)
               - x_final (int): Precise fold position in global image coordinates
               - confidence_data (dict): Data for confidence calculation
    """
    # Enhance fold contrast by combining mean brightness with uncertainty
    # Areas with high std_profile indicate inconsistent brightness (potential folds)
    enhanced_profile = mean_profile + std_profile

    # Apply Gaussian smoothing to reduce high-frequency noise
    # Kernel width 11: balances smoothing with feature preservation
    smooth = cv2.GaussianBlur(enhanced_profile, (11, 1), 0).flatten()

    # Find approximate minimum position as starting point for refinement
    x_min = np.argmin(smooth)

    # Define local fitting window: ±15 pixels around approximate minimum
    # Window size balances fitting stability with local accuracy
    x_fit = np.arange(max(0, x_min - 15), min(len(smooth), x_min + 16))
    y_fit = smooth[x_fit]

    # Fit parabolic curve to windowed data using least-squares optimization
    # parabola function: f(x) = ax² + bx + c
    popt, _ = curve_fit(parabola, x_fit, y_fit)

    # Calculate exact parabola vertex (minimum) position
    # For f(x) = ax² + bx + c, minimum occurs at x = -b/(2a)
    x_refined = -popt[1] / (2 * popt[0])

    # Convert refined local coordinate back to global image coordinates
    x_final = int(round(x0 + x_refined))

    # Collect confidence data
    confidence_data = {
        'enhanced_profile': enhanced_profile,
        'smooth_profile': smooth,
        'parabolic_params': popt,
        'fit_window': (x_fit, y_fit),
        'min_position': x_min,
        'profile_stats': {
            'mean': np.mean(smooth),
            'std': np.std(smooth),
            'min_value': np.min(smooth),
            'max_value': np.max(smooth)
        }
    }

    return x_final, confidence_data


def calculate_fold_confidence(confidence_data, mean_profile, std_profile):
    """
    Calculate Fold Detection Confidence Score
    ========================================

    Evaluates fold detection quality using multiple independent indicators:
    - Brightness contrast (fold depth)
    - Profile sharpness (fold clarity)
    - Statistical consistency (fold stability)
    - Parabolic fit quality (fold shape)

    Args:
        confidence_data (dict): Data from fold position detection
        mean_profile (np.ndarray): Mean brightness profile
        std_profile (np.ndarray): Standard deviation profile

    Returns:
        float: Confidence score between 0.0 (poor) and 1.0 (excellent)
    """
    smooth = confidence_data['smooth_profile']
    stats = confidence_data['profile_stats']

    # 1. Brightness contrast indicator (0-1)
    # Higher contrast = deeper fold shadow = better detection
    brightness_range = stats['max_value'] - stats['min_value']
    contrast_score = min(brightness_range / 50.0, 1.0)  # Normalize to 50 brightness units

    # 2. Profile sharpness indicator (0-1)
    # Sharp fold creates high gradient around minimum
    gradient = np.abs(np.gradient(smooth))
    max_gradient = np.max(gradient)
    sharpness_score = min(max_gradient / 10.0, 1.0)  # Normalize to 10 gradient units

    # 3. Statistical consistency indicator (0-1)
    # Low std at fold position indicates stable detection
    fold_position = np.argmin(smooth)
    fold_std = std_profile[min(fold_position, len(std_profile)-1)]
    mean_std = np.mean(std_profile)
    consistency_score = max(0.0, 1.0 - (fold_std / max(mean_std, 1.0)))

    # 4. Parabolic fit quality indicator (0-1)
    # Good parabolic fit indicates clear fold shape
    x_fit, y_fit = confidence_data['fit_window']
    a, b, c = confidence_data['parabolic_params']

    # Calculate predicted values and residuals
    y_pred = a * x_fit**2 + b * x_fit + c
    residuals = y_fit - y_pred
    rmse = np.sqrt(np.mean(residuals**2))

    # Lower RMSE = better fit
    fit_score = max(0.0, 1.0 - (rmse / 20.0))  # Normalize to 20 RMSE units

    # 5. Fold position reliability (0-1)
    # Check if minimum is well-defined (not at edge)
    edge_distance = min(fold_position, len(smooth) - 1 - fold_position)
    position_score = min(edge_distance / 10.0, 1.0)  # Normalize to 10 pixels from edge

    # Weighted combination of all indicators
    confidence = (
        0.25 * contrast_score +      # Fold depth
        0.20 * sharpness_score +     # Fold clarity
        0.20 * consistency_score +   # Statistical stability
        0.20 * fit_score +           # Shape quality
        0.15 * position_score        # Position reliability
    )

    return confidence




def detect_fold_brightness_profile(img, side, debug=False, debug_dir=None):
    """
    Main Fold Detection Pipeline via Statistical Brightness Analysis
    ==============================================================

    Primary entry point for fold detection. Orchestrates the complete detection
    pipeline from ROI definition through statistical analysis to precise fold
    localization and angle estimation.

    Processing Pipeline:
    1. Convert image to grayscale and apply noise reduction
    2. Define Region of Interest based on detected fold side
    3. Extract and filter brightness profiles using statistical methods
    4. Apply parabolic curve fitting for precise fold localization
    5. Estimate fold angle via linear regression on sampled points
    6. Generate debug visualizations if requested

    Args:
        img (np.ndarray): Input BGR image (H, W, 3)
        side (str): Detected fold side ('left', 'right', 'center')
        debug (bool): Enable debug visualization generation
        debug_dir (str): Output directory for debug files

    Returns:
        tuple: (x_final, angle, slope, intercept, confidence)
               - x_final (int): Precise fold position in image coordinates
               - angle (float): Fold angle in degrees
               - slope (float): Linear regression slope coefficient
               - intercept (float): Linear regression intercept
               - confidence (float): Fold detection confidence (0.0-1.0)

    Integration Notes:
        - Coordinates returned are in global image coordinate system
        - Angle is in degrees for intuitive interpretation
        - Debug files saved with standardized naming convention
        - All processing uses grayscale conversion for computational efficiency
    """
    from . import fold_debug  # Import debug module for visualization

    # Image preprocessing: convert to grayscale and apply noise reduction
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Gaussian blur reduces sensor noise while preserving fold features
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Define processing region based on fold side detection
    h, w = blur.shape
    x0, x1 = get_roi_bounds(side, w, h)  # Get horizontal ROI boundaries
    roi = blur[:, x0:x1]  # Extract region of interest

    # Statistical brightness profile analysis
    x_axis = np.arange(x0, x1)  # Coordinate array for visualization
    # Extract profiles with statistical outlier filtering and round-based variance accumulation
    filtered_profiles, mean_profile, std_profile, accumulated_std_profile, second_derivative, smoothed_profile = (
        extract_brightness_profiles(roi)
    )

    # Apply parabolic curve fitting for precise localization
    x_final, confidence_data = find_fold_position(mean_profile, std_profile, x0)
    detection_method = "parabolic"

    # Calculate fold detection confidence
    confidence = calculate_fold_confidence(confidence_data, mean_profile, std_profile)

    # Fold angle estimation via linear regression
    # Uses the original grayscale image for full-height analysis
    angle, a, b, width = estimate_fold_angle_from_profile(gray, x_final, step=3)

    # Generate debug visualizations if requested
    if debug and debug_dir:
        fold_debug.save_fold_profile_debug(
            filtered_profiles,
            mean_profile,
            std_profile,
            x_axis,
            x_final,
            roi,
            debug_dir,
            accumulated_std_profile=accumulated_std_profile,
            detection_method=detection_method,
            second_derivative=second_derivative,
        )

    # Return fold characteristics and confidence for downstream processing
    return x_final, angle, a, b, confidence


