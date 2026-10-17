# Simple test script to verify image processing functionality
import os
import tempfile
from pathlib import Path
from PIL import Image
from batch_resize import calculate_target_dimensions, resize_image

def test_image_creation():
    """Create a test image for processing"""
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple test image (100x100 red square)
        test_image_path = os.path.join(temp_dir, "test_image.png")
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image_path)
        
        # Test the resize function
        result = resize_image(
            test_image_path,
            temp_dir,
            target_width=50,
            target_height=50,
            prefix="test_",
            preferred_format="webp"
        )
        
        # Verify the result
        assert os.path.exists(result['output_path']), "Output file was not created"
        assert result['original_size'] == (100, 100), f"Original size mismatch: {result['original_size']}"
        assert result['new_size'] == (50, 50), f"New size mismatch: {result['new_size']}"
        assert result['file_size'] > 0, "Output file is empty"
        
        print("[OK] All tests passed!")
        print(f"[OK] Input: {result['input_path']}")
        print(f"[OK] Output: {result['output_path']}")
        print(f"[OK] Original size: {result['original_size'][0]}x{result['original_size'][1]}")
        print(f"[OK] New size: {result['new_size'][0]}x{result['new_size'][1]}")
        print(f"[OK] File size: {result['file_size']} bytes")

        # Signed percentage values preserve the original aspect ratio.
        assert calculate_target_dimensions(200, 100, size_mode="percentage", percentage=150) == (300, 150)
        assert calculate_target_dimensions(200, 100, size_mode="percentage", percentage=-150) == (100, 50)
        try:
            calculate_target_dimensions(200, 100, size_mode="percentage", percentage=-200)
        except ValueError:
            pass
        else:
            raise AssertionError("A percentage of -200 must be rejected")

        percentage_result = resize_image(
            test_image_path, temp_dir, target_width=0, target_height=0,
            prefix="percentage_", preferred_format="png", size_mode="percentage", percentage=150
        )
        assert percentage_result['new_size'] == (150, 150), f"Percentage resize mismatch: {percentage_result['new_size']}"

        landscape_path = os.path.join(temp_dir, "landscape.png")
        Image.new('RGB', (200, 100), color='blue').save(landscape_path)
        for percentage, expected_size in ((150, (300, 150)), (-150, (100, 50))):
            result = resize_image(
                landscape_path, temp_dir, target_width=0, target_height=0,
                prefix=f"landscape_{percentage}_", preferred_format="png",
                size_mode="percentage", percentage=percentage
            )
            assert result['new_size'] == expected_size, f"Unexpected dimensions for {percentage}%: {result['new_size']}"
        print("[OK] Signed percentage and aspect ratio tests passed")
        
        # Test with different formats
        formats_to_test = ['webp', 'jpeg', 'png']
        for fmt in formats_to_test:
            output_path = os.path.join(temp_dir, f"test_{fmt}.{fmt}")
            result = resize_image(
                test_image_path,
                temp_dir,
                target_width=75,
                target_height=75,
                prefix="format_",
                preferred_format=fmt
            )
            assert os.path.exists(result['output_path']), f"Output file for {fmt} was not created"
            print(f"[OK] Format test passed for: {fmt}")
        
        # Test with 0 dimensions (use original size)
        result = resize_image(
            test_image_path,
            temp_dir,
            target_width=0,
            target_height=0,
            prefix="original_",
            preferred_format="webp"
        )
        assert result['new_size'] == (100, 100), f"Original size not maintained: {result['new_size']}"
        print(f"[OK] Original size test passed")
        
        print("\n[OK] All tests completed successfully!")

if __name__ == "__main__":
    test_image_creation()
