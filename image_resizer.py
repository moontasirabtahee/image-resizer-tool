import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List, Callable, Optional, Union, Dict, Any
from enum import Enum
import threading
import time


class FilterType(Enum):
    GRAYSCALE = "grayscale"
    BLUR = "blur"
    SHARPEN = "sharpen"
    EDGE_DETECT = "edge_detect"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    ROTATE = "rotate"
    FLIP = "flip"


class ImageResizer:
    def __init__(self, image_files: List[Union[str, Path]], output_folder: str):
        print(f"🚀 Initializing ImageResizer with {len(image_files)} files...")
        self.image_files = [Path(f) for f in image_files]
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        print(f"📁 Output folder: {self.output_folder.absolute()}")

        self.valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        self.should_stop = False
        self.lock = threading.Lock()

    def validate_images(self) -> Tuple[List[Path], List[Path]]:
        """Validate images and separate valid/invalid files"""
        print(f"🔍 Validating {len(self.image_files)} image files...")
        valid = []
        invalid = []

        for file in self.image_files:
            print(f"   Checking: {file.name}")
            if file.is_file() and file.suffix.lower() in self.valid_extensions:
                try:
                    test_img = cv2.imread(str(file))
                    if test_img is not None:
                        valid.append(file)
                        print(f"   ✅ Valid: {file.name}")
                    else:
                        invalid.append(file)
                        print(f"   ❌ Invalid (could not load): {file.name}")
                except Exception as e:
                    invalid.append(file)
                    print(f"   ❌ Invalid (error): {file.name} - {e}")
            else:
                invalid.append(file)
                print(f"   ❌ Invalid (wrong format): {file.name}")

        print(f"✅ {len(valid)} valid images, ❌ {len(invalid)} invalid images")
        return valid, invalid

    def calculate_new_size(self, original_size: Tuple[int, int],
                           width: Optional[int] = None,
                           height: Optional[int] = None,
                           percentage: Optional[float] = None) -> Tuple[int, int]:
        """Calculate new dimensions"""
        orig_width, orig_height = original_size

        if percentage:
            new_width = int(orig_width * percentage / 100)
            new_height = int(orig_height * percentage / 100)
            print(f"   📏 Resizing by percentage: {percentage}% → {new_width}x{new_height}")
        elif width and height:
            new_width, new_height = width, height
            print(f"   📏 Resizing to fixed size: {width}x{height}")
        elif width:
            ratio = width / orig_width
            new_width = width
            new_height = int(orig_height * ratio)
            print(f"   📏 Resizing by width: {width}px → {new_width}x{new_height}")
        elif height:
            ratio = height / orig_height
            new_width = int(orig_width * ratio)
            new_height = height
            print(f"   📏 Resizing by height: {height}px → {new_width}x{new_height}")
        else:
            raise ValueError("Must specify width, height, or percentage")

        return (max(1, new_width), max(1, new_height))

    def apply_grayscale(self, image: np.ndarray, **kwargs) -> np.ndarray:
        print("   🎨 Applying grayscale filter...")
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def apply_blur(self, image: np.ndarray, **kwargs) -> np.ndarray:
        print("   🎨 Applying blur filter...")
        return cv2.GaussianBlur(image, (7, 7), 0)

    def apply_sharpen(self, image: np.ndarray, **kwargs) -> np.ndarray:
        print("   🎨 Applying sharpen filter...")
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel)

    def apply_edge_detect(self, image: np.ndarray, **kwargs) -> np.ndarray:
        print("   🎨 Applying edge detection filter...")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    def apply_brightness(self, image: np.ndarray, value: int = 30, **kwargs) -> np.ndarray:
        print(f"   🎨 Adjusting brightness by {value}...")
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.add(v, value)
        v = np.clip(v, 0, 255)
        final_hsv = cv2.merge((h, s, v))
        return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)

    def apply_contrast(self, image: np.ndarray, value: float = 1.5, **kwargs) -> np.ndarray:
        print(f"   🎨 Adjusting contrast to {value}x...")
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=value, tileGridSize=(8, 8))
        l = clahe.apply(l)
        final_lab = cv2.merge((l, a, b))
        return cv2.cvtColor(final_lab, cv2.COLOR_LAB2BGR)

    def apply_rotate(self, image: np.ndarray, angle: int = 90, **kwargs) -> np.ndarray:
        print(f"   🔄 Rotating image by {angle}°...")
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, matrix, (w, h))

    def apply_flip(self, image: np.ndarray, direction: int = 1, **kwargs) -> np.ndarray:
        flip_map = {1: "horizontal", 0: "vertical", -1: "both"}
        print(f"   🔄 Flipping image {flip_map.get(direction, 'unknown')}...")
        return cv2.flip(image, direction)

    def apply_filters(self, image: np.ndarray, filter_config: Dict[str, Any]) -> np.ndarray:
        """Apply multiple filters based on configuration"""
        print(f"   🎨 Applying {len(filter_config)} filter(s)...")

        filters = {
            FilterType.GRAYSCALE.value: self.apply_grayscale,
            FilterType.BLUR.value: self.apply_blur,
            FilterType.SHARPEN.value: self.apply_sharpen,
            FilterType.EDGE_DETECT.value: self.apply_edge_detect,
            FilterType.BRIGHTNESS.value: self.apply_brightness,
            FilterType.CONTRAST.value: self.apply_contrast,
            FilterType.ROTATE.value: self.apply_rotate,
            FilterType.FLIP.value: self.apply_flip,
        }

        for filter_name, params in filter_config.items():
            if params.get('enabled', False):
                apply_func = filters.get(filter_name)
                if apply_func:
                    with self.lock:
                        if not self.should_stop:
                            print(f"   ⚙️  Applying filter: {filter_name}")
                            image = apply_func(image, **params)

        return image

    def process_image(self, image_path: Path,
                      size_params: dict,
                      filter_config: Dict[str, Any],
                      prefix: str = "") -> bool:
        """Process a single image"""
        print(f"\n🖼️ Processing: {image_path.name}")
        start_time = time.time()

        try:
            with self.lock:
                if self.should_stop:
                    print(f"⚠️  Processing stopped: {image_path.name}")
                    return False

            # Read image
            print(f"   📖 Reading image...")
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"   ❌ FAILED to load image: {image_path.name}")
                return False

            print(f"   ✅ Loaded: {image.shape[1]}x{image.shape[0]} pixels")

            # Calculate new size
            h, w = image.shape[:2]
            new_size = self.calculate_new_size((w, h), **size_params)

            # Resize image
            print(f"   📐 Resizing image...")
            resized = cv2.resize(image, new_size, interpolation=cv2.INTER_LANCZOS4)

            # Apply filters
            processed = self.apply_filters(resized, filter_config)

            # Save processed image
            output_name = f"{prefix}{image_path.stem}{image_path.suffix}"
            output_path = self.output_folder / output_name

            print(f"   💾 Saving to: {output_path.absolute()}")

            # Handle different channel formats
            if len(processed.shape) == 2:  # Grayscale
                cv2.imwrite(str(output_path), processed)
            else:
                cv2.imwrite(str(output_path), processed)

            elapsed = time.time() - start_time
            print(f"   ✅ Completed in {elapsed:.2f} seconds!\n")
            return True

        except Exception as e:
            print(f"   ❌ ERROR processing {image_path}: {e}")
            return False

    def stop_processing(self):
        """Stop batch processing"""
        print("🛑 STOP button pressed - stopping processing...")
        with self.lock:
            self.should_stop = True

    def batch_resize(self, size_params: dict,
                     filter_config: Dict[str, Any],
                     progress_callback: Optional[Callable] = None) -> Tuple[int, int, List[str]]:
        """
        Process images in batch
        Returns: (success_count, total_count, error_files)
        """
        print(f"\n{'=' * 50}")
        print(f"🚀 STARTING BATCH PROCESSING")
        print(f"📊 Total images: {len(self.image_files)}")
        print(f"⚙️  Filters enabled: {list(filter_config.keys())}")
        print(f"📏 Size params: {size_params}")
        print(f"{'=' * 50}\n")

        valid_files, invalid_files = self.validate_images()

        if not valid_files:
            print("❌ No valid images found!")
            return 0, 0, [f.name for f in invalid_files]

        success_count = 0
        total = len(valid_files)
        error_files = []

        for idx, image_path in enumerate(valid_files):
            if self.process_image(image_path, size_params, filter_config):
                success_count += 1
            else:
                error_files.append(image_path.name)

            if progress_callback:
                progress_callback(idx + 1, total, image_path.name)

        error_files.extend([f.name for f in invalid_files])

        print(f"\n{'=' * 50}")
        print(f"🏁 BATCH PROCESSING COMPLETE")
        print(f"✅ Success: {success_count}/{total}")
        print(f"❌ Failed: {len(error_files)}")
        print(f"{'=' * 50}\n")

        return success_count, total, error_files