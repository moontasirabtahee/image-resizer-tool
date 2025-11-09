import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from image_resizer import ImageResizer, FilterType
import threading


class ImageResizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Image Editor & Resizer")
        self.root.geometry("850x650")  # Slightly smaller default
        self.root.minsize(800, 600)
        self.root.resizable(True, True)

        print("🚀 Starting Advanced Image Editor & Resizer...")

        # Variables
        self.selected_files = []
        self.output_folder = tk.StringVar()
        self.selected_preset = tk.StringVar(value="Custom")
        self.custom_width = tk.StringVar()
        self.custom_height = tk.StringVar()
        self.percentage = tk.StringVar()

        # Filter variables
        self.filter_vars = {
            FilterType.GRAYSCALE.value: tk.BooleanVar(),
            FilterType.BLUR.value: tk.BooleanVar(),
            FilterType.SHARPEN.value: tk.BooleanVar(),
            FilterType.EDGE_DETECT.value: tk.BooleanVar(),
        }

        # Advanced filters
        self.brightness_var = tk.IntVar(value=0)
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.rotate_var = tk.IntVar(value=0)
        self.flip_var = tk.StringVar(value="none")

        # Processing state
        self.is_processing = False
        self.current_resizer = None

        # Preset options
        self.presets = {
            "Custom": {"type": "custom"},
            "800x600": {"type": "preset", "width": 800, "height": 600},
            "1024x768": {"type": "preset", "width": 1024, "height": 768},
            "1280x720": {"type": "preset", "width": 1280, "height": 720},
            "1920x1080": {"type": "preset", "width": 1920, "height": 1080},
            "3840x2160 (4K)": {"type": "preset", "width": 3840, "height": 2160},
            "50%": {"type": "percentage", "percentage": 50},
            "75%": {"type": "percentage", "percentage": 75},
            "25%": {"type": "percentage", "percentage": 25},
            "150%": {"type": "percentage", "percentage": 150},
            "Instagram (1080x1080)": {"type": "preset", "width": 1080, "height": 1080},
            "Facebook Cover (851x315)": {"type": "preset", "width": 851, "height": 315},
            "Twitter Header (1500x500)": {"type": "preset", "width": 1500, "height": 500},
        }

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface with scrollable canvas"""
        print("🎨 Setting up UI with scrollable canvas...")

        # ==== CREATE SCROLLABLE CANVAS ====
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Canvas for scrolling
        self.canvas = tk.Canvas(main_container)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside canvas
        main_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=main_frame, anchor=tk.NW, width=850)

        # Configure scrolling
        def on_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        main_frame.bind('<Configure>', on_configure)

        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", on_mousewheel)

        # ==== UI CONTENT (now inside scrollable frame) ====
        # Title
        title_label = ttk.Label(main_frame, text="🖼️ Advanced Image Editor & Resizer",
                                font=('Segoe UI', 20, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Image Selection Frame
        files_frame = ttk.LabelFrame(main_frame, text="📁 Image Selection", padding="10")
        files_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        files_frame.grid_columnconfigure(1, weight=1)

        # File list
        self.file_listbox = tk.Listbox(files_frame, height=6, width=65, selectmode=tk.EXTENDED)
        self.file_listbox.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        scrollbar_files = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar_files.grid(row=0, column=2, sticky=(tk.N, tk.S), pady=5)
        self.file_listbox.configure(yscrollcommand=scrollbar_files.set)

        # File buttons
        ttk.Button(files_frame, text="📁 Add Images", command=self.select_images).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(files_frame, text="🗑️ Remove Selected", command=self.remove_selected).grid(row=1, column=1, padx=5,
                                                                                              pady=5)

        # Output Settings Frame
        output_frame = ttk.LabelFrame(main_frame, text="💾 Output Settings", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        output_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(output_frame, textvariable=self.output_folder, width=45).grid(row=0, column=1, pady=5, padx=10)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).grid(row=0, column=2, pady=5)

        # Notebook Tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)

        # Resize Tab
        resize_frame = ttk.Frame(notebook, padding="15")
        notebook.add(resize_frame, text="📏 Resize")

        ttk.Label(resize_frame, text="Quick Presets:").grid(row=0, column=0, sticky=tk.W, pady=10)
        preset_combo = ttk.Combobox(resize_frame, textvariable=self.selected_preset,
                                    values=list(self.presets.keys()), state="readonly", width=30)
        preset_combo.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=10, padx=10)
        preset_combo.bind("<<ComboboxSelected>>", self.on_preset_change)

        ttk.Label(resize_frame, text="Width (px):").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.width_entry = ttk.Entry(resize_frame, textvariable=self.custom_width, width=18)
        self.width_entry.grid(row=1, column=1, sticky=tk.W, pady=8, padx=10)

        ttk.Label(resize_frame, text="Height (px):").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.height_entry = ttk.Entry(resize_frame, textvariable=self.custom_height, width=18)
        self.height_entry.grid(row=2, column=1, sticky=tk.W, pady=8, padx=10)

        ttk.Label(resize_frame, text="or Percentage:").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.percentage_entry = ttk.Entry(resize_frame, textvariable=self.percentage, width=18)
        self.percentage_entry.grid(row=3, column=1, sticky=tk.W, pady=8, padx=10)

        ttk.Label(resize_frame, text="💡 Tip: Leave one field empty to maintain aspect ratio",
                  font=('Segoe UI', 9, 'italic')).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=10)

        # Filters Tab
        filter_frame = ttk.Frame(notebook, padding="15")
        notebook.add(filter_frame, text="🎨 Filters")

        filter_checkboxes = [
            ("Convert to Grayscale", FilterType.GRAYSCALE),
            ("Apply Blur Effect", FilterType.BLUR),
            ("Sharpen Image", FilterType.SHARPEN),
            ("Edge Detection", FilterType.EDGE_DETECT),
        ]

        for idx, (text, filter_type) in enumerate(filter_checkboxes):
            ttk.Checkbutton(filter_frame, text=text,
                            variable=self.filter_vars[filter_type.value]).grid(row=idx, column=0, sticky=tk.W, pady=6,
                                                                               padx=10)

        # Brightness slider
        ttk.Label(filter_frame, text="Brightness:").grid(row=4, column=0, sticky=tk.W, pady=12, padx=10)
        brightness_frame = ttk.Frame(filter_frame)
        brightness_frame.grid(row=4, column=1, sticky=tk.W, pady=12)

        brightness_scale = ttk.Scale(brightness_frame, from_=-100, to=100,
                                     variable=self.brightness_var, orient=tk.HORIZONTAL, length=220)
        brightness_scale.pack(side=tk.LEFT)
        self.brightness_label = ttk.Label(brightness_frame, text="0", width=5)
        self.brightness_label.pack(side=tk.LEFT, padx=10)
        brightness_scale.config(command=lambda v: self.update_label(self.brightness_label, int(float(v)), ""))

        # Contrast slider
        ttk.Label(filter_frame, text="Contrast:").grid(row=5, column=0, sticky=tk.W, pady=12, padx=10)
        contrast_frame = ttk.Frame(filter_frame)
        contrast_frame.grid(row=5, column=1, sticky=tk.W, pady=12)

        contrast_scale = ttk.Scale(contrast_frame, from_=0.1, to=3.0,
                                   variable=self.contrast_var, orient=tk.HORIZONTAL, length=220)
        contrast_scale.pack(side=tk.LEFT)
        self.contrast_label = ttk.Label(contrast_frame, text="1.0", width=5)
        self.contrast_label.pack(side=tk.LEFT, padx=10)
        contrast_scale.config(command=lambda v: self.update_label(self.contrast_label, float(v), ".1f"))

        # Transform Tab
        transform_frame = ttk.Frame(notebook, padding="15")
        notebook.add(transform_frame, text="🔄 Transform")

        # Rotation
        ttk.Label(transform_frame, text="Rotation Angle:").grid(row=0, column=0, sticky=tk.W, pady=12, padx=10)
        rotation_frame = ttk.Frame(transform_frame)
        rotation_frame.grid(row=0, column=1, sticky=tk.W, pady=12)

        rotation_scale = ttk.Scale(rotation_frame, from_=0, to=360,
                                   variable=self.rotate_var, orient=tk.HORIZONTAL, length=220)
        rotation_scale.pack(side=tk.LEFT)
        self.rotation_label = ttk.Label(rotation_frame, text="0°", width=5)
        self.rotation_label.pack(side=tk.LEFT, padx=10)
        rotation_scale.config(command=lambda v: self.update_label(self.rotation_label, int(float(v)), "°"))

        # Flip
        ttk.Label(transform_frame, text="Flip:").grid(row=1, column=0, sticky=tk.W, pady=12, padx=10)
        flip_combo = ttk.Combobox(transform_frame, textvariable=self.flip_var,
                                  values=["none", "horizontal", "vertical", "both"],
                                  state="readonly", width=18)
        flip_combo.grid(row=1, column=1, sticky=tk.W, pady=12, padx=10)

        # Progress Bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=700)
        self.progress_bar.pack(fill=tk.X, padx=5)

        # Status Label
        self.status_label = ttk.Label(main_frame, text="Ready - No images selected",
                                      font=('Segoe UI', 10, 'italic'))
        self.status_label.grid(row=5, column=0, columnspan=3, pady=(0, 10))

        # ==== SMALLER SUBMIT BUTTON ====
        submit_frame = ttk.Frame(main_frame)
        submit_frame.grid(row=6, column=0, columnspan=3, pady=15)

        self.submit_button = tk.Button(
            submit_frame,
            text="👉 SUBMIT & PROCESS IMAGES 👈",
            command=self.start_processing,
            bg="#4CAF50",
            fg="white",
            font=('Segoe UI', 14, 'bold'),  # **REDUCED from 18 to 14**
            activebackground="#45a049",
            relief=tk.RAISED,
            bd=3,
            padx=25,  # **REDUCED from 40**
            pady=12  # **REDUCED from 20**
        )
        self.submit_button.pack(pady=5)

        ttk.Label(submit_frame, text="✅ Click above to resize and save images",
                  font=('Segoe UI', 10, 'bold'), foreground='#4CAF50').pack()

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=7, column=0, columnspan=3, pady=10)

        ttk.Button(control_frame, text="Clear All", command=self.clear_all).grid(row=0, column=0, padx=8)
        ttk.Button(control_frame, text="Exit", command=self.root.quit).grid(row=0, column=1, padx=8)

        # Styles
        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('Segoe UI', 11, 'bold'))

        # Initialize
        self.on_preset_change()
        print("✅ UI setup complete - Scrollable canvas ready!")

    def update_label(self, label, value, fmt):
        if fmt == "":
            label.config(text=f"{value}")
        elif fmt == "°":
            label.config(text=f"{value}°")
        else:
            label.config(text=f"{value:{fmt}}")

    def select_images(self):
        print("\n📁 Opening file selection...")
        filetypes = (('Image files', '*.jpg *.jpeg *.png *.bmp *.tiff *.webp'), ('All files', '*.*'))
        files = filedialog.askopenfilenames(title="Select Images", filetypes=filetypes)
        if files:
            print(f"✅ Selected {len(files)} file(s)")
            self.selected_files.extend(files)
            self.update_file_list()
        else:
            print("❌ No files selected")

    def update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.file_listbox.insert(tk.END, Path(file).name)
        count = len(self.selected_files)
        self.status_label.config(text=f"Ready - {count} image(s) selected")
        print(f"✅ Displaying {count} image(s)")

    def remove_selected(self):
        selected_indices = list(self.file_listbox.curselection())
        if not selected_indices:
            print("⚠️  No files selected to remove")
            return
        selected_indices.reverse()
        for idx in selected_indices:
            del self.selected_files[idx]
            self.file_listbox.delete(idx)
        count = len(self.selected_files)
        self.status_label.config(text=f"Ready - {count} image(s) selected")
        print(f"🗑️ Removed {len(selected_indices)} file(s)")

    def clear_selection(self):
        print("🔄 Clearing all files...")
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
        self.status_label.config(text="Ready - No images selected")
        print("✅ All files cleared")

    def browse_output(self):
        print("\n📁 Opening output folder...")
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            print(f"✅ Output folder: {folder}")
        else:
            print("❌ No output folder selected")

    def on_preset_change(self, event=None):
        preset_name = self.selected_preset.get()
        preset = self.presets[preset_name]
        print(f"⚙️ Preset: {preset_name}")
        self.custom_width.set("")
        self.custom_height.set("")
        self.percentage.set("")
        self.width_entry.config(state='disabled')
        self.height_entry.config(state='disabled')
        self.percentage_entry.config(state='disabled')

        if preset.get("type") == "custom":
            self.width_entry.config(state='normal')
            self.height_entry.config(state='normal')
            self.percentage_entry.config(state='normal')
        elif preset.get("type") == "percentage":
            self.percentage_entry.config(state='normal')
            self.percentage.set(preset.get("percentage", ""))
        elif preset.get("type") == "preset":
            self.width_entry.config(state='normal')
            self.height_entry.config(state='normal')
            self.custom_width.set(preset.get("width", ""))
            self.custom_height.set(preset.get("height", ""))

    def clear_all(self):
        print("\n🔄 Clearing ALL fields...")
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
        self.output_folder.set("")
        self.selected_preset.set("Custom")
        self.custom_width.set("")
        self.custom_height.set("")
        self.percentage.set("")
        for var in self.filter_vars.values():
            var.set(False)
        self.brightness_var.set(0)
        self.contrast_var.set(1.0)
        self.rotate_var.set(0)
        self.flip_var.set("none")
        self.progress_var.set(0)
        self.status_label.config(text="Ready - No images selected")
        print("✅ ALL fields cleared")

    def get_filter_config(self) -> dict:
        config = {}
        for filter_name, var in self.filter_vars.items():
            if var.get():
                config[filter_name] = {'enabled': True}
        if self.brightness_var.get() != 0:
            config[FilterType.BRIGHTNESS.value] = {'enabled': True, 'value': self.brightness_var.get()}
        if self.contrast_var.get() != 1.0:
            config[FilterType.CONTRAST.value] = {'enabled': True, 'value': self.contrast_var.get()}
        if self.rotate_var.get() != 0:
            config[FilterType.ROTATE.value] = {'enabled': True, 'angle': self.rotate_var.get()}
        if self.flip_var.get() != "none":
            flip_map = {"none": -1, "horizontal": 1, "vertical": 0, "both": -1}
            config[FilterType.FLIP.value] = {'enabled': True, 'direction': flip_map[self.flip_var.get()]}
        print(f"⚙️ Filter config: {config}")
        return config

    def start_processing(self):
        print("\n" + "=" * 50)
        print("🎯 SUBMIT BUTTON CLICKED!")
        print("=" * 50)

        if not self.selected_files:
            print("❌ ERROR: No images selected!")
            messagebox.showerror("Error", "Please select at least one image")
            return

        if not self.output_folder.get():
            print("❌ ERROR: No output folder!")
            messagebox.showerror("Error", "Please select an output folder")
            return

        size_params = {}
        try:
            if self.custom_width.get():
                size_params['width'] = int(self.custom_width.get())
            if self.custom_height.get():
                size_params['height'] = int(self.custom_height.get())
            if self.percentage.get():
                size_params['percentage'] = float(self.percentage.get())
        except ValueError:
            print("❌ ERROR: Invalid numbers!")
            messagebox.showerror("Error", "Please enter valid numeric values")
            return

        if not size_params:
            print("❌ ERROR: No size parameters!")
            messagebox.showerror("Error", "Please specify size parameters")
            return

        filter_config = self.get_filter_config()
        print(f"✅ Settings: {len(self.selected_files)} images, {size_params}")

        # Start thread
        self.is_processing = True
        self.set_ui_state(False)
        self.submit_button.config(text="⏳ PROCESSING...", bg="#FFA500", state='disabled')

        print("🔄 Starting thread...")
        process_thread = threading.Thread(target=self.run_processing, args=(size_params, filter_config), daemon=True)
        process_thread.start()
        self.check_thread_completion(process_thread)

    def run_processing(self, size_params, filter_config):
        print("⚙️ Background thread started")
        try:
            self.current_resizer = ImageResizer(self.selected_files, self.output_folder.get())
            success, total, errors = self.current_resizer.batch_resize(size_params, filter_config, self.update_progress)
            print(f"✅ Done: {success}/{total}")
            self.root.after(0, self.show_results, success, total, errors)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.root.after(0, messagebox.showerror, "Error", f"Failed:\n{e}")
            self.root.after(0, self.finish_processing)

    def show_results(self, success, total, errors):
        if errors:
            error_msg = f"Failed: {len(errors)} files:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more"
            messagebox.showwarning("Complete with Errors", f"✅ {success}/{total} images.\n\n{error_msg}")
        else:
            messagebox.showinfo("Success!",
                                f"✅ All {success} images processed!\n\nSaved to:\n{self.output_folder.get()}")
        self.finish_processing()

    def check_thread_completion(self, thread):
        if thread.is_alive():
            self.root.after(100, self.check_thread_completion, thread)
        else:
            print("⚙️ Thread finished")
            self.finish_processing()

    def finish_processing(self):
        print("🧹 Finishing...")
        self.is_processing = False
        self.submit_button.config(text="👉 SUBMIT & PROCESS IMAGES 👈", bg="#4CAF50", state='normal')
        self.set_ui_state(True)
        self.status_label.config(text="Ready - Processing complete")
        self.progress_var.set(0)
        if self.current_resizer:
            self.current_resizer = None
        print("✅ Ready for next batch")

    def update_progress(self, current, total, filename=""):
        progress = (current / total) * 100
        self.root.after(0, self._update_ui_progress, progress, current, total, filename)

    def _update_ui_progress(self, progress, current, total, filename):
        self.progress_var.set(progress)
        self.status_label.config(text=f"Processing... {current}/{total} - {filename}")

    def set_ui_state(self, enabled):
        state = 'normal' if enabled else 'disabled'
        print(f"⚙️ UI state: {'enabled' if enabled else 'disabled'}")

        def set_recursive(widget):
            try:
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Button, tk.Button)):
                        if child.cget('text') != 'Exit':
                            child.config(state=state)
                    elif isinstance(child, (ttk.Entry, ttk.Combobox, ttk.Checkbutton, ttk.Scale)):
                        child.config(state=state)
                    set_recursive(child)
            except:
                pass

        set_recursive(self.root)


def main():
    print("\n" + "=" * 50)
    print("🚀 LAUNCHING Advanced Image Editor & Resizer")
    print("=" * 50 + "\n")

    root = tk.Tk()
    app = ImageResizerApp(root)
    root.mainloop()

    print("\n👋 Application closed!")
    print("=" * 50)


if __name__ == "__main__":
    main()