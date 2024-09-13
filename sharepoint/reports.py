from datetime import datetime, timedelta
import re

import pandas as pd

from connector.sharepoint_connector import SharePointConnector
from sharepoint.list_operations import ListOperations


class OverviewReport(SharePointConnector):
    def __init__(self, source_site, destination_site, cookie_dict, report_list):
        super().__init__(source_site, destination_site, cookie_dict)
        self.report_list = report_list
        self.required_columns = ListOperations.get_required_columns(
            self.source_site, self.report_list, self.session
        )

    def generate_report(self, simplified_list:list):
        df = pd.DataFrame(simplified_list)
        df["Mandatory Skill_lower"] = df["Mandatory Skill"].str.lower()
        df["Onsite/ Offshore_lower"] = df["Onsite/ Offshore"].str.lower()

        grouped = df.groupby(["Mandatory Skill_lower", "Onsite/ Offshore_lower"])
        aggregated_df = grouped.agg(
            **{
                "Total Requirements": (
                    "Current Status",
                    lambda x: len(x)
                ),
                "Open Requirements": (
                    "Current Status",
                    lambda x: sum(
                        status is not None
                        and ("open" in status.lower() or "proposed" in status.lower())
                        for status in x
                    ),
                ),
                "Fulfilled": (
                    "Current Status",
                    lambda x: sum(
                        status is not None and status.lower() == "fulfilled"
                        for status in x
                    ),
                ),
                "To be Onboarded": (
                    "Current Status",
                    lambda x: sum(
                        status is not None and status.lower() == "to be onboarded"
                        for status in x
                    ),
                ),
                "Requirement Ids": ("Id", lambda x: {"results": list(x)}),
                "Current Statuses": (
                    "Current Status",
                    lambda x: "\n".join([str(i) if i is not None else 'Not Present' for i in x]),
                ),
                "Billing Start Dates": (
                    "Billing Start date",
                    lambda x: "\n".join(
                        [
                            datetime.strftime(datetime.fromisoformat(i), "%B %d, %Y")
                            for i in x
                            if i is not None
                        ]
                    ),
                ),
                "Project Types": (
                    "Project Type",
                    lambda x: "\n".join([str(i) for i in x if i is not None]),
                ),
                "Customer Evaluation Required": (
                    "Customer Evaluation Required",
                    lambda x: "\n".join(str(i) for i in x if i is not None),
                ),
            }
        ).reset_index()

        first_occurrence = df.drop_duplicates(
            subset=["Mandatory Skill_lower", "Onsite/ Offshore_lower"]
        )
        report_data = aggregated_df.merge(
            first_occurrence[
                [
                    "Mandatory Skill_lower",
                    "Onsite/ Offshore_lower",
                    "Mandatory Skill",
                    "Onsite/ Offshore",
                ]
            ],
            on=["Mandatory Skill_lower", "Onsite/ Offshore_lower"],
        )

        report_data.drop(
            columns=["Mandatory Skill_lower", "Onsite/ Offshore_lower"], inplace=True
        )

        return report_data

    # def generate_report_v2(self, simplified_list):
    #     df = pd.DataFrame(simplified_list)
    #     report_columns = [
    #         "Mandatory Skill",
    #         "Open Requirements",
    #         "Fulfilled",
    #         "Onsite",
    #         "Offshore",
    #         "To be Onboarded",
    #         "Requirement Ids",
    #         "Billing Start Dates",
    #         "Project Types",
    #     ]
    #     grouped = df.groupby(["Mandatory Skill", "Onsite/ Offshore"])
    #     aggregated = grouped.agg(
    #         **{
    #             "Open Requirements": (
    #                 "Current Status",
    #                 lambda x: sum(
    #                     status is not None and status and "open" in status.lower()
    #                     for status in x
    #                 ),
    #             ),
    #             "Fulfilled": (
    #                 "Current Status",
    #                 lambda x: sum(
    #                     status is not None and status and status.lower() == "fulfilled"
    #                     for status in x
    #                 ),
    #             ),
    #             "To be Onboarded": (
    #                 "Current Status",
    #                 lambda x: sum(
    #                     status is not None and status.lower() == "to be onboarded"
    #                     for status in x
    #                 ),
    #             ),
    #         }
    #     )

    #     def get_details(group):
    #         return group[
    #             [
    #                 "Requirement Id",
    #                 "Billing Start date",
    #                 "Project Type",
    #                 "Customer Evaluation Required",
    #             ]
    #         ].to_dict(orient="records")

    #     details = grouped.apply(get_details, include_groups=False).reset_index(
    #         name="Details"
    #     )
    #     report_data = pd.merge(
    #         aggregated.reset_index(),
    #         details,
    #         on=["Mandatory Skill", "Onsite/ Offshore"],
    #     )

    #     return report_data

    def prepare_report_data(self, report_data: pd.DataFrame):
        insert_list = []
        report_columns = report_data.columns.values.tolist()
        for _, row in report_data.iterrows():
            payload = {}
            for column in report_columns:
                payload[
                    self.required_columns.get(column, {}).get("Internal Name", None)
                ] = row[column]
            insert_list.append(payload)

        return insert_list

class AlertReport(SharePointConnector):
    def __init__(self, source_site, destination_site, cookie_dict, report_list):
        super().__init__(source_site, destination_site, cookie_dict)
        self.report_list = report_list
        self.required_columns = ListOperations.get_required_columns(
            self.source_site, self.report_list, self.session
        )
        

    def generate_report(self, df:pd.DataFrame) -> pd.DataFrame:
        report = None

        if self.report_list == "Pending Updates Report":
            report = df[
                df["View Appearing In"].str.lower() == "to be updated"
            ][
                ["Requirement Id", "Location", "Requestor Employee Name"]
            ].reset_index(drop=True)

        elif self.report_list == "Onboarding Status Report":
            report = df[
                df["Current Status"].str.lower() == "to be onboarded"
            ][
                ["Requirement Id", "DM Name", "Emp ID"]
            ].reset_index(drop=True)

        elif self.report_list == "Delayed Onboarding Report":
            now = datetime.now()
            threshold_date = now - timedelta(days=3)

            report = df[
                (df["Current Status"].str.lower() == 'to be onboarded') &
                (df["Modified"] < threshold_date)
            ][["Requirement Id", "DM Name", "Emp ID"]].reset_index(drop=True)

        elif self.report_list == "Duplicate RGS Report":
            def find_dup_rgs(remark):
                if not remark:
                    return None
                pattern = re.compile(r'\b(duplicate|duplicate rgs|dup rgs|dup rg|duplicate rg)\b', re.IGNORECASE)
                if pattern.search(remark):
                    id_pattern = re.compile(r'\b9\d{5,}\b')
                    match = id_pattern.search(remark)
                    if match:
                        return int(match.group(0))
                    return 'No RGS ID Found'
                return None
            
            df["New RGS ID"] = df["Remarks   from   Project     team"].apply(find_dup_rgs)
            report = df[
                (df["Current Status"].str.lower().isin(["closed", "cancelled"]) == False) & 
                (df["New RGS ID"].notnull())
            ][
                ["Requirement Id", "Current Status", "New RGS ID", "Remarks   from   Project     team"]
            ].reset_index(drop=True)
            
        return report

    def prepare_data(self, df:pd.DataFrame, bg_list_id_mapping:dict, list_column_mapping:dict) -> list:
        insert_list = []
        for _, row in df.iterrows():
            report_columns = df.columns.values.tolist()
            payload = {}
            for column in report_columns:
                mapping_data = list_column_mapping.get(column, {})
                column_internal_name = mapping_data.get("Internal Name", None)
                column_data_type = mapping_data.get("Data Type", None)
                if "requirement id" in column.lower() or "rgs id" in column.lower():
                    new_requirement_id = row[column]
                    if isinstance(new_requirement_id, int):
                        payload[column_internal_name] = bg_list_id_mapping[new_requirement_id]
                else:
                    value = row[column]
                    if column_data_type == "Text":
                        if not isinstance(value, str):
                            value = str(value)
                        else:
                            if not value or 'na' in value.lower() or 'n/a' in value.lower() or value == '0':
                                value = "Not Available"
                    elif column_data_type == 'Number':
                        if value:
                            if not isinstance(value, int) or not isinstance(value, float):
                                value = int(value)
                    payload[column_internal_name] = value

            insert_list.append(payload)
        return insert_list
