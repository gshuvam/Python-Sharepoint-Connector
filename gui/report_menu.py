import customtkinter as ctk

from reports_main import main as generate_report
from main import main as sync

class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Reports Menu")
        self.geometry("400x570")
        self.file_paths = []
        self.dfs = {}
        self.mappings = {}

        self.label = ctk.CTkLabel(self, text="Main Menu", font=("Aptos", 25))
        self.label.pack(pady=20)

        self.open_button = ctk.CTkButton(
            self, text="Sync BG List", command=self.sync_bg_list
        )
        self.open_button.pack(pady=10)

        self.open_button = ctk.CTkButton(
            self, text="Generate All Reports", command=self.generate_all_reports
        )
        self.open_button.pack(pady=10)

        self.open_button = ctk.CTkButton(
            self,
            text="Sync BG List and Generate Reports",
            command=self.sync_list_gen_reports,
        )
        self.open_button.pack(pady=10)

        self.open_button = ctk.CTkButton(
            self, text="Generate Duplicate RGS Report", command=self.gen_dup_res_report
        )
        self.open_button.pack(pady=10)

        self.open_button = ctk.CTkButton(
            self,
            text="Generate Pending Updates Report",
            command=self.gen_pending_updates_report,
        )
        self.open_button.pack(pady=10)

        self.open_button = ctk.CTkButton(
            self,
            text="Generate Onboarding Status Report",
            command=self.gen_onboarding_status_report,
        )
        self.open_button.pack(pady=10)

        self.open_button = ctk.CTkButton(
            self,
            text="Generate Delayed Onboarding Report",
            command=self.gen_delayed_onboarding_report,
        )
        self.open_button.pack(pady=10)

        self.open_button = ctk.CTkButton(
            self,
            text="Generate Requirements Summary Report",
            command=self.gen_requirements_summary_report,
        )
        self.open_button.pack(pady=10)

        self.quit_button = ctk.CTkButton(self, text="Quit", command=self.quit)
        self.quit_button.pack(pady=10)

    def close_app(self):
        self.quit()

    def sync_bg_list(self):
        self.withdraw()
        sync()
        generate_report()
        self.quit()

    def generate_all_reports(self):
        self.withdraw()
        generate_report()
        self.quit()

    def sync_list_gen_reports(self):
        self.withdraw()
        generate_report(report="All")
        self.quit()

    def gen_dup_res_report(self):
        self.withdraw()
        generate_report(report="Duplicate RGS Report")
        self.quit()

    def gen_pending_updates_report(self):
        self.withdraw()
        generate_report(report="Pending Updates Report")
        self.quit()

    def gen_onboarding_status_report(self):
        self.withdraw()
        generate_report(report="Onboarding Status Report")
        self.quit()

    def gen_delayed_onboarding_report(self):
        self.withdraw()
        generate_report(report="Delayed Onboarding Report")
        self.quit()

    def gen_requirements_summary_report(self):
        self.withdraw()
        generate_report(report="Requirements Summary Report")
        self.quit()
