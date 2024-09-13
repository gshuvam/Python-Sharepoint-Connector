import logging
import time
import json
import requests
import pandas as pd
from requests import Session


class ListOperations:
    @staticmethod
    def get_required_columns(
        site_url: str, list_name: str, session: requests.Session
    ) -> dict[dict]:
        required_cols = {}
        required_cols["Id"] = {}

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"

        response = session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        columns_info = data.get("d", {}).get("results", [])
        for column in columns_info:
            title = column["Title"]
            internal_name = column["EntityPropertyName"]
            data_type = column["TypeAsString"]
            if column["FieldTypeKind"] in [20, 7]:
                internal_name += "Id"
            if internal_name not in ["ContentType"]:
                required_cols[title] = {
                    "Internal Name": internal_name,
                    "Data Type": data_type,
                }

        return required_cols

    @staticmethod
    def get_list_property(
        site_url: str, list_name: str, session: requests.Session, property_name: str
    ) -> str:
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }

        response = session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        output = data.get("d", {}).get(property_name, None)
        time.sleep(0.5)
        return output

    @staticmethod
    def get_list_data_type(site_url: str, list_name: str, session: Session):
        list_item_data_type = ListOperations.get_list_property(
            site_url=site_url,
            list_name=list_name,
            session=session,
            property_name="ListItemEntityTypeFullName",
        )

        return list_item_data_type

    @staticmethod
    def get_list_items(
        site_url: str, list_name: str, session: requests.Session, logger: logging.Logger
    ) -> list[dict]:
        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/items"

        all_items = []
        while endpoint:
            response = session.get(endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()
            if response.status_code == 200:
                items = data.get("d", {}).get("results", [])
                all_items.extend(items)

                endpoint = data.get("d", {}).get("__next", None)
            elif response.status_code == 404:
                logger.critical("List not found! Please double check your list name.")
                exit()
            else:
                print("Something went wrong!")
            time.sleep(2)
        items_retrieved = len(all_items)
        if items_retrieved > 0:
            logger.success("Total %s items retrieved", items_retrieved)
        else:
            logger.success("No items in the list.")
        return all_items

    @staticmethod
    def create_simplified_list(list_data: list, required_cols: dict) -> list[dict]:
        items_list = []
        for row in list_data:
            list_item_dict = {}
            column_display_names = list(required_cols.keys())
            for col in column_display_names:
                # adding Id
                if col == "Id":
                    row_id = row["Id"]
                    list_item_dict["Id"] = row_id
                # adding attachments
                elif col == "Modified":
                    list_item_dict["Modified"] = row["Modified"]
                else:
                    list_item_dict[col] = row[required_cols[col]["Internal Name"]]
            items_list.append(list_item_dict)
        return items_list

    @staticmethod
    def prepare_data(
        source_data: dict, column_mappings: dict, old_id: int = None
    ) -> dict:
        data = {}
        if old_id:
            data["Old_Id"] = old_id
        for key, value in source_data.items():
            data[column_mappings.get(key, {}).get("Internal Name", None)] = value
        return data

    @staticmethod
    def insert_items(insert_list):
        request_digest = self.digest_value
        time.sleep(1)
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest,
        }
        items_to_be_inserted = len(insert_list)
        self.logger.info("Starting insertion...")

        processed_insert_list = self.prepare_data(insert_list)

        for item in processed_insert_list:
            idetifier = item["Title"]
            payload = {"__metadata": {"type": self.list_item_data_type}}

            if items_to_be_inserted % 100 == 0:
                self.logger.info("Waiting for some time to avoid MS timeout")
                time.sleep(30)
            if items_to_be_inserted % 10 == 0:
                self.logger.info("Items left for insertion %s", items_to_be_inserted)

            for key, value in item.items():
                payload[key] = value

            response = self.session.post(
                f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            time.sleep(2)
            self.logger.success("Successfully inserted item %s", idetifier)
            if response.status_code != 201:
                self.logger.error("Unable to add item %s", response.json())
            items_to_be_inserted -= 1
