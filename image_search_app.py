import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class ImageSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Search Tool")
        self.root.geometry("800x700") # Made window slightly taller to accommodate bigger bar

        # Variables
        self.search_folder = tk.StringVar()
        self.image_label = None

        # --- UI Layout ---

        # 1. Folder Selection Section
        folder_frame = tk.Frame(root, pady=15)
        folder_frame.pack(fill="x", padx=10)

        tk.Label(folder_frame, text="Search Folder:").pack(side="left")
        
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.search_folder, width=40)
        self.folder_entry.pack(side="left", padx=5)

        btn_browse = tk.Button(folder_frame, text="Browse...", command=self.browse_folder)
        btn_browse.pack(side="left")

        # 2. Search Bar Section (UPDATED)
        search_frame = tk.Frame(root, pady=10)
        search_frame.pack(fill="x", padx=10)

        tk.Label(search_frame, text="File Name:", font=("Arial", 12)).pack(side="left")
        
        # CHANGE 1: Added font to make it bigger, adjusted width
        self.search_entry = tk.Entry(search_frame, width=30, font=("Arial", 28)) 
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind('<Return>', self.perform_search)

        # Made the button slightly bigger too to match
        btn_search = tk.Button(search_frame, text="Search", command=self.perform_search, font=("Arial", 10), height=1)
        btn_search.pack(side="left")

        # 3. Image Display Area
        self.display_frame = tk.Frame(root, bg="gray90", width=750, height=650)
        self.display_frame.pack_propagate(False)
        self.display_frame.pack(pady=10)

        self.lbl_image = tk.Label(self.display_frame, text="No image displayed", bg="gray90")
        self.lbl_image.pack(expand=True)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.search_folder.set(folder_selected)

    def perform_search(self, event=None):
        folder = self.search_folder.get()
        
        # Get the text BEFORE clearing it
        filename = self.search_entry.get().strip()

        # CHANGE 2: Clear the search bar immediately
        self.search_entry.delete(0, tk.END)

        if not folder:
            messagebox.showwarning("Warning", "Please select a folder first.")
            return
        
        if not filename:
            messagebox.showwarning("Warning", "Please enter a file name.")
            return

        # Attempt to find the file
        found_path = self.find_file(folder, filename)

        if found_path:
            self.display_image(found_path)
            # Optional: Set focus back to entry so you can type the next one immediately
            self.search_entry.focus() 
        else:
            messagebox.showinfo("Not Found", f"Could not find '{filename}' in the selected folder.")
            self.clear_image()

    def find_file(self, folder, filename):
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        
        full_path = os.path.join(folder, filename)
        if os.path.isfile(full_path):
            return full_path

        for ext in extensions:
            test_path = os.path.join(folder, filename + ext)
            if os.path.isfile(test_path):
                return test_path
            
        return None

    def display_image(self, path):
        try:
            img = Image.open(path)
            
            # Resize logic
            display_width = 750
            display_height = 650
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