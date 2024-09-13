import time
from collections import Counter as counter
from utils.methods import Utils
from connector.sharepoint_connector import SharePointConnector


class SharePointOperations(SharePointConnector):
    def __init__(
        self,
        source_site,
        destination_site,
        source_list,
        destination_list,
        cookie_dict,
        temp_folder,
    ):
        super().__init__(
            source_site=source_site,
            destination_site=destination_site,
            cookie_dict=cookie_dict,
        )
        self.source_list = source_list
        self.destination_list = destination_list
        self.temp_folder = temp_folder
        self.data_type_property = "ListItemEntityTypeFullName"
        self.primary_key = "Requirement Id"
        self.destination_list_item_data_type = None
        

    def get_list_items(self, site_url, list_name, query=None):
        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/items"
        if query:
            endpoint += query

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
                self.logger.critical("List not found! Please double check your list name.")
                exit()
            else:
                print("Something went wrong!")
            time.sleep(2)
        items_retrieved = len(all_items)
        self.logger.success("Total %s items retrieved", items_retrieved)
        return all_items

    def get_required_columns(self, site_url, list_name):
        required_cols = {}
        required_cols["Id"] = {}

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"

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
            if internal_name not in ['ContentType']:
                required_cols[title] = {"Internal Name": internal_name, "Data Type": data_type}     
        required_cols["Modified"] = {}
        required_cols["Attachment List"] = {}

        return required_cols

    def get_list_property(self, site_url, list_name, property_name):
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }

        response = self.session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        list_property =  data.get("d", {}).get(property_name, None)
        self.destination_list_item_data_type = list_property
        return list_property

    def get_attachments(self, site_url, list_name, item_id):
        attachemnt_list = []
        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/Items({item_id})/AttachmentFiles"
        response = self.session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        attachments = data.get("d", {}).get("results", [])
        for attachemnt in attachments:
            filename = attachemnt["FileName"]
            attachemnt_list.append(filename)
        return attachemnt_list

    def get_field_mappings(self, site_url, list_name):
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }

        response = self.session.get(endpoint, headers=headers)
        data = response.json()
        fields = data.get("d", {}).get("results", [])

        field_mappings = {field["Title"]: field["InternalName"] for field in fields}
        return field_mappings

    def download_attachments(self, site_url, list_name, item_id, attachment_list):
        headers = {"Accept": "application/json; odata=verbose"}
        for filename in attachment_list:
            endpoint = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/Items({item_id})/AttachmentFiles('{filename}')/$value"
            response = self.session.get(endpoint, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                with open(f"{self.temp_folder}\\{filename}", "wb") as f:
                    f.write(response.content)
            else:
                print(response.status_code)

    def delete_item(self, site_url, list_name, item_id):
        request_digest = self.destination_site_digest_value
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest,
            "IF-MATCH": "*",
            "X-HTTP-Method": "DELETE"
        }
        response = self.session.post(
                    f"{site_url}/_api/web/lists/getbytitle('{list_name}')/Items({item_id})",
                    headers=headers
                )
        response.raise_for_status()


    def upload_attachments(self, site_url, list_name, item_id, attachment_list):
        request_digest = self.destination_site_digest_value
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest,
        }
        attachments_to_be_uploaded = len(attachment_list)

        for filename in attachment_list:
            self.logger.info(
                "Attachments left for insertion %s", attachments_to_be_uploaded
            )
            with open(f"{self.temp_folder}\\{filename}", "rb") as f:
                response = self.session.post(
                    f"{site_url}/_api/web/lists/getbytitle('{list_name}')/Items({item_id})/AttachmentFiles/add(FileName='{filename}')",
                    headers=headers,
                    data=f,
                )
                response.raise_for_status()
            if response.status_code != 200:
                self.logger.error("Failed to upload %s", filename)
            else:
                self.logger.success("Uploaded attachment %s", filename)
            attachments_to_be_uploaded -= 1

    def delete_attachments(self, site_url, list_name, item_id, attachment_list):
        request_digest = self.destination_site_digest_value

        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "IF-MATCH": "*",
            "X-HTTP-Method": "DELETE",
            "X-RequestDigest": request_digest,
        }
        for filename in attachment_list:
            response = self.session.post(
                f"{site_url}/_api/web/lists/getbytitle('{list_name}')/Items({item_id})/AttachmentFiles('{filename}')",
                headers=headers,
            )
            response.raise_for_status()
            if not response.status_code == 200:
                self.logger.error("Failed to delete old attachment %s", filename)
            else:
                self.logger.success("Successfully deleted old attachment %s", filename)

    def create_simplified_list(self, site_url, list_name, list_data, required_cols):
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
                elif col == "Attachment List":
                    attachemts = []
                    if row["Attachments"]:
                        attachemts = self.get_attachments(
                            site_url=site_url, list_name=list_name, item_id=row_id
                        )
                        time.sleep(2)
                    list_item_dict["Attachment List"] = attachemts
                else:
                    list_item_dict[col] = row[required_cols[col]["Internal Name"]]
            items_list.append(list_item_dict)
        return items_list

    def insert_list_items(self, insert_items_list, required_source_cols):
        request_digest = self.destination_site_digest_value
        if not self.destination_list_item_data_type:
            list_item_data_type = self.get_list_property(
                self.destination_site, self.destination_list, self.data_type_property
            )
        else:
            list_item_data_type = self.destination_list_item_data_type

        time.sleep(1)
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest,
        }
        payload = {"__metadata": {"type": list_item_data_type}}

        items_to_be_inserted = len(insert_items_list)
        self.logger.info("Starting insertion...")

        if items_to_be_inserted % 100 == 0:
            self.logger.info('Waiting for some time to avoid MS timeout')
            time.sleep(30)

        for item in insert_items_list:
            if items_to_be_inserted % 10 == 0:
                self.logger.info("Items left for insertion %s", items_to_be_inserted)
            for key, value in item.items():
                if key not in ["Id", "Attachment List", "Modified"]:
                    payload[key] = value
            response = self.session.post(
                f"{self.destination_site}/_api/web/lists/getbytitle('{self.destination_list}')/items",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            time.sleep(2)

            title = item[required_source_cols[self.primary_key]["Internal Name"]]
            list_a_item_id = item["Id"]
            attachment_list = item["Attachment List"]

            data = response.json()
            list_b_item_id = data.get("d", {}).get("Id", None)

            if response.status_code == 201:
                self.logger.success("Successfully inserted item %s", title)
                if item["Attachments"]:
                    self.logger.info("Attachment(s) found in item %s", title)
                    self.download_attachments(
                        self.source_site, self.source_list, list_a_item_id, attachment_list
                    )

                    self.logger.info("Attempting to copy attachments...")

                    self.upload_attachments(
                        self.destination_site, self.destination_list, list_b_item_id, attachment_list
                    )
                    Utils.clear_folder(self.temp_folder)
            # print(response.json())
            if response.status_code != 201:
                self.logger.error("Failed to insert item %s", title)

            items_to_be_inserted -= 1

        self.logger.success("Insertion completed.")

    def update_list_items(self, update_list, second_list_contents, required_source_cols):
        request_digest = self.destination_site_digest_value

        if not self.destination_list_item_data_type:
            list_item_data_type = self.get_list_property(
            self.destination_site, self.destination_list, self.data_type_property
        )
        else:
            list_item_data_type = self.destination_list_item_data_type
        
        time.sleep(1)
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "IF-MATCH": "*",
            "X-HTTP-Method": "MERGE",
            "X-RequestDigest": request_digest,
        }
        payload = {"__metadata": {"type": list_item_data_type}}

        items_to_be_updated = len(update_list)
        self.logger.info("Starting update...")

        if items_to_be_updated % 100 == 0:
            self.logger.info('Waiting for some time to avoid MS timeout')
            time.sleep(30)

        for item in update_list:
            if items_to_be_updated % 10 == 0:
                self.logger.info("Items left for update: %s", items_to_be_updated)
            for key, value in item.items():
                if key not in ["Id", "Attachment List", "Modified"]:
                    payload[key] = value
            
            title = item[required_source_cols[self.primary_key]["Internal Name"]]
            source_list_item_id = item["Id"]
            source_list_attachments = item["Attachment List"]

            second_list_item = [i for i in second_list_contents if i[self.primary_key] == title][0]
            destination_list_item_id = second_list_item["Id"]
            destination_list_attachments = second_list_item["Attachment List"]

            response = self.session.post(
                f"{self.destination_site}/_api/web/lists/getbytitle('{self.destination_list}')/items({destination_list_item_id})",
                headers=headers,
                json=payload,   
            )
            response.raise_for_status()
            time.sleep(2)

            if response.status_code == 204:
                self.logger.success("Successfully updated item %s", title)
                compare = lambda x, y: counter(x) == counter(y)
                if not compare(source_list_attachments, destination_list_attachments):
                    self.logger.info("New attachment(s) found in item %s", title)
                    self.download_attachments(
                        self.source_site, self.source_list, source_list_item_id, source_list_attachments
                    )

                    if second_list_item["Attachments"]:
                        self.logger.info("Attempting to delete existing attachment(s)")
                        self.delete_attachments(
                            self.destination_site, self.destination_list,destination_list_item_id, destination_list_attachments
                        )

                    self.logger.info("Attempting to copy new attachments...")

                    self.upload_attachments(
                        self.destination_site, self.destination_list, destination_list_item_id, destination_list_attachments
                    )
                    Utils.clear_folder(self.temp_folder)

            if response.status_code != 204:
                print(f"Failed to add item: {response.content}")
