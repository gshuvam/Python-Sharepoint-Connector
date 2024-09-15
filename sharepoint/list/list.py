import time
from logger.custom_logger import get_logger
from connector.sharepoint_connector import SharePointConnector
from sharepoint.common.sharepoint_operations import SharePointOperations

class BaseList:
    """
    The `BaseList` class is responsible for interacting with SharePoint lists. It retrieves metadata, list properties, and required columns, while maintaining the session and digest information needed for operations with SharePoint. This class is a foundational class for handling basic SharePoint list operations, such as fetching list items and metadata.

    Attributes:
        - site_url (str): The base URL of the SharePoint site.
        - list_name (str): The name of the SharePoint list.
        - session (requests.Session): An authenticated session for interacting with SharePoint.
        - digest_value (str): The form digest value required for authenticated SharePoint operations.
        - list_item_dtype_property_name (str): The property name used to identify the data type of list items.
        - list_data_type (str): The data type of the list items retrieved using the `list_item_dtype_property_name`.
        - column_datatypes (dict): A dictionary containing internal names and data types for the columns of the list.
        - logger: A logger instance for logging information and errors.

    Methods:
        - get_list_items(query=None) -> list
        - get_list_property(property_name) -> str
        - get_required_columns() -> dict[dict]
        - __get_column_datatypes() -> dict
    """

    def __init__(
        self,
        site_url: str,
        list_name: str,
        sharepoint_connector_object: SharePointConnector,
    ):
        """
        Initializes the `BaseList` class with the necessary information to interact with a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site where the list is hosted.
            - list_name (str): The name of the SharePoint list.
            - sharepoint_connector_object (SharePointConnector): An instance of `SharePointConnector`, which provides an authenticated session and digest value.

        This constructor initializes the following:
            - `site_url`: The SharePoint site URL.
            - `list_name`: The name of the SharePoint list.
            - `session`: The authenticated session object retrieved from the `SharePointConnector`.
            - `digest_value`: The form digest value for authenticated SharePoint requests.
            - `list_item_dtype_property_name`: Set to "ListItemEntityTypeFullName", used to retrieve list item data type.
            - `list_data_type`: The data type of the list items retrieved by the `get_list_property` method.
            - `column_datatypes`: A dictionary containing the internal names and data types for the list's columns.
            - `logger`: An instance of the logger for logging.
        """

        self.site_url = site_url
        self.list_name = list_name
        self.session = sharepoint_connector_object.session
        self.digest_value = sharepoint_connector_object.digest_value
        self.list_item_dtype_property_name = "ListItemEntityTypeFullName"
        self.list_data_type = self.get_list_property(self.list_item_dtype_property_name)
        self.column_datatypes = self.__get_column_datatypes()
        self.logger = get_logger(self.__class__.__name__)

    def get_list_items(self, query=None) -> list:

        """
        Retrieves the items from the SharePoint list. Optionally, a query can be provided to filter the items.

        Parameters:
            - query (optional): A query string used to filter the list items (e.g., CAML or OData queries).

        Returns:
            - list: A list of SharePoint list items, optionally filtered by the query.

        Notes:
            - The returned list items may contain metadata and actual data from the SharePoint list.
            - If no query is provided, all list items will be retrieved.
        """

        endpoint = (
            f"{self.site_url}_api/web/lists/getbytitle('{self.list_name}')/items"
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

    def get_list_property(self, property_name) -> str:

        """
        Retrieves a specific property value for the SharePoint list.

        Parameters:
            - property_name (str): The name of the list property to retrieve.

        Returns:
            - str: The value of the specified list property.

        Example:
            - To retrieve the data type of the list items, use:
              `get_list_property("ListItemEntityTypeFullName")`.
        """

        endpoint = f"{self.site_url}_api/web/lists/getbytitle('{self.list_name}')"
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

        """
        A private method that retrieves the internal names and data types for all columns in the SharePoint list.

        Returns:
            - dict: A dictionary with column titles as keys, and the values being a dictionary containing the internal name and data type of each column.

        Example:
        ```
        {
            'Id': {}
            'Title': {
                'Internal Name': 'Title',
                'Data Type': 'Text',
            },
            'Created': {
                'Internal Name': 'Created',
                'Data Type': 'DateTime',
            }
        }
        ```
        Notes:
            - This method is automatically called during the initialization of the `BaseList` class.
            - It is a private method and is not intended to be called directly.
        """

        required_cols = {}
        required_cols["Id"] = {}

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{self.site_url}_api/web/lists/getbytitle('{self.list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"

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

    def __get_column_datatypes(self) -> dict:

        """
        A private method that retrieves the internal names and data types for all columns in the SharePoint list.

        Returns:
            - dict: A dictionary with column titles as keys, and the values being a dictionary containing the internal name and data type of each column.

        Example:
        ```
        {
            'Title': {
                'Internal Name': 'Title',
                'Data Type': 'Text',
            },
            'Created': {
                'Internal Name': 'Created',
                'Data Type': 'DateTime',
            }
        }
        ```
        Notes:
            - This method is automatically called during the initialization of the `BaseList` class.
            - It is a private method and is not intended to be called directly.
        """

        required_cols = {}

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{self.site_url}_api/web/lists/getbytitle('{self.list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"

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

    """
    The `List` class is an extension of the `BaseList` class that adds functionality for handling more complex data operations on a SharePoint list. This includes preparing data, inserting new items, updating existing items, and deleting items in batches. It also manages column name mappings and can be configured with a primary column for identifying items.

    Attributes:
        - site_url (str): The base URL of the SharePoint site.
        - list_name (str): The name of the SharePoint list.
        - primary_column (str): The primary column used to identify list items, default is 'Title'.
        - batch_size (int): The size of the batch for insert, update, and delete operations.
        - column_name_mappings (dict): A dictionary mapping the internal column names to their display names.
        - session (requests.Session): An authenticated session for interacting with SharePoint.
        - digest_value (str): The form digest value required for authenticated SharePoint operations.
        - list_data_type (str): The data type of the list items.
        - logger: A logger instance for logging information and errors.

    Methods:
        - prepare_data(insert_list: list) -> list
        - insert_items(insert_list: list[dict]) -> None
        - update_list_items(update_list: list[dict[str, dict]], attachment_upload_mode: str='UPDATE') -> None
        - delete_list_items(delete_list: list[dict]) -> None
        - __get_column_name_mappings() -> dict
    """

    def __init__(self, site_url: str, list_name: str, sharepoint_connector_object: SharePointConnector, primary_column='Title', batch_size=50):
        
        """
        Initializes the `List` class with additional features for handling complex operations on SharePoint lists.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - sharepoint_connector_object (SharePointConnector): An instance of `SharePointConnector` providing session and digest value.
            - primary_column (str, optional): The primary column used to identify list items, default is 'Title'.
            - batch_size (int, optional): The batch size for insert, update, and delete operations, default is 50.

        This constructor initializes the following:
            - `site_url`: The SharePoint site URL.
            - `list_name`: The name of the SharePoint list.
            - `session`: The authenticated session object from `SharePointConnector`.
            - `digest_value`: The form digest value for authenticated SharePoint requests.
            - `primary_column`: The primary column used to identify list items.
            - `batch_size`: The size of batches for insert, update, and delete operations.
            - `column_name_mappings`: A dictionary containing internal and display name mappings for the list columns.
        """
        
        super().__init__(site_url, list_name, sharepoint_connector_object)
        self.column_name_mappings = self.__get_column_name_mappings()
        self.primary_column = primary_column
        self.batch_size = batch_size

    def __get_column_name_mappings(self) -> dict:
        
        """
        Retrieves and returns a dictionary of the column name mappings for the SharePoint list.

        Returns:
            - dict: A dictionary where the keys are internal column names and the values are display names.

        Example:
            ```
            {
                'Title': 'Title',
                'Created': 'Created',
                'Modified': 'Modified'
            }
            ```

        Notes:
            - This method is private and is used internally by the `List` class.
            - It maps the internal column names to their respective display names for easier reference.
        """
        
        endpoint = f"{self.site_url}_api/web/lists/getbytitle('{self.list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"
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
        
        """
        Prepares data for insertion by mapping the provided data to the SharePoint list's columns.

        Parameters:
            - insert_list (list): A list of dictionaries containing the data to be inserted, where each dictionary represents a row.

        Returns:
            - list: A prepared list of dictionaries with proper column mappings and structure, ready to be inserted into the SharePoint list.

        Example:
            ```
            [
                {
                    'Title': 'New Item 1',
                    'Description': 'Description of item 1'
                },
                {
                    'Title': 'New Item 2',
                    'Description': 'Description of item 2'
                }
            ]
            ```
        Notes:
            - This method uses `column_name_mappings` to ensure the data is structured correctly before being inserted.
        """
        
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

        """
        Inserts items into the SharePoint list in batches.

        Parameters:
            - insert_list (list[dict]): A list of dictionaries where each dictionary represents the data of an item to be inserted.

        Returns:
            - None: This method doesn't return anything but performs batch insert operations into the SharePoint list.

        Example:
            ```
            insert_list = [
                {'Title': 'Item 1', 'Description': 'Description 1'},
                {'Title': 'Item 2', 'Description': 'Description 2'}
            ]
            ```

        Notes:
            - The `batch_size` parameter determines how many items are inserted in one batch.
            - The method handles batch processing, ensuring that multiple items are inserted efficiently.
        """

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
                f"{self.site_url}_api/web/lists/getbytitle('{self.list_name}')/items",
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


    def update_list_items(self, update_list: list[dict[str, dict]], attchment_upload_mode:str='UPDATE') -> None:
        
        """
        Updates existing items in the SharePoint list.

        Parameters:
            - update_list (list[dict[str, dict]]): A list of dictionaries where each dictionary contains an item to be updated, including the item ID and updated values.
            - attachment_upload_mode (str, optional): Mode for handling attachments during updates. Defaults to 'UPDATE'.

        Returns:
            - None: This method doesn't return anything but performs batch update operations on the SharePoint list.

        Example:
        ```
        update_list = [
            {'id1': {'Title': 'Updated Title 1', 'Description': 'Updated Description 1'}},
            {'id2': {'Title': 'Updated Title 2', 'Description': 'Updated Description 2'}}
        ]
        ```

        Notes:
            - The `attachment_upload_mode` parameter allows specifying how attachments are handled during updates.
            - The method processes updates in batches based on the `batch_size` attribute.
        """
        
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
                f"{self.site_url}_api/web/lists/getbytitle('{self.list_name}')/items({item_id})",
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
                self.logger.error(f"Failed to add item: {response.content}")

    def delete_list_items(self, delete_list:list[dict]) -> None:

        """
        Deletes items from the SharePoint list in batches.

        Parameters:
            - delete_list (list[dict]): A list of dictionaries where each dictionary contains the ID of the item to be deleted.

        Returns:
            - None: This method doesn't return anything but performs batch delete operations on the SharePoint list.

        Example:
            delete_list = [
                {'ID': 1},
                {'ID': 2}
            ]

        Notes:
            - The `batch_size` parameter determines how many items are deleted in one batch.
            - This method handles batch processing, ensuring efficient deletion of multiple items.
        """

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
                f"{self.site_url}_api/web/lists/getbytitle('{self.list_name}')/Items({item_id})",
                headers=headers
            )
            response.raise_for_status()
            time.sleep(2)
            total_items_to_delete -= 1
