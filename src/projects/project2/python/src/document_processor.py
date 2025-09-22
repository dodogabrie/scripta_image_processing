"""
document_processor.py

Main Document Processing Pipeline
===============================

This module provides the main entry point for document processing, orchestrating
the complete pipeline from initial analysis through fold detection and final output.
It integrates document segmentation, metadata analysis, and fold detection modules.

Processing Pipeline:
1. Document segmentation and boundary detection
2. Metadata analysis and format detection
3. Fold presence evaluation
4. Conditional fold detection (if recommended)
5. Final results compilation

Key Features:
- Automatic A4 format detection
- Intelligent fold detection decision making
- Quality assessment and recommendations
- Comprehensive results reporting
- Debug output generation

Author: [Generated Documentation]
Version: 1.0
"""

import cv2
import numpy as np
import os
from typing import Dict, Optional, Tuple, Any

from .document_segmentation import get_document_boundaries, analyze_background_page_brightness
from .metadata_analyzer import analyze_document_metadata
from .fold_detection import auto_detect_side, detect_fold_brightness_profile


class DocumentProcessor:
    """
    Main document processing pipeline class.

    This class orchestrates the complete document processing workflow,
    from initial analysis through fold detection and final output generation.
    """

    def __init__(self, debug: bool = False, debug_dir: Optional[str] = None):
        """
        Initialize the document processor.

        Args:
            debug (bool): Enable debug output generation
            debug_dir (Optional[str]): Directory for debug files
        """
        self.debug = debug
        self.debug_dir = debug_dir

        if self.debug and self.debug_dir:
            os.makedirs(self.debug_dir, exist_ok=True)

    def process_document(self, img: np.ndarray) -> Dict[str, Any]:
        """
        Process a document image through the complete pipeline.

        Args:
            img (np.ndarray): Input BGR image

        Returns:
            Dict[str, Any]: Complete processing results including:
                          - document_boundaries: Page boundary information
                          - metadata: Document format and content analysis
                          - fold_detection: Fold detection results (if applied)
                          - processing_summary: Overall results and recommendations
        """
        results = {
            "success": False,
            "processing_stages": [],
            "document_boundaries": None,
            "metadata": None,
            "fold_detection": None,
            "processing_summary": None,
            "debug_files": []
        }

        try:
            # Stage 1: Document Segmentation
            print("Stage 1: Analyzing document boundaries...")
            boundary_analysis = get_document_boundaries(img)
            results["document_boundaries"] = boundary_analysis
            results["processing_stages"].append("BOUNDARY_ANALYSIS")

            if self.debug and self.debug_dir:
                bg_analysis = boundary_analysis.get("full_analysis")
                if bg_analysis:
                    from . import fold_debug
                    fold_debug.save_background_analysis_debug(
                        bg_analysis, self.debug_dir, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    )
                    results["debug_files"].append("background_analysis_debug.png")

            # Stage 2: Metadata Analysis
            print("Stage 2: Analyzing document metadata...")
            page_boundaries = None
            if boundary_analysis["success"]:
                page_boundaries = boundary_analysis["page_boundaries"]

            metadata = analyze_document_metadata(img, page_boundaries)
            results["metadata"] = metadata
            results["processing_stages"].append("METADATA_ANALYSIS")

            # Stage 3: Fold Detection Decision
            print("Stage 3: Evaluating fold detection necessity...")
            should_detect_fold = self._should_apply_fold_detection(metadata, boundary_analysis)

            if should_detect_fold:
                print("Stage 4: Applying fold detection...")
                fold_results = self._apply_fold_detection(img, metadata, boundary_analysis)
                results["fold_detection"] = fold_results
                results["processing_stages"].append("FOLD_DETECTION")

                if self.debug and self.debug_dir and fold_results:
                    # Debug files are generated within fold detection
                    results["debug_files"].extend([
                        "fold_profile_debug.png",
                        "fold_profile_enhanced_debug.png"
                    ])
            else:
                print("Stage 4: Fold detection skipped (not recommended)")
                results["fold_detection"] = {
                    "applied": False,
                    "reason": "Not recommended based on analysis"
                }
                results["processing_stages"].append("FOLD_DETECTION_SKIPPED")

            # Stage 5: Generate Processing Summary
            processing_summary = self._generate_processing_summary(
                boundary_analysis, metadata, results["fold_detection"]
            )
            results["processing_summary"] = processing_summary
            results["processing_stages"].append("SUMMARY_GENERATION")

            results["success"] = True
            print("Document processing completed successfully!")

        except Exception as e:
            print(f"Error during document processing: {str(e)}")
            results["error"] = str(e)
            results["success"] = False

        return results

    def _should_apply_fold_detection(self, metadata: Dict, boundary_analysis: Dict) -> bool:
        """
        Determine whether fold detection should be applied based on analysis results.

        Args:
            metadata (Dict): Metadata analysis results
            boundary_analysis (Dict): Boundary analysis results

        Returns:
            bool: True if fold detection should be applied
        """
        # Check metadata recommendation
        if metadata["fold_detection_recommended"]:
            return True

        # Check if document quality is suitable
        if not metadata["processing_suitable"]:
            print("Skipping fold detection: Poor image quality")
            return False

        # Check if document has clear boundaries
        if not boundary_analysis["success"]:
            print("Skipping fold detection: Could not detect document boundaries")
            return False

        # Additional checks for wide documents (likely double-page spreads)
        w, h = metadata["dimensions"]
        aspect_ratio = w / h

        if aspect_ratio > 1.8:  # Very wide documents
            print("Applying fold detection: Wide document suggests double-page spread")
            return True

        # Check fold likelihood score
        fold_likelihood = metadata["fold_analysis"]["fold_likelihood"]
        if fold_likelihood > 0.3:  # Lower threshold for borderline cases
            print(f"Applying fold detection: Fold likelihood {fold_likelihood:.2f}")
            return True

        print(f"Skipping fold detection: Low fold likelihood {fold_likelihood:.2f}")
        return False

    def _apply_fold_detection(self, img: np.ndarray, metadata: Dict, boundary_analysis: Dict) -> Optional[Dict]:
        """
        Apply fold detection to the document.

        Args:
            img (np.ndarray): Input image
            metadata (Dict): Metadata analysis results
            boundary_analysis (Dict): Boundary analysis results

        Returns:
            Optional[Dict]: Fold detection results or None if failed
        """
        try:
            # Auto-detect fold side
            side = auto_detect_side(img)
            print(f"Detected fold side: {side}")

            # Apply fold detection
            x_fold, angle, slope, intercept = detect_fold_brightness_profile(
                img, side, debug=self.debug, debug_dir=self.debug_dir
            )

            # Detect document edges for cropping recommendations
            from .document_segmentation import detect_document_edge
            margin = detect_document_edge(
                img, side, x_fold, debug=self.debug, debug_dir=self.debug_dir
            )

            return {
                "applied": True,
                "success": True,
                "fold_position": int(x_fold),
                "fold_side": side,
                "fold_angle": float(angle),
                "fold_slope": float(slope),
                "fold_intercept": float(intercept),
                "document_margin": margin,
                "recommendations": self._generate_fold_recommendations(side, x_fold, margin, img.shape[1])
            }

        except Exception as e:
            print(f"Fold detection failed: {str(e)}")
            return {
                "applied": True,
                "success": False,
                "error": str(e)
            }

    def _generate_fold_recommendations(self, side: str, x_fold: int, margin: any, image_width: int) -> list:
        """Generate processing recommendations based on fold detection results."""
        recommendations = []

        # Cropping recommendations
        if isinstance(margin, tuple):  # Center fold
            left_margin, right_margin = margin
            if left_margin > 0:
                recommendations.append(f"CROP_LEFT: Remove {left_margin}px from left edge")
            if right_margin > 0:
                recommendations.append(f"CROP_RIGHT: Remove {right_margin}px from right edge")
        elif margin > 0:
            if side == "left":
                recommendations.append(f"CROP_RIGHT: Remove {margin}px from right edge")
            elif side == "right":
                recommendations.append(f"CROP_LEFT: Remove {margin}px from left edge")

        # Splitting recommendations for double-page spreads
        if side == "center":
            recommendations.append(f"SPLIT_PAGES: Split at fold position {x_fold}px")

        # Perspective correction recommendations
        recommendations.append("APPLY_PERSPECTIVE_CORRECTION: Use detected fold angle for correction")

        return recommendations

    def _generate_processing_summary(self, boundary_analysis: Dict, metadata: Dict, fold_detection: Dict) -> Dict:
        """
        Generate a comprehensive processing summary.

        Args:
            boundary_analysis (Dict): Boundary analysis results
            metadata (Dict): Metadata analysis results
            fold_detection (Dict): Fold detection results

        Returns:
            Dict: Processing summary with recommendations and quality assessment
        """
        summary = {
            "document_type": "UNKNOWN",
            "processing_quality": "UNKNOWN",
            "recommendations": [],
            "warnings": [],
            "statistics": {}
        }

        # Determine document type
        if metadata["is_a4"]:
            if fold_detection.get("applied") and fold_detection.get("success"):
                if fold_detection["fold_side"] == "center":
                    summary["document_type"] = "A4_DOUBLE_PAGE_SPREAD"
                else:
                    summary["document_type"] = "A4_SINGLE_PAGE_WITH_FOLD"
            else:
                summary["document_type"] = "A4_SINGLE_PAGE"
        else:
            summary["document_type"] = f"{metadata['page_format']}_DOCUMENT"

        # Assess processing quality
        quality_factors = []
        if boundary_analysis["success"]:
            quality_factors.append(boundary_analysis["quality"])
        quality_factors.append(metadata["quality_analysis"]["overall_quality"])

        avg_quality = self._calculate_average_quality(quality_factors)
        summary["processing_quality"] = avg_quality

        # Compile recommendations
        summary["recommendations"].extend(metadata["recommendations"])
        if fold_detection.get("recommendations"):
            summary["recommendations"].extend(fold_detection["recommendations"])

        # Add warnings
        if not boundary_analysis["success"]:
            summary["warnings"].append("Could not detect clear document boundaries")

        if metadata["quality_analysis"]["overall_quality"] == "POOR":
            summary["warnings"].append("Poor image quality may affect processing accuracy")

        if not metadata["processing_suitable"]:
            summary["warnings"].append("Image quality below recommended threshold")

        # Compile statistics
        summary["statistics"] = {
            "image_dimensions": metadata["dimensions"],
            "page_format": metadata["page_format"],
            "format_confidence": metadata["format_confidence"],
            "content_density": metadata["content_analysis"]["density_class"],
            "fold_likelihood": metadata["fold_analysis"]["fold_likelihood"],
            "processing_stages_completed": len([]),  # Will be filled by caller
        }

        if fold_detection.get("success"):
            summary["statistics"]["fold_detected"] = True
            summary["statistics"]["fold_position"] = fold_detection["fold_position"]
            summary["statistics"]["fold_side"] = fold_detection["fold_side"]
        else:
            summary["statistics"]["fold_detected"] = False

        return summary

    def _calculate_average_quality(self, quality_list: list) -> str:
        """Calculate average quality from list of quality assessments."""
        quality_scores = {
            "EXCELLENT": 4,
            "GOOD": 3,
            "FAIR": 2,
            "POOR": 1
        }

        scores = [quality_scores.get(q, 1) for q in quality_list]
        avg_score = sum(scores) / len(scores)

        if avg_score >= 3.5:
            return "EXCELLENT"
        elif avg_score >= 2.5:
            return "GOOD"
        elif avg_score >= 1.5:
            return "FAIR"
        else:
            return "POOR"


def process_document_image(image_path: str, debug: bool = False, debug_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for processing a document image from file path.

    Args:
        image_path (str): Path to the image file
        debug (bool): Enable debug output
        debug_dir (Optional[str]): Directory for debug files

    Returns:
        Dict[str, Any]: Complete processing results
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return {
            "success": False,
            "error": f"Could not load image from {image_path}"
        }

    # Create processor and run pipeline
    processor = DocumentProcessor(debug=debug, debug_dir=debug_dir)
    results = processor.process_document(img)

    # Add input information to results
    results["input_image"] = image_path
    results["input_dimensions"] = img.shape[:2]  # (height, width)

    return results


def print_processing_summary(results: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of processing results.

    Args:
        results (Dict[str, Any]): Processing results from process_document
    """
    if not results["success"]:
        print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
        return

    print("\n" + "="*60)
    print("📄 DOCUMENT PROCESSING SUMMARY")
    print("="*60)

    # Basic info
    summary = results["processing_summary"]
    metadata = results["metadata"]

    print(f"📋 Document Type: {summary['document_type']}")
    print(f"📏 Format: {metadata['page_format']} ({metadata['format_confidence']:.2f} confidence)")
    print(f"📐 Dimensions: {metadata['dimensions'][0]}x{metadata['dimensions'][1]} pixels")
    print(f"🎯 Processing Quality: {summary['processing_quality']}")

    # Fold detection results
    fold_detection = results["fold_detection"]
    if fold_detection["applied"] and fold_detection.get("success"):
        print(f"📌 Fold Detected: {fold_detection['fold_side']} side at position {fold_detection['fold_position']}px")
        print(f"📐 Fold Angle: {fold_detection['fold_angle']:.2f}°")
    elif fold_detection["applied"]:
        print("❌ Fold detection failed")
    else:
        print("⏭️  Fold detection skipped")

    # Recommendations
    if summary["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in summary["recommendations"]:
            print(f"   • {rec}")

    # Warnings
    if summary["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in summary["warnings"]:
            print(f"   • {warning}")

    # Processing stages
    print(f"\n✅ Completed Stages: {', '.join(results['processing_stages'])}")

    # Debug files
    if results["debug_files"]:
        print(f"🔍 Debug Files: {', '.join(results['debug_files'])}")

    print("="*60)