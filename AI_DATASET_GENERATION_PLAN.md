# AI Training Dataset Generation - Implementation Plan

## 🎯 Project Overview

Create a data labeling system that captures computer vision detection outputs (page corners + fold lines) from the existing processing pipeline to generate a neural network training dataset.

**Purpose**: Use the current rule-based CV pipeline as a labeling tool to create training data for a future neural network that will learn to detect page boundaries and fold lines directly from raw images.

---

## 📊 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: Raw Scanned Image (variable size, e.g., 4000×3000)     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ├─ Page Contour Detection (detect.py)
                     │  └─> approx_contour (4 corners in original pixel space)
                     │
                     ├─ Perspective Transformation (warp_image)
                     │  ├─> Matrix M (2×3 affine transform)
                     │  └─> rectified_img (warped/rotated image)
                     │
                     ├─ Fold Detection (process_image)
                     │  └─> x_fold, angle, slope, intercept (in rectified space)
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATASET GENERATION MODULE                          │
│                                                                 │
│  1. Resize ORIGINAL image → 512×512 (letterbox, black padding) │
│  2. Transform page corners: original coords → 512×512 coords   │
│  3. Transform fold line:                                       │
│     a) Apply M^(-1) to fold: rectified space → original space  │
│     b) Scale to 512×512 space                                  │
│  4. Generate JSON label with transformed coordinates           │
│  5. Save to _AI_training/dataset/                              │
│  6. Generate debug visualization to _AI_training/debug/        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 New File Structure

```
src/projects/project2/python/
├── src/
│   ├── dataset/                          # New package
│   │   ├── __init__.py
│   │   ├── resize_utils.py              # Image resize with letterbox padding
│   │   ├── coordinate_transform.py      # Coordinate transformation logic
│   │   ├── label_generator.py           # JSON label creation
│   │   ├── debug_visualizer.py          # Debug image generation
│   │   └── dataset_writer.py            # Main orchestrator
│   │
│   └── contour_detector/
│       └── transform.py                  # MODIFY: return M from warp_image()
│
├── main.py                               # MODIFY: add --generate-dataset flag
└── crop.py                               # MODIFY: add --generate-dataset flag

OUTPUT STRUCTURE:
_AI_training/
├── dataset/
│   ├── IMG_00001.jpg                     # 512×512 letterboxed original
│   ├── IMG_00001.json                    # Label file
│   ├── IMG_00002.jpg
│   ├── IMG_00002.json
│   └── ...
├── debug/
│   ├── IMG_00001_debug.jpg               # Visualization with corners + fold
│   ├── IMG_00002_debug.jpg
│   └── ...
└── metadata.json                         # Global dataset summary
```

---

## 🔧 Implementation Details

### **1. Resize Utils** (`src/dataset/resize_utils.py`)

**Purpose**: Resize variable-size images to 512×512 with letterbox padding

```python
def resize_with_letterbox(img, target_size=512):
    """
    Resize image to target_size×target_size with aspect ratio preservation.
    Add black letterbox padding to maintain square shape.

    Args:
        img: numpy array (H, W, 3) in BGR
        target_size: int, target dimension (default 512)

    Returns:
        resized_img: (target_size, target_size, 3) array
        scale: float, scaling factor applied
        offset_x: int, horizontal padding offset
        offset_y: int, vertical padding offset

    Algorithm:
        1. Calculate aspect ratio
        2. Scale to fit within target_size
        3. Add black padding (0, 0, 0) to center image
    """
```

**Example**:
- Input: 4000×3000 image
- Scale: 512/4000 = 0.128
- Scaled: 512×384
- Padding: 0×64 (top) + 0×64 (bottom)
- Output: 512×512, scale=0.128, offset_x=0, offset_y=64

---

### **2. Coordinate Transform** (`src/dataset/coordinate_transform.py`)

**Purpose**: Transform detection coordinates from original/rectified space to 512×512 dataset space

```python
def transform_page_corners(corners_original, scale, offset_x, offset_y):
    """
    Transform page corners from original image space to 512×512 space.

    Args:
        corners_original: numpy array (4, 2) - corners in original pixel coords
        scale: float from resize_with_letterbox
        offset_x, offset_y: int offsets from resize_with_letterbox

    Returns:
        corners_512: numpy array (4, 2) - corners in 512×512 pixel coords

    Formula:
        x_512 = x_original * scale + offset_x
        y_512 = y_original * scale + offset_y
    """

def inverse_transform_fold_to_original(x_fold, img_height_rectified, M):
    """
    Transform fold line from rectified space back to original image space.

    Args:
        x_fold: int, X coordinate of vertical fold in rectified image
        img_height_rectified: int, height of rectified image
        M: numpy array (2, 3) - affine transformation matrix from warp_image

    Returns:
        fold_point1: (x1, y1) - top point of fold line in original space
        fold_point2: (x2, y2) - bottom point of fold line in original space

    Algorithm:
        1. Define fold line in rectified space as vertical line:
           - point1_rect = (x_fold, 0)
           - point2_rect = (x_fold, img_height_rectified)

        2. Apply inverse transformation M^(-1):
           - M_inv = cv2.invertAffineTransform(M)
           - Transform both points using M_inv

        3. Return points in original image coordinates
    """

def transform_fold_to_512(fold_p1_original, fold_p2_original, scale, offset_x, offset_y):
    """
    Transform fold line points from original space to 512×512 space.

    Args:
        fold_p1_original: (x, y) tuple in original coords
        fold_p2_original: (x, y) tuple in original coords
        scale, offset_x, offset_y: from resize_with_letterbox

    Returns:
        fold_p1_512: (x, y) in 512×512 space
        fold_p2_512: (x, y) in 512×512 space
    """
```

---

### **3. Label Generator** (`src/dataset/label_generator.py`)

**Purpose**: Create JSON label files matching the specified schema

```python
def create_label_dict(
    filename,
    filepath,
    page_present,
    page_corners_512,
    fold_present,
    fold_p1_512,
    fold_p2_512,
    resize_params
):
    """
    Generate label dictionary in the required JSON format.

    Returns:
        {
            "filename": "IMG_00123.jpg",
            "filepath": "_AI_training/dataset/IMG_00123.jpg",
            "page_present": true,
            "page_corners": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],  # pixels
            "fold_present": true,
            "fold_line": {
                "point1": [x1, y1],  # pixels
                "point2": [x2, y2]   # pixels
            },
            "resize_params": {
                "target_size": [512, 512],
                "scale": 0.128,
                "offset_x": 0,
                "offset_y": 64,
                "original_size": [4000, 3000]
            }
        }

    Note: All coordinates in absolute pixel values (0-512 range)
    """

def save_label_json(label_dict, output_path):
    """Save label dictionary to JSON file with proper formatting."""
```

---

### **4. Debug Visualizer** (`src/dataset/debug_visualizer.py`)

**Purpose**: Generate debug images showing detections overlaid on 512×512 images

```python
def draw_debug_visualization(
    img_512,
    page_corners_512,
    fold_p1_512,
    fold_p2_512,
    page_present,
    fold_present
):
    """
    Draw detection overlays on 512×512 image for debugging.

    Visualization:
        - Page corners: Green circles (radius=5) with labels P1, P2, P3, P4
        - Page boundary: Green polyline connecting corners
        - Fold line: Red line (thickness=2) from point1 to point2
        - Text annotations with detection status

    Args:
        img_512: numpy array (512, 512, 3) - letterboxed image
        page_corners_512: list of 4 (x,y) tuples or None
        fold_p1_512, fold_p2_512: (x,y) tuples or None
        page_present: bool
        fold_present: bool

    Returns:
        debug_img: numpy array (512, 512, 3) with overlays drawn

    Colors:
        - Green (0, 255, 0): Page detection
        - Red (0, 0, 255): Fold detection
        - White (255, 255, 255): Text labels
    """
```

---

### **5. Dataset Writer** (`src/dataset/dataset_writer.py`)

**Purpose**: Main orchestrator that coordinates all dataset generation steps

```python
class DatasetWriter:
    """
    Main class for generating AI training dataset during image processing.
    """

    def __init__(self, output_base_dir, dataset_subdir="dataset", debug_subdir="debug"):
        """
        Initialize dataset writer.

        Args:
            output_base_dir: Base output directory (e.g., "/path/to/output")
            dataset_subdir: Subfolder for dataset (default: "dataset")
            debug_subdir: Subfolder for debug images (default: "debug")

        Creates:
            {output_base_dir}/_AI_training/dataset/
            {output_base_dir}/_AI_training/debug/
        """
        self.ai_training_dir = os.path.join(output_base_dir, "_AI_training")
        self.dataset_dir = os.path.join(self.ai_training_dir, dataset_subdir)
        self.debug_dir = os.path.join(self.ai_training_dir, debug_subdir)
        self.samples_generated = []

        os.makedirs(self.dataset_dir, exist_ok=True)
        os.makedirs(self.debug_dir, exist_ok=True)

    def add_sample(
        self,
        original_img,           # Raw input image (variable size)
        filename,               # Base filename (e.g., "IMG_00123.jpg")
        page_corners_original,  # (4,2) array or None
        rectified_img,          # Warped image or None
        transformation_matrix,  # M from warp_image (2,3) or None
        fold_x,                 # X coord in rectified space or None
        fold_detected           # bool
    ):
        """
        Process one image and generate dataset sample.

        Steps:
            1. Resize original image to 512×512 with letterbox
            2. Transform page corners to 512×512 space
            3. If fold detected:
               - Inverse transform fold from rectified to original
               - Transform fold to 512×512 space
            4. Generate JSON label
            5. Save 512×512 image to dataset/
            6. Generate and save debug visualization to debug/
            7. Track in samples_generated list

        Returns:
            success: bool
        """

    def finalize(self):
        """
        Generate metadata.json with dataset summary.

        Creates:
            _AI_training/metadata.json

        Content:
            {
                "total_samples": 150,
                "samples_with_page": 148,
                "samples_with_fold": 142,
                "target_size": [512, 512],
                "generated_at": "2025-10-06T14:30:00",
                "samples": [
                    {
                        "filename": "IMG_00001.jpg",
                        "page_present": true,
                        "fold_present": true
                    },
                    ...
                ]
            }
        """
```

---

## 🔄 Modification Points in Existing Code

### **Modification 1**: `src/contour_detector/transform.py`

**Function**: `warp_image()`

**Change**: Add transformation matrix `M` to return values

```python
# Current signature:
def warp_image(...) -> (cropped, crop_no_rotation)

# New signature:
def warp_image(...) -> (cropped, crop_no_rotation, M)

# Return the transformation matrix M that was calculated internally
# This matrix is already computed around line ~250 in the function
```

**Impact**:
- Minimal - just add one more return value
- M is already calculated internally
- All callers need to handle 3 return values instead of 2

---

### **Modification 2**: `main.py`

**Changes**:

1. **Add command-line argument**:
```python
parser.add_argument(
    "--generate-dataset",
    action="store_true",
    default=False,
    help="Generate AI training dataset in _AI_training/ folder"
)
```

2. **Initialize DatasetWriter**:
```python
dataset_writer = None
if args.generate_dataset:
    from src.dataset.dataset_writer import DatasetWriter
    dataset_writer = DatasetWriter(args.output_dir)
    print("[DATASET] AI training dataset generation ENABLED")
```

3. **In `process_single_image()` function**:
   - Capture `page_corners` after contour detection
   - Capture `M` from modified `warp_image()`
   - After processing, call `dataset_writer.add_sample(...)` if enabled

4. **After processing all images**:
```python
if dataset_writer:
    dataset_writer.finalize()
    print("[DATASET] AI training dataset generation completed")
```

---

### **Modification 3**: `crop.py`

**Changes**: Same as main.py but for single-image processing

1. Add `--generate-dataset` argument
2. Initialize DatasetWriter if flag present
3. Capture detection data and call `add_sample()`
4. Call `finalize()`

---

## 📋 JSON Label Schema

### Example 1: Full Detection (Page + Fold)

```json
{
  "filename": "IMG_00123.jpg",
  "filepath": "_AI_training/dataset/IMG_00123.jpg",
  "page_present": true,
  "page_corners": [
    [45, 32],
    [478, 28],
    [482, 488],
    [41, 492]
  ],
  "fold_present": true,
  "fold_line": {
    "point1": [256, 35],
    "point2": [262, 485]
  },
  "resize_params": {
    "target_size": [512, 512],
    "scale": 0.128,
    "offset_x": 0,
    "offset_y": 12,
    "original_size": [4000, 3000]
  }
}
```

### Example 2: Page Only (No Fold)

```json
{
  "filename": "IMG_00124.jpg",
  "filepath": "_AI_training/dataset/IMG_00124.jpg",
  "page_present": true,
  "page_corners": [
    [52, 38],
    [461, 35],
    [465, 479],
    [48, 482]
  ],
  "fold_present": false,
  "fold_line": null,
  "resize_params": {
    "target_size": [512, 512],
    "scale": 0.17,
    "offset_x": 32,
    "offset_y": 0,
    "original_size": [3000, 3000]
  }
}
```

### Example 3: No Detection

```json
{
  "filename": "IMG_00125.jpg",
  "filepath": "_AI_training/dataset/IMG_00125.jpg",
  "page_present": false,
  "page_corners": null,
  "fold_present": false,
  "fold_line": null,
  "resize_params": {
    "target_size": [512, 512],
    "scale": 0.21,
    "offset_x": 0,
    "offset_y": 48,
    "original_size": [2448, 1836]
  }
}
```

---

## 🧮 Transformation Mathematics

### **Step 1: Page Corners Transformation**

Given:
- Original image size: `(W_orig, H_orig)`
- Target size: `512×512`
- Scale: `s = min(512/W_orig, 512/H_orig)`
- Offsets: `(offset_x, offset_y)` from centering

Transform:
```
x_512 = x_original × s + offset_x
y_512 = y_original × s + offset_y
```

### **Step 2: Fold Line Inverse Transformation**

Given:
- Fold position in rectified image: `x_fold`
- Rectified image height: `H_rect`
- Transformation matrix: `M` (2×3 affine matrix from warp_image)

Process:
```python
# Define fold line in rectified space (vertical line)
fold_top_rect = [x_fold, 0]
fold_bottom_rect = [x_fold, H_rect]

# Compute inverse transformation
M_inv = cv2.invertAffineTransform(M)

# Transform points back to original space
fold_top_orig = apply_affine_inverse(fold_top_rect, M_inv)
fold_bottom_orig = apply_affine_inverse(fold_bottom_rect, M_inv)

# Now scale to 512×512
fold_top_512 = transform_point(fold_top_orig, scale, offset_x, offset_y)
fold_bottom_512 = transform_point(fold_bottom_orig, scale, offset_x, offset_y)
```

**Important**: The fold line will appear **inclined** in the original/512×512 space because it was vertical only after rotation!

---

## 🧪 Testing Strategy

### Unit Tests

1. **test_resize_utils.py**
   - Various aspect ratios (landscape, portrait, square)
   - Edge cases (very small, very large images)
   - Verify padding is black (0, 0, 0)

2. **test_coordinate_transform.py**
   - Identity transforms (no scaling/offset)
   - Known transformations with hand-calculated results
   - Inverse transformation round-trip accuracy

3. **test_label_generator.py**
   - Schema validation
   - Null handling (no page/fold cases)
   - JSON serialization/deserialization

### Integration Tests

1. **test_full_pipeline.py**
   - Run on sample images with known ground truth
   - Verify JSON labels are created
   - Verify debug images are generated
   - Check coordinate ranges (0-512)

---

## 📦 Step-by-Step Implementation Order

### **Phase 1: Core Utilities** (No dependencies)
1. ✅ Create `src/dataset/__init__.py`
2. ✅ Implement `resize_utils.py`
3. ✅ Implement `coordinate_transform.py`
4. ✅ Implement `label_generator.py`
5. ✅ Write unit tests for above

### **Phase 2: Visualization** (Depends on Phase 1)
6. ✅ Implement `debug_visualizer.py`
7. ✅ Test debug visualization manually

### **Phase 3: Orchestrator** (Depends on Phases 1-2)
8. ✅ Implement `dataset_writer.py`
9. ✅ Write integration tests

### **Phase 4: Code Integration** (Depends on Phase 3)
10. ✅ Modify `warp_image()` to return M
11. ✅ Update all callers of `warp_image()` (page_processor.py, etc.)
12. ✅ Add dataset generation to `main.py`
13. ✅ Add dataset generation to `crop.py`
14. ✅ Test end-to-end with sample images

### **Phase 5: Validation** (Final testing)
15. ✅ Run on full dataset
16. ✅ Manually inspect debug visualizations
17. ✅ Validate JSON labels
18. ✅ Verify coordinate accuracy

---

## 🚀 Usage Examples

### Batch Processing with Dataset Generation

```bash
python main.py \
  /path/to/input \
  /path/to/output \
  --generate-dataset \
  --verbose

# Creates:
# /path/to/output/_AI_training/dataset/*.jpg + *.json
# /path/to/output/_AI_training/debug/*_debug.jpg
# /path/to/output/_AI_training/metadata.json
```

### Single Image with Dataset Generation

```bash
python crop.py \
  input_image.jpg \
  output_dir/ \
  --generate-dataset \
  --debug

# Creates:
# output_dir/_AI_training/dataset/input_image.jpg
# output_dir/_AI_training/dataset/input_image.json
# output_dir/_AI_training/debug/input_image_debug.jpg
```

---

## 📊 Expected Output Structure

```
output/
├── _AI_training/
│   ├── dataset/
│   │   ├── IMG_0001.jpg          # 512×512 letterboxed
│   │   ├── IMG_0001.json         # Label
│   │   ├── IMG_0002.jpg
│   │   ├── IMG_0002.json
│   │   └── ...
│   │
│   ├── debug/
│   │   ├── IMG_0001_debug.jpg    # With corners + fold drawn
│   │   ├── IMG_0002_debug.jpg
│   │   └── ...
│   │
│   └── metadata.json             # Dataset summary
│
├── IMG_0001_left.jpg             # Normal processing outputs
├── IMG_0001_right.jpg
└── ...
```

---

## ⚠️ Important Notes

1. **Original Images**: Dataset always uses ORIGINAL raw scans, never rectified
2. **Coordinate Space**: All JSON coordinates in absolute pixels (0-512 range)
3. **Fold Inclination**: Fold appears inclined in original/512 space (vertical only in rectified)
4. **Padding Color**: Black (0, 0, 0) for letterbox padding
5. **Matrix M**: Must be captured from `warp_image()` return value
6. **Inverse Transform**: Use `cv2.invertAffineTransform(M)` for fold line
7. **Optional Generation**: Dataset generation is opt-in via `--generate-dataset` flag
8. **No Interference**: Normal processing outputs unaffected when flag disabled

---

## 🎓 Neural Network Training Context

The generated dataset will train a model to:

**Input**: Raw scanned image (512×512, RGB)

**Output**:
- Page bounding box: 4 corner points (x, y) in pixel coordinates
- Fold line: 2 points (x, y) defining the fold line
- Confidence scores for each detection

**Architecture Suggestion** (not part of implementation):
- Backbone: ResNet/EfficientNet for feature extraction
- Head: Keypoint detection network
- Loss: MSE on coordinates + BCE on presence flags

---

## 📝 Summary

This plan creates a complete data labeling system that:
- ✅ Captures CV detections during processing
- ✅ Transforms coordinates to 512×512 dataset space
- ✅ Handles inverse transformations for fold lines
- ✅ Generates structured JSON labels
- ✅ Creates debug visualizations
- ✅ Integrates seamlessly with existing pipeline
- ✅ Requires minimal code modifications
- ✅ Preserves original processing functionality

**Ready to implement step-by-step upon approval.**
