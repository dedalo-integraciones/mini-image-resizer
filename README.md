# Mini Image Resizer Application

This is a lightweight Windows application for batch image resizing and format conversion, primarily for WebP output optimized for web use.

## Features

### Core Functionality
- Select multiple images from file system
- Resize images with high-quality preservation
- Convert to WebP, JPEG, or PNG formats
- Batch processing for multiple images
- Real-time preview of selected images

### Image Processing
- Fixed-size resizing by width and height, with automatic aspect ratio when one dimension is 0
- Percentage resizing that scales width and height proportionally, preserving the original aspect ratio
- Signed percentage values: `100` keeps the original size, `150` scales to 150% (+50%), and `-150` scales to 50% (-50%)
- High-quality resampling using LANCZOS algorithm
- Configurable quality settings for web optimization
- Automatic filename generation with user-defined prefix

### User Interface
- Simple, clean, modern interface
- Real-time image preview
- Progress indicators for batch operations
- Interactive size configuration
- Save location selection

### File Management
- Preserve original files
- Save processed images to preferred location
- Display original/new size comparisons
- Show file size information

## Usage

### Prerequisites
- Windows 10 or later
- Python 3.11+
- PyQt6 (for GUI)
- Pillow (for image processing)

### Installation
1. Ensure Python is installed
2. Install required dependencies:
   ```
   pip install pillow PyQt6
   ```

### Running the Application
```bash
python main.py
```

### Configuration
The application allows customization through the GUI:
- **Image Selection**: Browse and select multiple image files
- **Size Control**: Switch between fixed dimensions (width/height in pixels; use 0 to calculate that dimension automatically) and percentage scaling. In percentage mode, `100` keeps the original size, `150` enlarges it by 50%, and `-150` reduces it by 50%, always preserving aspect ratio.
- **Prefix**: Add custom prefix to output filenames
- **Format**: Choose output format (webp, jpeg, png)
- **Location**: Specify save directory or use default

### Example Processing
1. Select multiple image files
2. Configure size and output format
3. Click "Process Images"
4. View results and file information

## Technical Details

### Image Quality
- Uses PIL's LANCZOS resampling for high-quality resizing
- WebP output with quality setting of 85 for optimal web performance
- Progressive JPEG for better web loading experience
- PNG preservation for lossless scenarios

### Performance Features
- Threaded processing for responsive UI
- Real-time preview updates
- Progress tracking for batch operations
- Efficient memory management

### Windows Integration
- Native file dialog integration
- Standard Windows UI components
- Proper window management and event handling

## License
This project is distributed under the [MIT License](LICENSE), which permits personal and commercial use, modification, and redistribution subject to its terms.

The visual assets in `assets/` are original works created by the project author and are included in this project under the MIT License.

## Dédalo Integraciones
[Visit Dédalo Integraciones](https://dedalointegraciones.vercel.app/)
