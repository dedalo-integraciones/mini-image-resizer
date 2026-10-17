import sys
import os
import time
import threading
import platform
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from batch_resize import calculate_target_dimensions


DARK_COLORS = {
    'bg_primary': '#0F0B1A',
    'bg_panel': '#1A1428',
    'bg_card': '#241B3A',
    'border': '#3A2F5A',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B8AED4',
    'text_muted': '#6E6488',
    'accent': '#6933CA',
    'accent_hover': '#7B46E0',
    'accent_active': '#4C29B6',
    'success': '#4ADE80',
    'warning': '#FBBF24',
    'error': '#F87171',
}

LIGHT_COLORS = {
    'bg_primary': '#F5F5F7',
    'bg_panel': '#FFFFFF',
    'bg_card': '#EDEDED',
    'border': '#D1D1D6',
    'text_primary': '#1D1D1F',
    'text_secondary': '#6E6E73',
    'text_muted': '#86868B',
    'accent': '#6933CA',
    'accent_hover': '#7B46E0',
    'accent_active': '#4C29B6',
    'success': '#268A3E',
    'warning': '#B45309',
    'error': '#D93025',
}


def get_system_theme():
    """Detect Windows light/dark mode via registry."""
    try:
        if platform.system() == 'Windows':
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            )
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            winreg.CloseKey(key)
            return 'light' if value == 1 else 'dark'
    except Exception:
        pass
    return 'dark'


COLORS = DARK_COLORS if get_system_theme() == 'dark' else LIGHT_COLORS


def resource_path(relative_path):
    """Ruta absoluta de recursos, compatible con desarrollo y PyInstaller one-file."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class ImageResizeWorker(threading.Thread):
    """Worker thread for processing multiple images"""
    
    def __init__(self, file_paths, output_path, target_width, target_height, prefix="", preferred_format="webp", quality=50, callback=None, size_mode="fixed", percentage=100):
        super().__init__()
        self.file_paths = file_paths
        self.output_path = output_path
        self.target_width = target_width
        self.target_height = target_height
        self.size_mode = size_mode
        self.percentage = percentage
        self.prefix = prefix
        self.preferred_format = preferred_format
        self.quality = quality
        self.callback = callback
        self.results = []
        self.errors = []
        
    def run(self):
        total = len(self.file_paths)
        start_time = time.time()
        
        for i, file_path in enumerate(self.file_paths):
            self.file_index = i + 1
            try:
                result = self.process_image(file_path)
                self.results.append(result)
            except Exception as e:
                self.errors.append(f"{Path(file_path).name}: {str(e)}")
                result = None
            
            # Update progress with file-level details
            progress = int(((i + 1) / total) * 100)
            elapsed = time.time() - start_time
            if self.callback:
                self.callback(progress, result, i + 1, total, elapsed)
    
    def process_image(self, file_path):
        """Process a single image with high quality preservation"""
        with Image.open(file_path) as img:
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            original_width, original_height = img.size
            
            # Validate input image is not zero-sized
            if original_width <= 0 or original_height <= 0:
                raise ValueError(f"Input image has invalid dimensions: {original_width}x{original_height}")
            
            target_width, target_height = calculate_target_dimensions(
                original_width, original_height, self.target_width, self.target_height,
                self.size_mode, self.percentage
            )
            
            # Resize using high-quality LANCZOS resampling
            resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Generate output filename with prefix
            input_filename = Path(file_path).stem
            output_filename = f"{self.prefix}{input_filename}.{self.preferred_format}"
            output_filepath = os.path.join(self.output_path, output_filename)
            
            # Save with quality settings optimized for web
            save_kwargs = {}
            
            if self.preferred_format == 'webp':
                # WebP uses quality parameter (0-100, 50 is balanced as requested)
                save_kwargs['quality'] = max(0, min(100, self.quality))
                save_kwargs['format'] = 'WEBP'
                resized_img.save(output_filepath, **save_kwargs)
            elif self.preferred_format == 'jpeg':
                # JPEG uses quality parameter (0-100, 85 is good for web)
                save_kwargs['quality'] = max(0, min(100, self.quality))
                save_kwargs['format'] = 'JPEG'
                resized_img.save(output_filepath, **save_kwargs)
            elif self.preferred_format == 'png':
                # PNG doesn't use quality parameter (lossless)
                save_kwargs['format'] = 'PNG'
                resized_img.save(output_filepath, **save_kwargs)
            else:
                save_kwargs['quality'] = max(0, min(100, self.quality))
                resized_img.save(output_filepath, **save_kwargs)
            
            # Verify output file was created successfully and has valid dimensions
            if not os.path.exists(output_filepath):
                raise RuntimeError("Output file was not created")
            
            output_file_size = os.path.getsize(output_filepath)
            if output_file_size == 0:
                raise RuntimeError("Output file is empty")
            
            return {
                'input_path': file_path,
                'output_path': output_filepath,
                'original_size': (original_width, original_height),
                'new_size': (target_width, target_height),
                'file_size': output_file_size,
                'output_filename': output_filename,
                'quality_used': self.quality if self.preferred_format in ['webp', 'jpeg'] else None
            }


class ImageResizerApp:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Image Resizer")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg=COLORS['bg_primary'])

        icon_path = resource_path('assets/icon.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(default=icon_path)
            except Exception:
                pass
            try:
                photo = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, photo)
            except Exception:
                pass

        self.images = []
        self.output_path = None
        self.current_preview_path = None

        self.setup_ui()
        
    def _style(self, widget, bg=None, fg=None, font=None):
        """Apply theme colors to a widget."""
        config = {}
        if bg: config['background'] = bg
        if fg: config['foreground'] = fg
        if font: config['font'] = font
        if config: widget.configure(**config)
        return widget
        
    def setup_ui(self):
        """Setup the user interface"""
        # Left frame - Image selection and list
        left_frame = self.create_left_panel()
        
        # Right frame - Settings and processing
        self.right_frame = self.create_right_panel()  # Store as instance variable
        
        # Pack frames
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        self.right_frame.pack(side='right', fill='y', padx=10, pady=10)
        
    def create_left_panel(self):
        """Create left panel with image selection and preview"""
        frame = tk.Frame(self.root, bg=COLORS['bg_primary'], highlightbackground=COLORS['border'], highlightthickness=1)
        
        # Title with logo
        title_frame = tk.Frame(frame, bg=COLORS['bg_primary'])
        title_frame.pack(pady=(0, 5))
        
        # Load and display logo
        try:
            logo_path = resource_path('assets/Isotipo.png')
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img.thumbnail((32, 32), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(title_frame, image=self.logo_photo, bg=COLORS['bg_primary'])
                logo_label.pack(side='left', padx=(0, 10))
        except Exception:
            pass
        
        # Title text
        title = tk.Label(title_frame, text="Mini Image Resizer", font=('Segoe UI', 18, 'bold'), bg=COLORS['bg_primary'], fg=COLORS['text_primary'])
        title.pack(side='left', pady=(0, 5))
        
        # Powered by text
        powered_label = tk.Label(frame, text="powered by Dédalo", font=('Segoe UI', 8), bg=COLORS['bg_primary'], fg=COLORS['text_muted'])
        powered_label.pack(pady=(0, 10))
        
        subtitle = tk.Label(frame, text="Batch image resizing with WebP optimization", font=('Segoe UI', 10), bg=COLORS['bg_primary'], fg=COLORS['text_secondary'])
        subtitle.pack(pady=(0, 10))
        
        # Clear session images button
        clear_btn = tk.Button(frame, text="Clear Session", command=self.clear_images,
                               bg=COLORS['warning'], fg=COLORS['text_primary'], font=('Segoe UI', 9, 'bold'),
                               activebackground=COLORS['accent_hover'], activeforeground=COLORS['text_primary'],
                               relief='flat', padx=8, pady=4, cursor='hand2')
        clear_btn.pack(pady=(0, 10))
        
        # Select button
        select_btn = tk.Button(frame, text="Select Images", command=self.select_images, 
                               bg=COLORS['accent'], fg=COLORS['text_primary'], font=('Segoe UI', 10, 'bold'),
                               activebackground=COLORS['accent_hover'], activeforeground=COLORS['text_primary'],
                               relief='flat', padx=12, pady=6, cursor='hand2')
        select_btn.pack(pady=(0, 10))
        
        # Image list with scrollbar
        list_frame = tk.Frame(frame, bg=COLORS['bg_panel'])
        list_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, bg=COLORS['bg_panel'], troughcolor=COLORS['bg_panel'], activebackground=COLORS['accent'])
        scrollbar.pack(side='right', fill='y')
        
        self.image_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                         font=('Segoe UI', 10), height=15,
                                         bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                                         selectbackground=COLORS['accent'], selectforeground=COLORS['text_primary'],
                                         activestyle='none', borderwidth=0, highlightthickness=0)
        self.image_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.image_listbox.yview)
        
        # Bind selection event
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_selected)
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(frame, bg=COLORS['bg_card'], highlightbackground=COLORS['border'], highlightthickness=1, height=300)
        self.preview_canvas.pack(fill='both', expand=True, pady=(10, 0))
        
        return frame
        
    def create_right_panel(self):
        """Create right panel with settings"""
        frame = tk.Frame(self.root, bg=COLORS['bg_primary'], highlightbackground=COLORS['border'], highlightthickness=1)
        
        # Size settings group
        size_frame = tk.LabelFrame(frame, text="Target Size", font=('Segoe UI', 10, 'bold'), bg=COLORS['bg_panel'], fg=COLORS['text_primary'], bd=1, relief='solid')
        size_frame.pack(fill='x', pady=(0, 10))
        
        mode_frame = tk.Frame(size_frame, bg=COLORS['bg_panel'])
        mode_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(mode_frame, text="Mode:", width=10, anchor='w', bg=COLORS['bg_panel'], fg=COLORS['text_secondary']).pack(side='left')
        self.size_mode_var = tk.StringVar(value='fixed')
        for label, value in (("Fixed size", "fixed"), ("Percentage", "percentage")):
            tk.Radiobutton(
                mode_frame, text=label, value=value, variable=self.size_mode_var,
                command=self.update_size_mode, indicatoron=False, width=12,
                bg=COLORS['bg_card'], fg=COLORS['text_primary'], selectcolor=COLORS['accent'],
                activebackground=COLORS['accent_hover'], activeforeground=COLORS['text_primary'],
                relief='flat', padx=4, pady=3
            ).pack(side='left', padx=(0, 5))

        self.fixed_size_frame = tk.Frame(size_frame, bg=COLORS['bg_panel'])
        self.fixed_size_frame.pack(fill='x')

        # Width input
        width_frame = tk.Frame(self.fixed_size_frame, bg=COLORS['bg_panel'])
        width_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(width_frame, text="Width:", width=10, bg=COLORS['bg_panel'], fg=COLORS['text_secondary']).pack(side='left')
        self.width_var = tk.IntVar(value=0)
        width_spin = tk.Spinbox(width_frame, from_=0, to=10000, textvariable=self.width_var, width=10,
                                bg=COLORS['bg_card'], fg=COLORS['text_primary'], buttonbackground=COLORS['bg_card'],
                                relief='flat', highlightthickness=1, highlightbackground=COLORS['border'])
        width_spin.pack(side='left', padx=(0, 10))
        tk.Label(width_frame, text="px", bg=COLORS['bg_panel'], fg=COLORS['text_muted']).pack(side='left')
        
        # Height input
        height_frame = tk.Frame(self.fixed_size_frame, bg=COLORS['bg_panel'])
        height_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(height_frame, text="Height:", width=10, bg=COLORS['bg_panel'], fg=COLORS['text_secondary']).pack(side='left')
        self.height_var = tk.IntVar(value=0)
        height_spin = tk.Spinbox(height_frame, from_=0, to=10000, textvariable=self.height_var, width=10,
                                 bg=COLORS['bg_card'], fg=COLORS['text_primary'], buttonbackground=COLORS['bg_card'],
                                 relief='flat', highlightthickness=1, highlightbackground=COLORS['border'])
        height_spin.pack(side='left', padx=(0, 10))
        tk.Label(height_frame, text="px", bg=COLORS['bg_panel'], fg=COLORS['text_muted']).pack(side='left')

        self.percentage_frame = tk.Frame(size_frame, bg=COLORS['bg_panel'])
        tk.Label(
            self.percentage_frame, text="Scale:", width=10, anchor='w',
            bg=COLORS['bg_panel'], fg=COLORS['text_secondary']
        ).pack(side='left', padx=(5, 0), pady=5)
        self.percentage_var = tk.IntVar(value=100)
        tk.Spinbox(
            self.percentage_frame, from_=-199, to=10000, textvariable=self.percentage_var, width=10,
            bg=COLORS['bg_card'], fg=COLORS['text_primary'], buttonbackground=COLORS['bg_card'],
            relief='flat', highlightthickness=1, highlightbackground=COLORS['border']
        ).pack(side='left', padx=(0, 8), pady=5)
        tk.Label(
            self.percentage_frame, text="%  (100 = original, 150 = +50%, -150 = -50%)",
            bg=COLORS['bg_panel'], fg=COLORS['text_muted']
        ).pack(side='left', pady=5)
        
        # Prefix input
        prefix_frame = tk.Frame(size_frame, bg=COLORS['bg_panel'])
        prefix_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(prefix_frame, text="Prefix:", width=10, bg=COLORS['bg_panel'], fg=COLORS['text_secondary']).pack(side='left')
        self.prefix_var = tk.StringVar()
        prefix_entry = tk.Entry(prefix_frame, textvariable=self.prefix_var, bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                                relief='flat', highlightthickness=1, highlightbackground=COLORS['border'],
                                insertbackground=COLORS['text_primary'])
        prefix_entry.pack(side='left', fill='x', expand=True)
        self.prefix_entry = prefix_entry
        
        # Format selection
        format_frame = tk.Frame(size_frame, bg=COLORS['bg_panel'])
        format_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(format_frame, text="Format:", width=10, bg=COLORS['bg_panel'], fg=COLORS['text_secondary']).pack(side='left')
        self.format_var = tk.StringVar(value='webp')
        format_combo = tk.OptionMenu(format_frame, self.format_var, 'webp', 'jpeg', 'png')
        format_combo.configure(bg=COLORS['bg_card'], fg=COLORS['text_primary'], relief='flat',
                               highlightthickness=1, highlightbackground=COLORS['border'])
        format_combo.pack(side='left', fill='x', expand=True)
        
        # Quality slider (only visible for WebP and JPEG)
        quality_frame = tk.Frame(size_frame, bg=COLORS['bg_panel'])
        quality_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(quality_frame, text="Quality:", width=10, bg=COLORS['bg_panel'], fg=COLORS['text_secondary']).pack(side='left')
        self.quality_var = tk.IntVar(value=50)  # Default 50 (balanced)
        quality_scale = tk.Scale(quality_frame, from_=0, to=100, orient='horizontal', 
                                 variable=self.quality_var, length=150, bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                                 troughcolor=COLORS['bg_card'], activebackground=COLORS['accent'])
        quality_scale.pack(side='left', padx=(0, 10))
        tk.Label(quality_frame, text="(0-100, 50=balanced)", bg=COLORS['bg_panel'], fg=COLORS['text_muted']).pack(side='left')
        
        # Initially hide quality slider for PNG (it doesn't use quality)
        def on_format_change(*args):
            if self.format_var.get() == 'png':
                quality_frame.pack_forget()
            else:
                quality_frame.pack(fill='x', padx=5, pady=5)
        
        self.format_var.trace('w', on_format_change)
        # Call once to set initial state
        on_format_change()
        
        # Save location group
        location_frame = tk.LabelFrame(frame, text="Save Location", font=('Segoe UI', 10, 'bold'), bg=COLORS['bg_panel'], fg=COLORS['text_primary'], bd=1, relief='solid')
        location_frame.pack(fill='x', pady=(0, 10))
        
        self.location_var = tk.StringVar(value="Will use source folder")
        location_label = tk.Label(location_frame, textvariable=self.location_var, bg=COLORS['bg_panel'], fg=COLORS['text_secondary'])
        location_label.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        
        browse_btn = tk.Button(location_frame, text="Browse...", command=self.browse_location,
                               bg=COLORS['accent'], fg=COLORS['text_primary'], font=('Segoe UI', 9, 'bold'),
                               activebackground=COLORS['accent_hover'], activeforeground=COLORS['text_primary'],
                               relief='flat', padx=10, pady=4, cursor='hand2')
        browse_btn.pack(side='right', padx=5, pady=5)
        
        # Image info group
        info_frame = tk.LabelFrame(frame, text="Image Information", font=('Segoe UI', 10, 'bold'), bg=COLORS['bg_panel'], fg=COLORS['text_primary'], bd=1, relief='solid')
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.original_info = tk.Label(info_frame, text="Original: -", bg=COLORS['bg_panel'], fg=COLORS['text_secondary'])
        self.original_info.pack(anchor='w', padx=5, pady=2)
        
        self.new_info = tk.Label(info_frame, text="New: -", bg=COLORS['bg_panel'], fg=COLORS['text_secondary'])
        self.new_info.pack(anchor='w', padx=5, pady=2)
        
        self.filesize_info = tk.Label(info_frame, text="File Size: -", bg=COLORS['bg_panel'], fg=COLORS['text_secondary'])
        self.filesize_info.pack(anchor='w', padx=5, pady=2)
        
        # Progress bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100, style='Horizontal.TProgressbar')
        self.progress_bar.pack(fill='x', padx=5, pady=(0, 10))
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Horizontal.TProgressbar', background=COLORS['accent'], troughcolor=COLORS['bg_panel'], bordercolor=COLORS['border'], lightcolor=COLORS['accent'], darkcolor=COLORS['accent'])
        
        # Process button
        self.process_btn = tk.Button(frame, text="Process Images", command=self.process_images,
                                     bg=COLORS['accent'], fg=COLORS['text_primary'], font=('Segoe UI', 12, 'bold'),
                                     activebackground=COLORS['accent_hover'], activeforeground=COLORS['text_primary'],
                                     relief='flat', padx=10, pady=8, cursor='hand2')
        self.process_btn.pack(fill='x', padx=5, pady=(0, 5))
        self.process_btn.config(state='disabled')
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(frame, textvariable=self.status_var, bg=COLORS['bg_primary'], fg=COLORS['text_secondary'])
        self.status_label.pack(anchor='w', padx=5, pady=(10, 0))
        
        return frame

    def update_size_mode(self):
        if self.size_mode_var.get() == 'percentage':
            self.fixed_size_frame.pack_forget()
            self.percentage_frame.pack(fill='x', before=self.prefix_entry.master)
        else:
            self.percentage_frame.pack_forget()
            self.fixed_size_frame.pack(fill='x', before=self.prefix_entry.master)
        if self.current_preview_path:
            self.update_image_info(self.current_preview_path)
        
    def select_images(self):
        """Open file dialog to select images"""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if files:
            for file_path in files:
                self.images.append(file_path)
                self.image_listbox.insert('end', Path(file_path).name)
            
            # Set default save location to source folder of first image
            if not self.output_path and files:
                self.output_path = str(Path(files[0]).parent)
                self.location_var.set(self.output_path)
            
            self.process_btn.config(state='normal')
            
    def browse_location(self):
        """Open directory dialog to select save location"""
        directory = filedialog.askdirectory(title="Select Save Location")
        if directory:
            self.output_path = directory
            self.location_var.set(directory)

    def clear_images(self):
        """Clear all images from the session and reset the UI."""
        if not self.images and (not hasattr(self, 'worker') or not self.worker or not self.worker.is_alive()):
            messagebox.showinfo("Session Empty", "There are no images in the current session to clear.")
            return

        if hasattr(self, 'worker') and self.worker and self.worker.is_alive():
            messagebox.showwarning(
                "Processing in Progress",
                "Image processing is currently running.\n"
                "Clear the session after processing finishes to avoid inconsistent state."
            )
            return

        if not messagebox.askyesno(
            "Clear Session Images",
            "This will remove all loaded and processed images from the session.\n"
            "Do you want to continue?"
        ):
            return

        self.images.clear()
        self.image_listbox.delete(0, 'end')
        self.output_path = None
        self.location_var.set("Will use source folder")
        self.current_preview_path = None
        self.preview_canvas.delete("all")
        self.original_info.config(text="Original: -")
        self.new_info.config(text="New: -")
        self.filesize_info.config(text="File Size: -")
        self.progress_var.set(0)
        self.process_btn.config(state='disabled')
        self.status_var.set("Ready")
        self.status_label.config(fg=COLORS['text_secondary'])
            
    def on_image_selected(self, event):
        """Handle image selection from list"""
        selection = self.image_listbox.curselection()
        if selection:
            index = selection[0]
            file_path = self.images[index]
            self.current_preview_path = file_path
            self.display_preview(file_path)
            self.update_image_info(file_path)
            
    def display_preview(self, image_path):
        """Display image preview in canvas"""
        try:
            # Load image
            img = Image.open(image_path)
            
            # Get canvas dimensions
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1:
                canvas_width = 400
            if canvas_height <= 1:
                canvas_height = 300
            
            # Calculate scale to fit canvas
            img_width, img_height = img.size
            scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize for display
            display_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(display_img)
            
            # Draw on canvas
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor='nw', image=self.tk_image)
            
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(200, 150, text=f"Error: {str(e)}", fill=COLORS['error'])
            
    def update_image_info(self, image_path):
        """Display image information"""
        try:
            with Image.open(image_path) as img:
                original_width, original_height = img.size
                self.original_info.config(text=f"Original: {original_width} x {original_height}")
                
                # Calculate new size using the same rules as the processing worker.
                target_width = self.width_var.get()
                target_height = self.height_var.get()
                new_width, new_height = calculate_target_dimensions(
                    original_width, original_height, target_width, target_height,
                    self.size_mode_var.get(), self.percentage_var.get()
                )
                
                self.new_info.config(text=f"New: {new_width} x {new_height}")
                
                # Get file size
                file_size = os.path.getsize(image_path)
                self.filesize_info.config(text=f"File Size: {file_size / 1024:.1f} KB")
                
        except Exception as e:
            self.original_info.config(text=f"Error: {str(e)}")
            self.new_info.config(text="New: -")
            self.filesize_info.config(text="File Size: -")
            
    def process_images(self):
        """Process selected images with batch processing"""
        if not self.images:
            messagebox.showwarning("Warning", "Please select images to process")
            return
            
        target_width = self.width_var.get()
        target_height = self.height_var.get()
        size_mode = self.size_mode_var.get()
        percentage = self.percentage_var.get()
        prefix = self.prefix_var.get().strip()
        output_format = self.format_var.get()
        quality = self.quality_var.get()
        
        # Validate target size is not 0,0
        if size_mode == 'fixed' and target_width == 0 and target_height == 0:
            messagebox.showerror("Invalid Size", "Target size cannot be 0 x 0. Please enter a width or height greater than 0.")
            return
        
        # Validate target dimensions are positive
        if size_mode == 'fixed' and (target_width < 0 or target_height < 0):
            messagebox.showerror("Invalid Size", "Target width and height must be greater than or equal to 0.")
            return

        if size_mode == 'percentage' and percentage <= -200:
            messagebox.showerror("Invalid Size", "Percentage must be greater than -200.")
            return
        
        # Check if prefix is empty - warn about overwriting existing files
        if not prefix:
            overwrite_reply = messagebox.askyesno(
                "Prefix Required",
                "The prefix field is empty.\n\n"
                "If you continue without a prefix, existing files may be overwritten.\n\n"
                "Do you want to continue anyway?"
            )
            
            if not overwrite_reply:
                self.prefix_entry.focus_set()
                return
        
        save_location = self.output_path
        if not save_location:
            save_location = str(Path(self.images[0]).parent)
        
        target_description = (
            f"{percentage}% scale" if size_mode == 'percentage'
            else f"{target_width if target_width else 'Auto'} x {target_height if target_height else 'Auto'} px"
        )

        # Confirm before processing
        reply = messagebox.askyesno(
            "Confirm Processing",
            f"Process {len(self.images)} image(s)?\n\n"
            f"Target Size: {target_description}\n"
            f"Format: {output_format.upper()}\n"
            f"Prefix: {prefix if prefix else 'None'}\n"
            f"Compression Level: {quality} (0-100, 50=balanced)\n"
            f"Save Location: {save_location}"
        )
        
        if reply:
            # Reset progress
            self.progress_var.set(0)
            self.status_var.set("Processing...")
            self.process_btn.config(state='disabled')
            
            # Create modern spinner for busy state
            self.spinner = tk.Label(self.right_frame, text="⏳ Processing...", font=('Segoe UI', 10, 'bold'), bg=COLORS['bg_primary'], fg=COLORS['accent'])
            self.spinner.pack(pady=5)
            
            # Create detailed progress label for per-file status
            self.processing_label = tk.Label(self.right_frame, text="", font=('Segoe UI', 9), bg=COLORS['bg_primary'], fg=COLORS['text_secondary'])
            self.processing_label.pack(pady=2)
            
            # Create time remaining label
            self.time_label = tk.Label(self.right_frame, text="", font=('Segoe UI', 8), bg=COLORS['bg_primary'], fg=COLORS['text_muted'])
            self.time_label.pack(pady=2)
            
            start_time = time.time()
            
            # Start worker thread
            def update_progress(progress, result, current_index, total, elapsed):
                self.progress_var.set(progress)
                current_file = Path(self.images[current_index - 1]).name if current_index > 0 else ""
                
                if result:
                    self.processing_label.config(text=f"Processing: {current_file}")
                    # Calculate estimated time remaining
                    if current_index > 0 and current_index < total:
                        avg_time_per_file = elapsed / current_index
                        remaining_files = total - current_index
                        estimated_remaining = avg_time_per_file * remaining_files
                        minutes, seconds = divmod(int(estimated_remaining), 60)
                        time_str = f"Est. remaining: {minutes}m {seconds}s"
                        self.time_label.config(text=time_str)
                
                if progress == 100:
                    self.status_var.set("Complete!")
                    self.status_label.config(fg=COLORS['success'])
                    self.process_btn.config(state='normal')
                    self.spinner.pack_forget()
                    self.processing_label.pack_forget()
                    self.time_label.pack_forget()
                    # Show summary for all processed images
                    summary = "Processing Complete!\n\n"
                    summary += f"Processed {len(self.worker.results)} image(s):\n\n"
                    
                    for r in self.worker.results:
                        summary += f"- {Path(r['input_path']).name}\n"
                        summary += f"  Output: {r['output_filename']}\n"
                        summary += f"  Original: {r['original_size'][0]}x{r['original_size'][1]}\n"
                        summary += f"  New: {r['new_size'][0]}x{r['new_size'][1]}\n"
                        summary += f"  File Size: {r['file_size'] / 1024:.1f} KB\n\n"
                    
                    messagebox.showinfo("Success", summary)
            
            self.worker = ImageResizeWorker(
                self.images,
                save_location,
                target_width,
                target_height,
                prefix,
                output_format,
                quality,
                callback=update_progress,
                size_mode=size_mode,
                percentage=percentage
            )
            self.worker.start()


def main():
    """Application entry point"""
    root = tk.Tk()
    app = ImageResizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()