import time
import requests
from connector.sharepoint_connector import SharePointConnector
from sharepoint_operations import SharePointOperations

class BaseList:

    '''
    ### Methods - 
    * get_list_items(self, query=None)
    * get_list_property(self, property_name)
    * get_required_columns(self)
    * __get_column_datatypes(self)
    '''

    def __init__(
        self,
        site_url: str,
        list_name: str,
        sharepoint_connector_object: SharePointConnector,
    ):
        self.site_url = (site_url,)
        self.list_name = (list_name,)
        self.session = sharepoint_connector_object.session
        self.digest_value = sharepoint_connector_object.digest_value
        self.list_item_dtype_property_name = "ListItemEntityTypeFullName"
        self.list_data_type = self.get_list_property(self.list_item_property_name)
        self.column_datatypes = self.__get_column_datatypes()

    def get_list_items(self, query=None) -> list:
        endpoint = (
            f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items"
        )
        if query:
            endpoint += query
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }

        all_items = []
        while endpoint:
            response = self.session.get(endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()
            if response.status_code == 200:
                items = data.get("d", {}).get("results", [])
                all_items.extend(items)

                endpoint = data.get("d", {}).get("__next", None)
            elif response.status_code == 404:
                self.logger.critical(
                    "List not found! Please double check your list name."
                )
                exit()
            else:
                self.logger.critical("Something went wrong!")
            time.sleep(2)
        items_retrieved = len(all_items)
        self.logger.success("Total %s items retrieved from the List", items_retrieved)

        return all_items

    def get_list_property(self, property_name):
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }

        response = self.session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        output = data.get("d", {}).get(property_name, None)
        time.sleep(0.5)

        return output

    def get_required_columns(self) -> dict[dict]:
        required_cols = {}
        required_cols["Id"] = {}

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"

        response = self.session.get(endpoint, headers=headers)
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

    def __get_column_datatypes(self):
        required_cols = {}

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"

        response = self.session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        columns_info = data.get("d", {}).get("results", [])
        for column in columns_info:
            title = column["Title"]
            internal_name = column["EntityPropertyName"]
            data_type = column["TypeAsString"]
            if column["FieldTypeKind"] == 20:
                internal_name += "Id"
            if internal_name not in ["ContentType"]:
                required_cols[title] = {
                    "Internal Name": internal_name,
                    "Data Type": data_type,
                }
        time.sleep(0.5)

        return required_cols


class List(BaseList):
    def __init__(self, site_url: str, list_name: str, session: requests.Session, primary_column='Title', batch_size=50):
        super().__init__(site_url, list_name, session)
        self.column_name_mappings = self.__get_column_name_mappings()
        self.primary_column = primary_column
        self.batch_size = batch_size

    def __get_column_name_mappings(self) -> dict:
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }

        response = self.session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()

        fields = data.get("d", {}).get("results", [])
        field_mappings = {field["Title"]: field["InternalName"] for field in fields}
        time.sleep(0.5)
        return field_mappings

    def prepare_data(self, insert_list: list) -> list:
        processed_insert_list = []
        for item in insert_list:
            processed_item_dict = {}
            for key, value in item.items():
                data_type = self.list_field_dict[key]["Data Type"]
                internal_name = self.list_field_dict[key]["Internal Name"]

                if data_type == "Text":
                    if not isinstance(value, str):
                        value = str(value)
                elif data_type == "Number":
                    if not isinstance(value, int) or not isinstance(value, float):
                        try:
                            value = float(value)
                        except ValueError:
                            value = None
                elif data_type == "DateTime":
                    pass
                elif data_type == "Choice":
                    pass
                elif data_type == "Attachments":
                    pass
                else:
                    pass
                if value is not None:
                    processed_item_dict[internal_name] = value
            processed_insert_list.append(processed_item_dict)
        return processed_insert_list

    def insert_items(self, insert_list: list[dict]) -> None:
        request_digest = self.digest_value
        required_columns = self.get_required_columns()

        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest,
        }
        items_to_be_inserted = len(insert_list)
        self.logger.info("Starting insertion...")
        self.logger.info("Items left for insertion: %s", len(insert_list))

        for item_data in insert_list:
            idetifier = item_data[required_columns[self.primary_column]["Internal Name"]]
            attachment_list = item_data.get("Attachment List", None)

            payload = {"__metadata": {"type": self.list_item_data_type}}

            if items_to_be_inserted % self.batch_size == 0:
                self.logger.info("Waiting for some time to avoid MS timeout")
                time.sleep(30)

            if items_to_be_inserted % 10 == 0:
                self.logger.info("Items left for insertion %s", items_to_be_inserted)

            for key, value in item_data.items():
                if key not in ["Id", "Attachment List", "Modified"]:
                    payload[key] = value

            response = self.session.post(
                f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            item_id = response.json().get("d", {}).get("Id", None)
            time.sleep(2)

            if response.status_code != 201:
                self.logger.error("Unable to add item %s", idetifier)
                self.logger.error("Error details: %s", response.json())

            #Uploading attachments (if applicable)
            if attachment_list:
                self.logger.info("Attempting to upload attachments...")
                SharePointOperations.upload_attachments(
                    self.site_url, self.list_name, item_id, attachment_list
                )
            items_to_be_inserted -= 1


    '''
    update_list = [
        { 
            'id': {
                'key1': 'value1',
            }
        },
    ]
    '''
    def update_list_items(self, update_list: list[dict[str, dict]], attchment_upload_mode:str='UPDATE') -> None:
        request_digest = self.digest_value
        required_columns = self.get_required_columns()
        if not self.list_item_data_type:
            list_item_data_type = self.get_list_property(
                self.list_item_dtype_property_name
            )
        else:
            list_item_data_type = self.list_item_data_type

        time.sleep(1)
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "IF-MATCH": "*",
            "X-HTTP-Method": "MERGE",
            "X-RequestDigest": request_digest,
        }
        payload = {
            "__metadata": {
                "type": list_item_data_type
            }
        }

        items_to_be_updated = len(update_list)
        self.logger.info("Starting update...")

        for item in update_list:
            item_id = None
            item_data = None
            
            if items_to_be_updated % self.batch_size == 0:
                self.logger.info("Waiting for some time to avoid MS timeout")
                time.sleep(30)

            if items_to_be_updated % 10 == 0:
                self.logger.info("Items left for update: %s", items_to_be_updated)

            for k, v in item.items():
                item_id = k
                item_data = v
                for key, value in item_data.items:
                    if key not in ["Id", "Attachment List", "Modified"]:
                        payload[key] = value

            title = item_data[required_columns[self.primary_column]["Internal Name"]]
            item_attachments = item_data.get("Attachment List", None)

            response = self.session.post(
                f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items({item_id})",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            time.sleep(2)

            if response.status_code == 204:
                self.logger.success("Successfully updated item %s", title)
                if item_attachments:
                    self.logger.info("New attachment(s) found in item %s", title)

                    if attchment_upload_mode == 'REPLACE':
                        self.logger.info("Attempting to delete existing attachment(s)")
                        SharePointOperations.delete_attachments(
                            self.site_url,
                            self.list_name,
                            item_id
                        )

                    self.logger.info("Attempting to upload new attachments...")
                    SharePointOperations.upload_attachments(
                        self.site_url,
                        self.list_name,
                        item_id,
                        attachment_list=item_attachments
                    )

            if response.status_code != 204:
                print(f"Failed to add item: {response.content}")

    def delete_list_items(self, delete_list:list[dict]) -> None:
        request_digest = self.digest_value
        total_items_to_delete = len(delete_list)

        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest,
            "IF-MATCH": "*",
            "X-HTTP-Method": "DELETE"
        }

        self.logger.info('Starting deletion...')
        for item in delete_list:
            item_id = item['Id']

            if total_items_to_delete % self.batch_size == 0:
                self.logger.info("Waiting for some time to avoid MS timeout")
                time.sleep(30)

            if total_items_to_delete % 10 == 0:
                self.logger.info("Items left for update: %s", total_items_to_delete)

            response = self.session.post(
                f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/Items({item_id})",
                headers=headers
            )
            response.raise_for_status()
            time.sleep(2)
            total_items_to_delete -= 1
