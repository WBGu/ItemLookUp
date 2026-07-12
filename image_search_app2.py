import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import json
import re


class ImageSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Search Tool + Inventory")
        self.root.geometry("800x850")

        # --------------------------------------------------
        # Variables
        # --------------------------------------------------

        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)

        default_json_inventory = os.path.join(
            parent_dir,
            "Inventory",
            "Inventory.json"
        )

        self.search_folder = tk.StringVar()
        self.inventory_path = tk.StringVar(value=default_json_inventory)

        self.inventory_data = {}

        self.current_files = []
        self.current_index = 0
        self.current_item_id = ""

        if os.path.exists(default_json_inventory):
            self.load_inventory()
        else:
            print("Warning: Default inventory JSON not found on startup.")

        # --------------------------------------------------
        # Folder / Inventory Selection
        # --------------------------------------------------

        selection_frame = tk.Frame(root, pady=10)
        selection_frame.pack(fill="x", padx=10)

        tk.Label(
            selection_frame,
            text="Images Folder:"
        ).grid(row=0, column=0, sticky="w")

        tk.Entry(
            selection_frame,
            textvariable=self.search_folder,
            width=50
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            selection_frame,
            text="Browse...",
            command=self.browse_folder
        ).grid(row=0, column=2)

        tk.Label(
            selection_frame,
            text="Inventory JSON:"
        ).grid(row=1, column=0, sticky="w", pady=5)

        tk.Entry(
            selection_frame,
            textvariable=self.inventory_path,
            width=50
        ).grid(row=1, column=1, padx=5)

        tk.Button(
            selection_frame,
            text="Browse...",
            command=self.browse_inventory
        ).grid(row=1, column=2)

        # --------------------------------------------------
        # Search Section
        # --------------------------------------------------

        search_frame = tk.Frame(root, pady=10)
        search_frame.pack(fill="x", padx=10)

        tk.Label(
            search_frame,
            text="Item ID:",
            font=("Arial", 12)
        ).pack(side="left")

        self.search_entry = tk.Entry(
            search_frame,
            width=20,
            font=("Arial", 28)
        )
        self.search_entry.pack(side="left", padx=10)

        self.search_entry.bind(
            "<Return>",
            self.perform_search
        )

        tk.Button(
            search_frame,
            text="Search",
            command=self.perform_search,
            font=("Arial", 10),
            height=2
        ).pack(side="left")

        # --------------------------------------------------
        # Navigation Buttons
        # --------------------------------------------------

        nav_frame = tk.Frame(root)
        nav_frame.pack(pady=5)

        tk.Button(
            nav_frame,
            text="◀ Previous",
            width=12,
            command=self.show_previous
        ).pack(side="left", padx=10)

        tk.Button(
            nav_frame,
            text="Next ▶",
            width=12,
            command=self.show_next
        ).pack(side="left", padx=10)

        # --------------------------------------------------
        # Inventory Information
        # --------------------------------------------------

        self.lbl_inventory_info = tk.Label(
            root,
            text="",
            font=("Arial", 16, "bold"),
            fg="blue"
        )
        self.lbl_inventory_info.pack(pady=5)

        # --------------------------------------------------
        # Image Display
        # --------------------------------------------------

        self.display_frame = tk.Frame(root)
        self.display_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.lbl_filename = tk.Label(
            self.display_frame,
            text="",
            font=("Arial", 12, "bold")
        )
        self.lbl_filename.pack(pady=5)

        self.lbl_image = tk.Label(self.display_frame)
        self.lbl_image.pack(expand=True)

        # --------------------------------------------------
        # Keyboard Navigation
        # --------------------------------------------------

        self.root.bind("<Left>", lambda e: self.show_previous())
        self.root.bind("<Right>", lambda e: self.show_next())

    # ==================================================
    # Inventory Functions
    # ==================================================

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()

        if folder_selected:
            self.search_folder.set(folder_selected)

    def browse_inventory(self):
        file_selected = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )

        if file_selected:
            self.inventory_path.set(file_selected)
            self.load_inventory()

    def load_inventory(self):
        try:
            with open(self.inventory_path.get(), "r") as f:
                self.inventory_data = json.load(f)

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load JSON:\n{e}"
            )

    # ==================================================
    # Search
    # ==================================================

    def perform_search(self, event=None):
        folder = self.search_folder.get()
        item_id = self.search_entry.get().strip()

        self.search_entry.delete(0, tk.END)

        if not folder:
            messagebox.showwarning(
                "Warning",
                "Please select an image folder first."
            )
            return

        if not item_id:
            return

        self.current_item_id = item_id
        if self.inventory_path.get():
            self.load_inventory()

        found_paths = self.find_files(folder, item_id)
        print("FILES FOUND:")
        for f in found_paths:
            print("   ", os.path.basename(f))

        print("COUNT:", len(found_paths))

        if found_paths:
            self.current_files = found_paths
            self.current_index = 0
            self.show_current_image()
            self.root.focus_set()
        else:
            self.clear_image()

            messagebox.showinfo(
                "Not Found",
                f"Could not find image for '{item_id}'."
            )

    def find_files(self, folder, prefix):
        valid_exts = (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp"
        )

        matches = []

        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                name, ext = os.path.splitext(file)

                if (
                    ext.lower() in valid_exts
                    and name.startswith(prefix)
                ):
                    matches.append(
                        os.path.join(root_dir, file)
                    )

        return sorted(matches)

    # ==================================================
    # Image Display
    # ==================================================

    def show_current_image(self):
        if not self.current_files:
            return

        path = self.current_files[self.current_index]

        filename = os.path.splitext(
            os.path.basename(path)
        )[0]

        # Converts:
        # K295 -> K295
        # K295_1 -> K295
        # K295_2 -> K295
        item_id = filename.split("_")[0]

        qty = self.inventory_data.get(item_id, "N/A")

        self.lbl_inventory_info.config(
            text=f"Item: {item_id}    Qty: {qty}"
        )

        try:
            img = Image.open(path)

            max_width = 750
            max_height = 550

            img.thumbnail(
                (max_width, max_height),
                Image.Resampling.LANCZOS
            )

            photo = ImageTk.PhotoImage(img)

            self.lbl_image.config(image=photo)
            self.lbl_image.image = photo

            self.lbl_filename.config(
                text=(
                    f"{os.path.basename(path)}   "
                    f"({self.current_index + 1}"
                    f"/{len(self.current_files)})"
                )
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to open image:\n{e}"
            )

    # ==================================================
    # Navigation
    # ==================================================

    def navigate_item(self, direction):
        if not self.current_item_id:
            return

        # Find the numeric part of the current item ID
        match = re.search(r'(\d+)', self.current_item_id)
        if match:
            num_str = match.group(1)
            current_num = int(num_str)

            # Increment or decrement based on direction
            if direction == "next":
                new_num = current_num + 1
            else:
                new_num = current_num - 1

            # Pad with zeros to match the original string length (e.g., 05 -> 06)
            new_num_str = f"{new_num:0{len(num_str)}d}"

            # Reconstruct the string (e.g., "K295" -> "K296")
            new_item_id = (
                self.current_item_id[:match.start()] +
                new_num_str +
                self.current_item_id[match.end():]
            )

            print(f"Navigating to {direction} item: {new_item_id}")

            # Populate the search bar and trigger a new search programmatically
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, new_item_id)
            self.perform_search()
        else:
            print("No numeric part found in Item ID to increment.")

    def show_next(self):
        self.navigate_item("next")

    def show_previous(self):
        self.navigate_item("prev")

    # ==================================================
    # Clear
    # ==================================================

    def clear_image(self):
        self.lbl_image.config(image="")
        self.lbl_image.image = None

        self.lbl_filename.config(text="")
        self.lbl_inventory_info.config(text="")

        self.current_files = []
        self.current_index = 0
        
    def on_left_arrow(self, event):
        print("LEFT ARROW")
        self.show_previous()

    def on_right_arrow(self, event):
        print("RIGHT ARROW")
        self.show_next()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSearchApp(root)
    root.mainloop()