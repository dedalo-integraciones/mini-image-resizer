#!/usr/bin/env python3
# Batch image resizer script for command line use

import os
import sys
from pathlib import Path
from PIL import Image


def resize_image(input_path, output_path, target_width, target_height, prefix="", preferred_format="webp", quality=50):
    """Resize an image with high quality preservation"""
    with Image.open(input_path) as img:
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get original dimensions
        original_width, original_height = img.size
        
        # Validate input image is not zero-sized
        if original_width <= 0 or original_height <= 0:
            raise ValueError(f"Input image has invalid dimensions: {original_width}x{original_height}")
        
        # Calculate target dimensions
        # If both are 0, use original size
        if target_width == 0 and target_height == 0:
            target_width_final = original_width
            target_height_final = original_height
        # If width is 0, calculate from height
        elif target_width == 0:
            if target_height <= 0:
                raise ValueError("Height must be greater than 0 when width is 0")
            target_width_final = int(target_height * original_width / original_height)
            target_height_final = target_height
        # If height is 0, calculate from width
        elif target_height == 0:
            if target_width <= 0:
                raise ValueError("Width must be greater than 0 when height is 0")
            target_height_final = int(target_width * original_height / original_width)
            target_width_final = target_width
        # Both specified
        else:
            if target_width <= 0 or target_height <= 0:
                raise ValueError("Width and height must be greater than 0")
            target_width_final = target_width
            target_height_final = target_height
        
        # Validate target dimensions are positive
        if target_width_final <= 0 or target_height_final <= 0:
            raise ValueError(f"Calculated target dimensions are invalid: {target_width_final}x{target_height_final}")
        
        # Resize using high-quality LANCZOS
        resized_img = img.resize((target_width_final, target_height_final), Image.Resampling.LANCZOS)
        
        # Generate output filename with prefix
        input_filename = Path(input_path).stem
        output_filename = f"{prefix}{input_filename}.{preferred_format}"
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        final_output_path = os.path.join(output_dir if output_dir else '.', output_filename)
        
        # Save with quality settings optimized for web
        save_kwargs = {}
        
        if preferred_format == 'webp':
            # WebP uses quality parameter (0-100, 50 is balanced)
            save_kwargs['quality'] = max(0, min(100, quality))
            save_kwargs['format'] = 'WEBP'
            resized_img.save(final_output_path, **save_kwargs)
        elif preferred_format == 'jpeg':
            save_kwargs['quality'] = max(0, min(100, quality))
            save_kwargs['format'] = 'JPEG'
            save_kwargs['optimize'] = True
            resized_img.save(final_output_path, **save_kwargs)
        elif preferred_format == 'png':
            save_kwargs['format'] = 'PNG'
            resized_img.save(final_output_path, **save_kwargs)
        else:
            save_kwargs['quality'] = quality if 0 < quality <= 100 else 85
            resized_img.save(final_output_path, **save_kwargs)
        
        # Verify output file was created successfully and is not empty
        if not os.path.exists(final_output_path):
            raise RuntimeError("Output file was not created")
        
        output_file_size = os.path.getsize(final_output_path)
        if output_file_size == 0:
            raise RuntimeError("Output file is empty")
        
        return {
            'input_path': input_path,
            'output_path': final_output_path,
            'original_size': (original_width, original_height),
            'new_size': (target_width_final, target_height_final),
            'file_size': output_file_size,
            'output_filename': output_filename,
            'quality_used': quality
        }


def main():
    print("Mini Image Resizer Batch Processor")
    print("=" * 40)
    
    # Simple command line interface
    if len(sys.argv) < 2:
        print("Usage: python batch_resize.py <input_directory> [output_directory] [width] [height] [prefix] [format] [quality]")
        print("  input_directory: Directory containing images to process")
        print("  output_directory: Output directory (default: same as input)")
        print("  width: Target width in pixels (0 for original)")
        print("  height: Target height in pixels (0 for original)")
        print("  prefix: Prefix for output filenames")
        print("  format: Output format (webp, jpeg, png) - default: webp")
        print("  quality: Compression level 0-100, 50 is balanced (default: 50)")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else input_dir
    target_width = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    target_height = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    prefix = sys.argv[5] if len(sys.argv) > 5 else ""
    output_format = sys.argv[6].lower() if len(sys.argv) > 6 else "webp"
    quality = int(sys.argv[7]) if len(sys.argv) > 7 else 50
    
    # Validate quality
    if not 0 <= quality <= 100:
        print(f"Error: Quality must be between 0 and 100. Got: {quality}")
        sys.exit(1)
    
    # Validate target size is not 0,0
    if target_width == 0 and target_height == 0:
        print("Error: Target size cannot be 0x0. Please specify at least one dimension > 0, or use 0 to keep original size.")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Supported image formats
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
    
    # Process images
    processed_count = 0
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_formats):
            input_path = os.path.join(input_dir, filename)
            try:
                result = resize_image(input_path, output_dir, target_width, target_height, prefix, output_format, quality)
                print(f"Processed: {filename}")
                print(f"  Output: {result['output_filename']}")
                print(f"  Original: {result['original_size'][0]}x{result['original_size'][1]}")
                print(f"  New: {result['new_size'][0]}x{result['new_size'][1]}")
                print(f"  Compression Level: {result['quality_used']}")
                print(f"  File size: {result['file_size'] / 1024:.1f} KB")
                print()
                processed_count += 1
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nBatch processing complete. Processed {processed_count} images.")


if __name__ == "__main__":
    main()