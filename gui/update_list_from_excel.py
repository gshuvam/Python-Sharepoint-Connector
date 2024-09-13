from tkinter import filedialog
import io
import customtkinter as ctk
import msoffcrypto
import pandas as pd
from auth.auth import LoginHandler
from gui.dialogs import (
    InputDialog,
    PasswordDialog,
    MappingDialog,
    MappingViewer,
    SheetSelectionDialog,
)
from sharepoint.list import List
from utils.tools import read_config, get_mappings, str_to_bool


class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Update List from Excel Files")
        self.geometry("400x230")
        self.file_paths = []
        self.dfs = {}
        self.mappings = {}
        # img = PhotoImage(file='C:\\Users\\1772690\\Python\\ShareConnect\\src\\app.ico')
        # self.iconphoto(False, img)

        self.label = ctk.CTkLabel(self, text="Main Menu")
        self.label.pack(pady=20)

        self.open_button = ctk.CTkButton(
            self, text="Update SharePoint List", command=self.prompt_for_files
        )
        self.open_button.pack(pady=10)

        self.open_button = ctk.CTkButton(
            self, text="Update Config File", command=self.current_mapping_config
        )
        self.open_button.pack(pady=10)

        self.quit_button = ctk.CTkButton(self, text="Quit", command=self.quit)
        self.quit_button.pack(pady=10)

    def prompt_for_files(self):
        self.withdraw()
        self.file_paths = list(
            filedialog.askopenfilenames(
                title="Select Excel files",
                filetypes=[("Excel files", "*.xlsx;*.xls;*.xlsb")],
            )
        )

        if not self.file_paths:
            self.quit()
            return

        self.process_files()

    def get_password(self, file_name):
        dialog = PasswordDialog(
            self, "Password", f"The file {file_name} is passoword encrypted"
        )
        return dialog.get_input()

    def choose_sheet(self, sheet_names, filename):
        dialog = SheetSelectionDialog(self, sheet_names, filename)
        self.wait_window(dialog)
        return dialog.result

    def process_files(self):
        index = 0
        file_encrypted = True

        for file_path in self.file_paths:
            chosen_sheets = None
            file_name = file_path.split("/")[-1]

            if file_name.endswith('.xlsb'):
                engine = 'pyxlsb'
            else:
                engine = 'openpyxl'
            try:
                all_sheets = pd.ExcelFile(file_path).sheet_names
                if all_sheets:
                    file_encrypted = False

                if len(all_sheets) > 1:
                    chosen_sheets = self.choose_sheet(all_sheets, file_name)
                    if not chosen_sheets:
                        print(f"No sheet selected for {file_name}. Skipping...")
                        continue
                else:
                    chosen_sheets = all_sheets

                for sheet in chosen_sheets:
                    df = pd.read_excel(file_path, sheet_name=sheet, engine=engine)
                    self.dfs[file_name] = df
                index += 1

            except Exception as e:
                if file_encrypted:
                    # maybe the file is password protected

                    try:
                        password = self.get_password(file_name)
                        with open(file_path, "rb") as file:
                            decrypted_file = io.BytesIO()
                            office_file = msoffcrypto.OfficeFile(file)
                            office_file.load_key(password=password)
                            office_file.decrypt(decrypted_file)
                            decrypted_file.seek(0)

                        sheet_names = pd.ExcelFile(decrypted_file).sheet_names
                        # print(sheet_names)
                        if len(sheet_names) > 1:
                            chosen_sheets = self.choose_sheet(sheet_names, file_name)
                            if not chosen_sheets:
                                print(f"No sheet selected for {file_name}. Skipping...")
                                continue
                        else:
                            chosen_sheets = sheet_names
                        for sheet in chosen_sheets:
                            df = pd.read_excel(
                                decrypted_file, sheet_name=sheet, engine=engine
                            )
                            self.dfs[file_name] = df
                        index += 1
                    except Exception as e:
                        self.file_paths = self.file_paths[index:]
                        return self.handle_read_error(e, "Failed to open the file")
                else:
                    print("Exception noticed on: ", e)
        if not self.dfs:
            self.close_app()
        val = self.update_sharepoint_list()
        try:
            if not val:
                raise ValueError
        except ValueError as ve:
            self.handle_read_error(ve, "No column match found!")

    def handle_read_error(self, error, error_text):
        retry_dialog = ctk.CTkToplevel(self)
        retry_dialog.title("Error")

        error_label = ctk.CTkLabel(retry_dialog, text=error_text)
        error_label.pack(padx=10, pady=10)

        error_label = ctk.CTkLabel(retry_dialog, text=error)
        error_label.pack(padx=5, pady=5)

        button_frame = ctk.CTkFrame(retry_dialog)
        button_frame.pack(padx=10, pady=10)

        retry_button = ctk.CTkButton(
            button_frame,
            text="Retry",
            command=lambda: [retry_dialog.destroy(), self.process_files()],
        )
        retry_button.pack(side=ctk.LEFT, padx=5)

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=lambda: [retry_dialog.destroy(), self.quit()],
        )
        cancel_button.pack(side=ctk.LEFT, padx=5)

        retry_dialog.wait_window()

        if not self:
            raise RuntimeError("Application closed")

    def check_mapping(self, df, config, file_path):
        dataframe_columns = df.columns.values.tolist()
        list_columns = get_mappings(config, "List Columns", "list_columns")
        list_columns.remove('Profile Type')

        unmapped_columns = {}
        for list_col in list_columns:
            if list_col not in dataframe_columns:
                mappings = get_mappings(config, "Mappings", list_col)
                matched = False
                for mapping in mappings:
                    if mapping in dataframe_columns:
                        unmapped_columns[list_col] = mapping
                        matched = True
                        break
                if not matched:
                    unmapped_columns[list_col] = None

        mapping_needed = any(value is None for value in unmapped_columns.values())

        list_columns_for_config_update = [
            key for key, value in unmapped_columns.items() if value is None
        ]

        if mapping_needed:
            self.manual_mapping(df, list_columns_for_config_update, config, file_path)

            if not mappings:
                return
            unmapped_columns.update(self.mappings)
        else:
            for list_col, value in unmapped_columns.items():
                if unmapped_columns[list_col] is None:
                    unmapped_columns[list_col] = config.get("Mappings", list_col)

        self.close_app()
        return unmapped_columns

    def manual_mapping(self, df, list_columns, config, file_path):
        self.withdraw()
        dialog = MappingDialog(self, df.columns, list_columns, config, file_path)
        self.wait_window(dialog)
        self.mappings = dialog.mappings

    def close_app(self):
        self.quit()

    def current_mapping_config(self):
        self.withdraw()
        file_path = "mapping.ini"
        config = read_config(file_path)
        self.withdraw()
        viewer = MappingViewer(self, config, file_path)
        self.wait_window(viewer)
        self.deiconify()

    def update_sharepoint_list(self):
        dfs = self.dfs
        file_path = "mapping.ini"
        config = read_config(file_path)
        list_columns = get_mappings(config, "List Columns", "list_columns")

        list_columns.remove('Profile Type')

        for _, df in dfs.items():
            insert_list = []
            self.mappings = self.check_mapping(df, config, file_path)
            if not self.mappings:
                return False

            dataframe_columns = df.columns.values.tolist()

            for _, row in df.iterrows():
                payload = {}
                for column in list_columns:
                    if column not in dataframe_columns:
                        payload[column] = row[self.mappings[column]]
                    else:
                        payload[column] = row[column]
                payload['Profile Type'] =  'Internal'
                insert_list.append(payload)

            self.insert_list_items(insert_list, config)
        return True

    def insert_list_items(self, insert_list, config):
        site_url = get_mappings(config, "Environment Variables", "site_url")[0]
        list_name = get_mappings(config, "Environment Variables", "list_name")[0]
        key_location = get_mappings(config, "Environment Variables", 'key_location')[0]
        cache_location = get_mappings(config, "Environment Variables", 'cache_location')[0]
        domain = get_mappings(config, "Environment Variables", 'domain')[0]
        DEBUGGING = str_to_bool(
            get_mappings(config, "Environment Variables", "debugging")[0]
        )

        ENABLE_CACHE = str_to_bool(
            get_mappings(config, "Environment Variables", "enable_cache")[0]
        )

        username_dialog = InputDialog(self, "Username", "Enter Sharepoint Username")
        username = username_dialog.get_input()

        # password_dialog = PasswordDialog(self, "Password", "Enter Sharepoint Password")
        # password = password_dialog.get_input()
        password = None

        login_handler = LoginHandler(
            site_url=site_url,
            username=username,
            password=password,
            DEBUGGING=DEBUGGING,
            cache_file=cache_location,
            key_file=key_location,
            domain=domain
        )

        cookies = login_handler.authenticate(ENABLE_CACHE)

        list_operations = List(
            source_site=None,
            destination_site=site_url,
            source_list=None,
            destination_list=list_name,
            cookie_dict=cookies,
            list_excel_col_mapping=self.mappings
        )

        list_operations.insert_items(insert_list)
