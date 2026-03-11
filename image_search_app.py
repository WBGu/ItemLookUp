import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import json  # Added for JSON parsing

class ImageSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Search Tool + Inventory")
        self.root.geometry("800x850") # Increased height for inventory info

        # --- Variables ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        
        default_json_inventory = os.path.join(parent_dir, "Inventory","Inventory.json")
        
        self.search_folder = tk.StringVar()
        self.inventory_path = tk.StringVar(value=default_json_inventory)
        self.inventory_data = {}
        
        if os.path.exists(default_json_inventory):
            self.load_inventory()
        else:
            print("Warning: Default inventory JSON not found on startup.")

        # --- UI Layout ---
        # 1. Folder & File Selection Section
        selection_frame = tk.Frame(root, pady=10)
        selection_frame.pack(fill="x", padx=10)

        # Image Folder Row
        tk.Label(selection_frame, text="Images Folder:").grid(row=0, column=0, sticky="w")
        tk.Entry(selection_frame, textvariable=self.search_folder, width=50).grid(row=0, column=1, padx=5)
        tk.Button(selection_frame, text="Browse...", command=self.browse_folder).grid(row=0, column=2)

        # Inventory JSON Row
        tk.Label(selection_frame, text="Inventory JSON:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(selection_frame, textvariable=self.inventory_path, width=50).grid(row=1, column=1, padx=5)
        tk.Button(selection_frame, text="Browse...", command=self.browse_inventory).grid(row=1, column=2)

        # 2. Search Bar Section
        search_frame = tk.Frame(root, pady=10)
        search_frame.pack(fill="x", padx=10)

        tk.Label(search_frame, text="Item ID:", font=("Arial", 12)).pack(side="left")
        
        self.search_entry = tk.Entry(search_frame, width=20, font=("Arial", 28)) 
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind('<Return>', self.perform_search)

        btn_search = tk.Button(search_frame, text="Search", command=self.perform_search, font=("Arial", 10), height=2)
        btn_search.pack(side="left")

        # 3. Inventory Result Text
        # This is where "K294 - Qty: 4" will appear
        self.lbl_inventory_info = tk.Label(root, text="", font=("Arial", 16, "bold"), fg="blue")
        self.lbl_inventory_info.pack(pady=5)

        # 4. Image Display Area
        self.display_frame = tk.Frame(root, bg="gray90", width=750, height=550)
        self.display_frame.pack_propagate(False)
        self.display_frame.pack(pady=10)

        self.lbl_image = tk.Label(self.display_frame, text="No image displayed", bg="gray90")
        self.lbl_image.pack(expand=True)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.search_folder.set(folder_selected)

    def browse_inventory(self):
        file_selected = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_selected:
            self.inventory_path.set(file_selected)
            self.load_inventory()

    def load_inventory(self):
        """Loads or reloads the JSON data."""
        try:
            with open(self.inventory_path.get(), 'r') as f:
                self.inventory_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON: {e}")

    def perform_search(self, event=None):
        folder = self.search_folder.get()
        item_id = self.search_entry.get().strip()

        # Clear search bar immediately
        self.search_entry.delete(0, tk.END)

        if not folder:
            messagebox.showwarning("Warning", "Please select an image folder first.")
            return
        
        if not item_id:
            return

        # 1. Update Inventory Text
        # We reload the inventory here in case the JSON file was edited externally
        if self.inventory_path.get():
            self.load_inventory()
            
        qty = self.inventory_data.get(item_id, "N/A")
        self.lbl_inventory_info.config(text=f"{item_id} - Qty: {qty}")

        # 2. Attempt to find and display the image
        found_path = self.find_file(folder, item_id)

        if found_path:
            self.display_image(found_path)
            self.search_entry.focus() 
        else:
            messagebox.showinfo("Not Found", f"Could not find image for '{item_id}'.")
            self.clear_image()

    def find_file(self, folder, filename):
        extensions = ['', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
        for root, dirs, files in os.walk(folder):
            for ext in extensions:
                target = filename + ext
                if target in files:
                    return os.path.join(root, target)
        return None

    def display_image(self, path):
        try:
            img = Image.open(path)
            # Maintain aspect ratio logic
            display_width, display_height = 750, 550
            img_ratio = img.width / img.height
            frame_ratio = display_width / display_height

            if img_ratio > frame_ratio:
                new_width = display_width
                new_height = int(display_width / img_ratio)
            else:
                new_height = display_height
                new_width = int(display_height * img_ratio)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            self.lbl_image.config(image=photo, text="")
            self.lbl_image.image = photo 

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def clear_image(self):
        self.lbl_image.config(image="", text="No image displayed")
        self.lbl_image.image = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSearchApp(root)
    root.mainloop()