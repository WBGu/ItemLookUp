import tkinter as tk
from tkinter import messagebox
from tksheet import Sheet
import subprocess
import os
import json
import shutil
from collections import Counter

# --- CONFIGURATION ---
# UPDATE THIS PATH to your separate Data Repo folder
DATA_REPO_PATH = r"/path/to/your/separate/data_repo" 

# The name of the file
FILENAME = "inventory.json"

# Derived Paths
LOCAL_FILE = os.path.join(os.getcwd(), FILENAME)
REMOTE_FILE = os.path.join(DATA_REPO_PATH, FILENAME)

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory System - POS View")
        self.root.geometry("1450x750") 
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.inventory = self.load_inventory()

        # --- Top Control Panel (Buttons) ---
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_pull = tk.Button(control_frame, text="⬇ Pull Remote", bg="#FF9800", fg="white", font=("Arial", 10, "bold"), command=self.pull_inventory_data)
        self.btn_pull.pack(side="left", padx=(0, 5))

        self.btn_finalize = tk.Button(control_frame, text="✔ Finalize Transaction", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.finalize_transaction)
        self.btn_finalize.pack(side="left", padx=(5, 5))

        self.btn_push = tk.Button(control_frame, text="⬆ Push to Git", bg="#2196F3", fg="white", font=("Arial", 10, "bold"), command=self.push_inventory_data)
        self.btn_push.pack(side="left", padx=(5, 5))

        self.btn_add_rows = tk.Button(control_frame, text="+ Add 10 Rows", bg="#9E9E9E", fg="white", font=("Arial", 10, "bold"), command=self.add_more_rows)
        self.btn_add_rows.pack(side="left", padx=(5, 5))

        self.btn_copy = tk.Button(control_frame, text="📋 Copy Grid", bg="#673AB7", fg="white", font=("Arial", 10, "bold"), command=self.copy_grid_to_clipboard)
        self.btn_copy.pack(side="left", padx=(5, 0))
        
        tk.Label(control_frame, text="Legend: ", font=("Arial", 10, "bold")).pack(side="left", padx=(40, 0))
        tk.Label(control_frame, text=" OK ", bg="#DFF0D8").pack(side="left", padx=2)
        tk.Label(control_frame, text=" Oversold ", bg="orange").pack(side="left", padx=2)
        tk.Label(control_frame, text=" Invalid ID ", bg="#FFCDD2").pack(side="left", padx=2)

        # --- Time Input Panel ---
        time_frame = tk.Frame(self.root)
        time_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.month_var = tk.StringVar()
        self.day_var = tk.StringVar()
        self.hour_var = tk.StringVar()
        self.minute_var = tk.StringVar()
        self.ampm_var = tk.StringVar()

        tk.Label(time_frame, text="Start Time: ", font=("Arial", 10, "bold")).pack(side="left")

        tk.Entry(time_frame, textvariable=self.month_var, width=5).pack(side="left")
        tk.Label(time_frame, text="Month").pack(side="left", padx=(2, 10))

        tk.Entry(time_frame, textvariable=self.day_var, width=5).pack(side="left")
        tk.Label(time_frame, text="Day").pack(side="left", padx=(2, 10))

        tk.Entry(time_frame, textvariable=self.hour_var, width=5).pack(side="left")
        tk.Label(time_frame, text="Hour").pack(side="left", padx=(2, 10))

        tk.Entry(time_frame, textvariable=self.minute_var, width=5).pack(side="left")
        tk.Label(time_frame, text="Minute").pack(side="left", padx=(2, 10))

        tk.Entry(time_frame, textvariable=self.ampm_var, width=5).pack(side="left")
        tk.Label(time_frame, text="AM/PM").pack(side="left", padx=(2, 10))

        # --- Main Content Area (Splits into Left and Right) ---
        main_content_frame = tk.Frame(self.root)
        main_content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT SIDE: Sheet Setup
        self.sheet_frame = tk.Frame(main_content_frame)
        self.sheet_frame.pack(side="left", fill="both", expand=True)

        headers = ["Buyer"] + ["Item ID"] * 10
        self.sheet = Sheet(self.sheet_frame, headers=headers, total_columns=11, total_rows=15)
        self.sheet.enable_bindings(("single_select", "row_select", "column_width_resize", 
                                    "arrowkeys", "rc_select", "copy", "cut", "paste", 
                                    "delete", "undo", "edit_cell"))
        self.sheet.pack(fill="both", expand=True)

        col_widths = [200] + [85] * 10
        self.sheet.set_column_widths(col_widths)

        self.sheet.extra_bindings("end_edit_cell", func=self.validate_entire_sheet)
        self.sheet.extra_bindings("end_paste", func=self.validate_entire_sheet)

        # RIGHT SIDE: Inventory Display Panel
        self.inv_display_frame = tk.Frame(main_content_frame, width=280) # Increased width to 280 to fit longer labels
        self.inv_display_frame.pack(side="right", fill="y", padx=(10, 0))
        self.inv_display_frame.pack_propagate(False) 

        tk.Label(self.inv_display_frame, text="Current Inventory", font=("Arial", 10, "bold"), bg="#E0E0E0").pack(fill="x", pady=(0, 5))

        # --- Search Bar UI ---
        search_frame = tk.Frame(self.inv_display_frame)
        search_frame.pack(fill="x", pady=(0, 5))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=12)
        self.search_entry.pack(side="left", padx=(0, 2))
        self.search_entry.bind("<Return>", self.search_inventory) # Bind Enter key

        self.search_btn = tk.Button(search_frame, text="🔍", command=self.search_inventory)
        self.search_btn.pack(side="left")

        self.search_result_label = tk.Label(search_frame, text="Qty: -", font=("Arial", 10, "bold"))
        self.search_result_label.pack(side="left", padx=(5, 0))
        # ---------------------------

        # Scrollbar and Text area
        self.inv_scrollbar = tk.Scrollbar(self.inv_display_frame)
        self.inv_scrollbar.pack(side="right", fill="y")

        self.inv_text = tk.Text(self.inv_display_frame, yscrollcommand=self.inv_scrollbar.set, font=("Courier", 11), state="disabled", bg="#F8F9FA")
        self.inv_text.pack(side="left", fill="both", expand=True)
        self.inv_scrollbar.config(command=self.inv_text.yview)

        # Populate the display initially
        self.update_inventory_display()

    def search_inventory(self, event=None):
        """Looks up the item ID, displays the formatted result, and clears the bar."""
        query = self.search_var.get().strip().upper()
        
        if not query:
            self.search_result_label.config(text="Qty: -", fg="black")
            return
            
        if query in self.inventory:
            qty = self.inventory[query]
            if qty > 0:
                self.search_result_label.config(text=f"{query} - Qty: {qty}", fg="green")
            else:
                self.search_result_label.config(text=f"{query} - Qty: 0", fg="red")
        else:
            self.search_result_label.config(text=f"{query} - Not Found", fg="red")
            
        # Clear the search bar text
        self.search_var.set("")

    def update_inventory_display(self):
        self.inv_text.config(state="normal") 
        self.inv_text.delete("1.0", tk.END)  
        
        display_str = "ID      | Qty\n"
        display_str += "-" * 15 + "\n"
        
        for item_id, qty in sorted(self.inventory.items()):
            display_str += f"{item_id:<8}| {qty}\n"
            
        self.inv_text.insert(tk.END, display_str)
        self.inv_text.config(state="disabled")

    def on_closing(self):
        if messagebox.askyesno("Exit Confirmation", "Are you sure you want to exit?\nUnsaved work on the grid will be lost."):
            self.root.destroy()

    def add_more_rows(self):
        for _ in range(10):
            self.sheet.insert_row()
        self.sheet.redraw()

    def copy_grid_to_clipboard(self):
        try:
            m = self.month_var.get()
            d = self.day_var.get()
            h = self.hour_var.get()
            mins = self.minute_var.get()
            ampm = self.ampm_var.get()

            clipboard_text = f"Start Time:\t{m}/{d} @ {h}:{mins} {ampm}\n\n"

            headers = self.sheet.headers()
            clipboard_text += "\t".join([str(h) for h in headers]) + "\n"
            
            data = self.sheet.get_sheet_data()
            for row in data:
                clean_row = [str(x) if x is not None else "" for x in row]
                clipboard_text += "\t".join(clean_row) + "\n"
            
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            self.root.update()
            
            messagebox.showinfo("Success", "Grid and Time copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")

    def load_inventory(self):
        if not os.path.exists(LOCAL_FILE):
            if os.path.exists(REMOTE_FILE):
                shutil.copy(REMOTE_FILE, LOCAL_FILE)
            else:
                return {}
        try:
            with open(LOCAL_FILE, 'r') as f:
                data = json.load(f)
                return {k.upper(): v for k, v in data.items()}
        except Exception as e:
            print(f"Load Error: {e}")
            return {}

    def save_inventory_locally(self):
        try:
            with open(LOCAL_FILE, 'w') as f:
                json.dump(self.inventory, f, indent=4)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file: {e}")

    def finalize_transaction(self):
        all_data = self.sheet.get_sheet_data()
        transaction_counts = Counter()
        
        for row_data in all_data:
            for item in row_data[1:]: 
                item_str = str(item).strip().upper()
                if item_str:
                    transaction_counts[item_str] += 1
        
        if not transaction_counts:
            messagebox.showinfo("Info", "No items to finalize.")
            return

        for item_id, qty_needed in transaction_counts.items():
            if item_id not in self.inventory:
                messagebox.showerror("Error", f"Item '{item_id}' is invalid.")
                return
            if qty_needed > self.inventory[item_id]:
                messagebox.showerror("Error", f"Item '{item_id}' is oversold.")
                return

        confirm = messagebox.askyesno("Confirm", "Finalize transaction and update inventory?")
        if not confirm:
            return

        items_hit_zero = []
        for item_id, qty_used in transaction_counts.items():
            self.inventory[item_id] -= qty_used
            if self.inventory[item_id] == 0:
                items_hit_zero.append(item_id)
        
        self.save_inventory_locally()
        
        self.update_inventory_display()
        
        self.search_var.set("")
        self.search_inventory() 
        
        self.sheet.set_sheet_data([["" for _ in range(11)] for _ in range(15)])
        self.sheet.redraw()

        success_msg = "Transaction Finalized Successfully!"
        if items_hit_zero:
            zero_list_str = "\n".join([f"• {item}" for item in items_hit_zero])
            warning_msg = f"{success_msg}\n\n⚠️ URGENT: The following items are now OUT OF STOCK:\n{zero_list_str}"
            messagebox.showwarning("Stock Alert", warning_msg)
        else:
            messagebox.showinfo("Success", success_msg)

    def pull_inventory_data(self):
        if not os.path.exists(DATA_REPO_PATH):
            messagebox.showerror("Error", f"Data Repo path not found:\n{DATA_REPO_PATH}")
            return
        
        if not messagebox.askyesno("Force Update", "Overwrite local inventory with Git version?\nUnsaved changes will be lost."):
            return

        try:
            subprocess.run(["git", "fetch", "--all"], cwd=DATA_REPO_PATH, capture_output=True, text=True)
            reset_result = subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=DATA_REPO_PATH, capture_output=True, text=True)
            
            if reset_result.returncode != 0:
                messagebox.showerror("Git Error", f"Reset failed:\n{reset_result.stderr}")
                return

            if os.path.exists(REMOTE_FILE):
                shutil.copy(REMOTE_FILE, LOCAL_FILE)
                self.inventory = self.load_inventory()
                
                self.update_inventory_display()
                self.validate_entire_sheet()
                
                self.search_var.set("")
                self.search_inventory()
                
                messagebox.showinfo("Success", f"Inventory Force Updated!\nServer status: {reset_result.stdout}")
            else:
                messagebox.showerror("Error", "inventory.json missing from data repo.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def push_inventory_data(self):
        try:
            shutil.copy(LOCAL_FILE, REMOTE_FILE)
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy inventory to repo: {e}")
            return

        script_path = "git_sync.bat"
        try:
            result = subprocess.run(["cmd.exe", "/c", script_path, DATA_REPO_PATH], capture_output=True, text=True)
            if result.returncode == 0:
                messagebox.showinfo("Git Push Success", result.stdout)
            else:
                messagebox.showerror("Git Push Error", result.stderr)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def validate_entire_sheet(self, event=None):
        try:
            all_data = self.sheet.get_sheet_data()
            item_counts = Counter()
            
            for row_data in all_data:
                for item in row_data[1:]: 
                    item_str = str(item).strip().upper()
                    if item_str:
                        item_counts[item_str] += 1
            
            for row_idx, row_data in enumerate(all_data):
                for col_idx in range(1, 11): 
                    raw_val = row_data[col_idx]
                    if raw_val is None: item_id = ""
                    else: item_id = str(raw_val).strip().upper()

                    if not item_id:
                        self.sheet.highlight_cells(row=row_idx, column=col_idx, bg=None, redraw=False)
                        continue

                    if item_id not in self.inventory:
                        self.sheet.highlight_cells(row=row_idx, column=col_idx, bg="#FFCDD2", redraw=False)
                    elif item_counts[item_id] > self.inventory[item_id]:
                        self.sheet.highlight_cells(row=row_idx, column=col_idx, bg="orange", redraw=False)
                    else:
                        self.sheet.highlight_cells(row=row_idx, column=col_idx, bg="#DFF0D8", redraw=False)
            
            self.sheet.redraw()
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()