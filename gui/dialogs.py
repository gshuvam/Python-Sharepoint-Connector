import customtkinter as ctk
from utils.tools import write_config, set_mappings, get_mappings

class InputDialog(ctk.CTkToplevel):
    def __init__(self, master, prompt, title):
        super().__init__(master)
        self.title(title)
        self.prompt = prompt
        self.user_input = None
        self.attributes("-topmost", True)

        self.label = ctk.CTkLabel(self, text=self.prompt)
        self.label.pack(padx=10, pady=10)

        self.entry = ctk.CTkEntry(self)
        self.entry.pack(padx=10, pady=10)
        self.after(100, self.entry.focus_set())

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(padx=10, pady=10)

        self.ok_button = ctk.CTkButton(self.button_frame, text="OK", command=self.ok)
        self.ok_button.pack(side=ctk.LEFT, padx=5)

        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(side=ctk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.entry.bind("<Return>", lambda event: self.ok)
        self.entry.bind("<Escape>", lambda event: self.cancel)


    def ok(self, event=None):
        self.user_input = self.entry.get()
        if self.user_input:
            self.destroy()
        else:
            self.show_warning("Warning", "Input cannot be empty.")

    def cancel(self, event=None):
        self.user_input = None
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.user_input

    def show_warning(self, title, message):
        warning_dialog = ctk.CTkToplevel(self)
        warning_dialog.title(title)

        warning_label = ctk.CTkLabel(warning_dialog, text=message)
        warning_label.pack(padx=10, pady=10)

        ok_button = ctk.CTkButton(warning_dialog, text="OK", command=warning_dialog.destroy)
        ok_button.pack(padx=10, pady=10)

        warning_dialog.wait_window()

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, master, title, password_subject):
        
        super().__init__(master)
        self.title(title)
        self.user_input = None
        self.password_subject = password_subject

        self.label = ctk.CTkLabel(self, text="Enter the password")
        self.label.pack(padx=10, pady=10)
        
        self.label = ctk.CTkLabel(self, text=password_subject)
        self.label.pack(padx=10, pady=7)

        self.entry = ctk.CTkEntry(self, show='*')
        self.entry.pack(padx=10, pady=10)
        self.entry.focus_set()

        self.show_password = ctk.BooleanVar()
        self.show_password_check = ctk.CTkCheckBox(self, text="Show Password", variable=self.show_password, command=self.toggle_password)
        self.show_password_check.pack(padx=10, pady=10)

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(padx=10, pady=10)

        self.ok_button = ctk.CTkButton(self.button_frame, text="OK", command=self.ok)
        self.ok_button.pack(side=ctk.LEFT, padx=5)

        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(side=ctk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.entry.bind("<Return>", lambda event: self.ok)
        self.entry.bind("<Escape>", lambda event: self.cancel)

    def toggle_password(self):
        if self.show_password.get():
            self.entry.configure(show='')
        else:
            self.entry.configure(show='*')

    def ok(self, event=None):
        self.user_input = self.entry.get()
        if self.user_input:
            self.destroy()
        else:
            self.show_warning("Warning", "Password cannot be empty.")

    def cancel(self, event=None):
        self.user_input = None
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.user_input

    def show_warning(self, title, message):
        warning_dialog = ctk.CTkToplevel(self)
        warning_dialog.title(title)

        warning_label = ctk.CTkLabel(warning_dialog, text=message)
        warning_label.pack(padx=10, pady=10)

        ok_button = ctk.CTkButton(warning_dialog, text="OK", command=warning_dialog.destroy)
        ok_button.pack(padx=10, pady=10)

        warning_dialog.wait_window()

class MappingDialog(ctk.CTkToplevel):
    def __init__(self, parent, dataframe_columns, list_columns, config, file_path):
        super().__init__(parent)
        self.dataframe_columns = dataframe_columns
        self.list_columns = list_columns
        self.config = config
        self.file_path = file_path
        self.mappings = {}

        self.title("Column Mapping")
        window_length = 100 + (60*len(list_columns))
        self.geometry(f"400x{window_length}")
        
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="List Columns").grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkLabel(self, text="Excel Columns").grid(row=0, column=1, padx=10, pady=10)
        
        self.entries = {}
        for i, list_col in enumerate(self.list_columns):
            ctk.CTkLabel(self, text=list_col).grid(row=i+1, column=0, padx=10, pady=10)
            entry = ctk.CTkEntry(self)
            entry.grid(row=i+1, column=1, padx=10, pady=10)
            self.entries[list_col] = entry
        
        ctk.CTkButton(self, text="Submit", command=self.on_submit).grid(row=len(self.list_columns) + 1, column=0, padx=20, pady=20)
        ctk.CTkButton(self, text="Cancel", command=self.on_cancel).grid(row=len(self.list_columns) + 1, column=1, padx=20, pady=20)

    def on_submit(self):
        for list_col, entry in self.entries.items():
            df_col = entry.get()
            if not self.config.has_section('Mappings'):
                self.config.add_section('Mappings')
            set_mappings(self.config, 'Mappings', list_col, df_col)
            self.mappings[list_col] = df_col

        write_config(self.config, self.file_path)
        self.destroy()
    
    def on_cancel(self):
        self.destroy()


class MappingViewer(ctk.CTkToplevel):
    def __init__(self, parent, config, file_path):
        super().__init__(parent)
        self.config = config
        self.file_path = file_path
        self.mappings = {}

        self.title("View and Update Mappings")
        self.geometry("615x650")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()

    def create_widgets(self):
        self.canvas = ctk.CTkCanvas(self.main_frame, highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self.main_frame, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.entries = {}
        row_idx = 0

        for section in self.config.sections():
            ctk.CTkLabel(
                self.scrollable_frame, text=section, 
                font=ctk.CTkFont(size=16, weight="bold")
            ).grid(row=row_idx, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

            row_idx += 1
            if section == 'Mappings':
                ctk.CTkLabel(self.scrollable_frame, text='List Column').grid(row=row_idx, column=0, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(self.scrollable_frame, text='Current Mappings (comma-separated)').grid(row=row_idx, column=1, padx=10, pady=10, columnspan=4, sticky="w")

            row_idx += 1
            for list_col in self.config.options(section):
                ctk.CTkLabel(self.scrollable_frame, text=list_col).grid(row=row_idx, column=0, padx=10, pady=10, sticky="w")
                
                current_mappings = get_mappings(self.config, section, list_col)
                current_mappings_str = ", ".join(current_mappings)
                entry = ctk.CTkEntry(self.scrollable_frame, width=430)
                entry.insert(0, current_mappings_str)
                entry.grid(row=row_idx, column=1, padx=10, pady=10, sticky="w")
                self.entries[(section, list_col)] = entry
                
                row_idx += 1
                
        row_idx += 1
        button_frame = ctk.CTkFrame(self.scrollable_frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(button_frame, text="Update", command=self.on_update).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkButton(button_frame, text="Cancel", command=self.on_cancel).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_update(self):
        for (section, list_col), entry in self.entries.items():
            new_mapping_str = entry.get()
            new_mappings = [mapping.strip() for mapping in new_mapping_str.split(",")]
            self.config.set(section, list_col, str(new_mappings))
        
        write_config(self.config, self.file_path)
        self.destroy()

    def on_cancel(self):
        self.destroy()
    

class SheetSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, sheet_names, file_name):
        super().__init__(parent)
        self.title("Select Sheet")
        window_height = 200 + len(sheet_names) * 40
        self.geometry(f"300x{window_height}")
        self.result = None

        self.label = ctk.CTkLabel(self, text="Choose a sheet:")
        self.label.pack(pady=10)

        self.label = ctk.CTkLabel(self, text=f"File name: {file_name}")
        self.label.pack(pady=5)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(padx=70, pady=20)

        self.checkbox_vars = {}

        for sheet_name in sheet_names:
            var = ctk.StringVar(value="off")
            self.checkbox_vars[sheet_name] = var
            checkbox = ctk.CTkCheckBox(self.main_frame, text=sheet_name, variable=var, onvalue="on", offvalue="off")
            checkbox.pack(pady=10, padx=10, anchor='w')

        self.ok_button = ctk.CTkButton(self, text="OK", command=self.on_ok)
        self.ok_button.pack(side=ctk.LEFT, padx=5)

        self.cancel_button = ctk.CTkButton(self, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side=ctk.LEFT, padx=5)

    def on_ok(self):
        selected_sheets = [sheet for sheet, var in self.checkbox_vars.items() if var.get() == "on"]
        self.result = selected_sheets
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()