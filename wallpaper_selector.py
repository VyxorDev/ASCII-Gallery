import os
import sys
import platform
import subprocess
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox

class ASCIIWallpaperSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("ASCII Gallery - Wallpaper Selector")
        self.root.geometry("820x520")
        self.root.configure(bg="#121212")
        self.root.minsize(650, 420)

        # Locate the gallery folder relative to this script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.gallery_dir = os.path.join(base_dir, "gallery")
        
        self.wallpapers = self._find_wallpapers()
        self.current_preview = None

        self._setup_styles()
        self._build_ui()

        if self.wallpapers:
            self.listbox.selection_set(0)
            self._on_select(None)
        else:
            messagebox.showwarning(
                "No Wallpapers Found",
                f"Could not find any PNG images inside:\n{self.gallery_dir}\n\nMake sure this script is in the root of your ascii-gallery folder."
            )

    def _find_wallpapers(self):
        """Recursively finds all .png files in the gallery directory."""
        found = {}
        if not os.path.exists(self.gallery_dir):
            return found

        for root_dir, _, files in os.walk(self.gallery_dir):
            for file in sorted(files):
                if file.lower().endswith(".png"):
                    # Create a clean display name (e.g., "CallOfDutyGhost.png" -> "CallOfDutyGhost")
                    display_name = os.path.splitext(file)[0]
                    full_path = os.path.join(root_dir, file)
                    found[display_name] = full_path
        return found

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#121212")
        style.configure("TLabel", background="#121212", foreground="#e0e0e0", font=("Consolas", 10))
        style.configure("Header.TLabel", font=("Consolas", 13, "bold"), foreground="#00ff88")
        style.configure(
            "Apply.TButton",
            font=("Consolas", 11, "bold"),
            background="#00ff88",
            foreground="#121212",
            padding=(12, 8)
        )
        style.map("Apply.TButton", background=[("active", "#00cc6a")])

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left Panel: List of Wallpapers
        left_panel = ttk.Frame(main_frame, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)

        ttk.Label(left_panel, text="> ASCII GALLERY", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))

        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg="#1e1e1e",
            fg="#e0e0e0",
            selectbackground="#00ff88",
            selectforeground="#121212",
            font=("Consolas", 10),
            borderwidth=0,
            highlightthickness=1,
            highlightcolor="#333333",
            activestyle="none"
        )
        scrollbar.config(command=self.listbox.yview)

        for name in self.wallpapers.keys():
            self.listbox.insert(tk.END, f" {name}")

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Right Panel: Preview & Apply Button
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.preview_label = tk.Label(
            right_panel,
            text="Select a wallpaper to preview",
            bg="#0a0a0a",
            fg="#666666",
            font=("Consolas", 10),
            relief=tk.FLAT
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        bottom_bar = ttk.Frame(right_panel)
        bottom_bar.pack(fill=tk.X)

        self.info_label = ttk.Label(bottom_bar, text="")
        self.info_label.pack(side=tk.LEFT)

        self.apply_btn = ttk.Button(
            bottom_bar,
            text="Set as Desktop Wallpaper",
            style="Apply.TButton",
            command=self._apply_wallpaper
        )
        self.apply_btn.pack(side=tk.RIGHT)

    def _on_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return

        name = self.listbox.get(selection[0]).strip()
        path = self.wallpapers[name]
        
        # Update file size info
        size_mb = os.path.getsize(path) / (1024 * 1024)
        self.info_label.config(text=f"{name}.png ({size_mb:.2f} MB)")

        # Load and resize image using native Tkinter PhotoImage (no Pillow required)
        try:
            raw_img = tk.PhotoImage(file=path)
            # Calculate subsample factor to fit nicely inside the ~500x380 preview box
            scale_w = max(1, raw_img.width() // 500)
            scale_h = max(1, raw_img.height() // 380)
            scale = max(scale_w, scale_h)
            
            self.current_preview = raw_img.subsample(scale, scale)
            self.preview_label.config(image=self.current_preview, text="")
        except Exception as e:
            self.preview_label.config(image="", text=f"Preview unavailable:\n{e}")

    def _apply_wallpaper(self):
        selection = self.listbox.curselection()
        if not selection:
            return

        name = self.listbox.get(selection[0]).strip()
        image_path = os.path.abspath(self.wallpapers[name])
        os_name = platform.system()

        try:
            if os_name == "Windows":
                # SPI_SETDESKWALLPAPER = 20, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE = 3
                ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)

            elif os_name == "Darwin":  # macOS
                script = f'tell application "System Events" to tell every desktop to set picture to "{image_path}"'
                subprocess.run(["osascript", "-e", script], check=True)

            elif os_name == "Linux":
                # Supports GNOME / Ubuntu / Pop!_OS
                uri = f"file://{image_path}"
                subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri], check=True)
                subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", uri], check=False)
            else:
                raise NotImplementedError(f"Unsupported OS: {os_name}")

            messagebox.showinfo("Success", f"Wallpaper updated to {name}!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set wallpaper:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ASCIIWallpaperSelector(root)
    root.mainloop()
