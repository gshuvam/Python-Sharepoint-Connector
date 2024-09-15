import time
import requests
from requests import Session
from logger.custom_logger import get_logger


class ListOperations:

    """
    ListOperations

    The `ListOperations` class provides static utility methods for interacting with SharePoint lists. These methods include retrieving list properties, data types, items, and column mappings, as well as preparing data for operations and simplifying list structures.

    Static Methods:
        - get_required_columns(site_url: str, list_name: str, session: requests.Session) -> dict[dict]
        - get_list_property(site_url: str, list_name: str, session: requests.Session, property_name: str) -> str
        - get_list_data_type(site_url: str, list_name: str, session: Session) -> str
        - get_list_items(site_url: str, list_name: str, session: requests.Session) -> list[dict]
        - get_column_datatypes(site_url: str, list_name: str, session: requests.Session) -> dict
        - prepare_data(source_data: dict, column_mappings: dict, old_id: int = None) -> dict
        - get_simplified_list(site_url: str, list_name: str, list_data: list, required_cols: dict) -> list
    """

    logger = get_logger('ListOperations')

    @staticmethod
    def get_required_columns(
        site_url: str, list_name: str, session: requests.Session
    ) -> dict[dict]:
        
        """
        Retrieves the required columns from a SharePoint list, including their internal names and data types.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - session (requests.Session): An authenticated session object for making requests.

        Returns:
            - dict[dict]: A dictionary where each key is a column title and the value is another dictionary containing:
                - "Internal Name": The internal name of the column.
                - "Data Type": The data type of the column.

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
            - The returned dictionary provides the necessary information for handling columns in list operations.
        """

        required_cols = {}
        required_cols["Id"] = {}

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}_api/web/lists/getbytitle('{list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"

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
        
        """
        Retrieves a specific property value for a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - session (requests.Session): An authenticated session object for making requests.
            - property_name (str): The name of the property to retrieve.

        Returns:
            - str: The value of the specified list property.

        Example:
            list_property = ListOperations.get_list_property(site_url, list_name, session, 'BaseTemplate')

        Notes:
            - The property name should be valid for the SharePoint list and correctly spelled.
        """

        endpoint = f"{site_url}_api/web/lists/getbytitle('{list_name}')"
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
    def get_list_data_type(site_url: str, list_name: str, session: Session) -> str:

        """
        Retrieves the data type of the list items in a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - session (requests.Session): An authenticated session object for making requests.

        Returns:
            - str: The data type of the list items.

        Example:
            list_data_type = ListOperations.get_list_data_type(site_url, list_name, session)

        Notes:
            - The data type is used to understand the structure and type of data stored in the list.
        """

        list_item_data_type = ListOperations.get_list_property(
            site_url=site_url,
            list_name=list_name,
            session=session,
            property_name="ListItemEntityTypeFullName",
        )

        return list_item_data_type

    @staticmethod
    def get_list_items(
        site_url: str, list_name: str, session: requests.Session
    ) -> list[dict]:
        
        """
        Retrieves items from a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - session (requests.Session): An authenticated session object for making requests.

        Returns:
            - list[dict]: A list of dictionaries where each dictionary represents a SharePoint list item.

        Example:
            items = ListOperations.get_list_items(site_url, list_name, session)

        Notes:
            - The method retrieves all items from the specified list.
            - The returned list includes metadata and actual data for each item.
        """

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}_api/web/lists/getbytitle('{list_name}')/items"

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
                ListOperations.logger.critical("List not found! Please double check your list name.")
                exit()
            else:
                ListOperations.logger.error("Something went wrong!")
            time.sleep(2)
        items_retrieved = len(all_items)
        if items_retrieved > 0:
            ListOperations.logger.success("Total %s items retrieved", items_retrieved)
        else:
            ListOperations.logger.success("No items in the list.")
        return all_items
    
    @staticmethod
    def get_column_datatypes(site_url:str, list_name:str, session:requests.Session) -> dict:

        """
        Retrieves the data types of columns in a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - session (requests.Session): An authenticated session object for making requests.

        Returns:
            - dict: A dictionary where each key is a column title and the value is the data type of the column.

        Example:
        ```
        {
            'Title': 'Text',
            'Created': 'DateTime'
        }
        ```
        Notes:
            - The returned dictionary helps in understanding the data types of columns for data handling and validation.
        """

        required_cols = {}

        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}_api/web/lists/getbytitle('{list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"

        response = session.get(endpoint, headers=headers)
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

    @staticmethod
    def prepare_data(
        source_data: dict, column_mappings: dict, old_id: int = None
    ) -> dict:
        
        """
        Prepares data for operations by mapping source data to the SharePoint list's column structure.

        Parameters:
            - source_data (dict): A dictionary containing the source data to be prepared.
            - column_mappings (dict): A dictionary mapping source column names to SharePoint list column names.
            - old_id (int, optional): The ID of the item being updated (if applicable).

        Returns:
            - dict: A dictionary containing the prepared data mapped to the SharePoint list's columns.

        Example:
            ```
            prepared_data = ListOperations.prepare_data(
                source_data={'Name': 'Item 1', 'Description': 'Description of item 1'},
                column_mappings={'Name': 'Title', 'Description': 'Description'},
                old_id=1
            )
            ```
        Notes:
            - The `column_mappings` dictionary ensures that data is structured correctly for the SharePoint list.
            - This method is useful for transforming data before inserting or updating list items.
        """

        data = {}
        if old_id:
            data["Old_Id"] = old_id
        for key, value in source_data.items():
            data[column_mappings.get(key, {}).get("Internal Name", None)] = value
        return data

    @staticmethod
    def get_simplified_list(self, site_url, list_name, list_data, required_cols) -> list:

        """
        Simplifies a list of SharePoint list items by including only the required columns.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - list_data (list): A list of dictionaries where each dictionary represents a SharePoint list item.
            - required_cols (dict): A dictionary of required columns to include in the simplified list.

        Returns:
            - list: A simplified list containing only the required columns for each item.

        Example:
            ```
            simplified_list = ListOperations.get_simplified_list(
                site_url,
                list_name,
                list_data,
                required_cols={'Title': 'Title', 'Description': 'Description'}
            )
            ```
        Notes:
            - The method filters out unnecessary columns and includes only those specified in `required_cols`.
            - Useful for reducing data complexity and focusing on relevant information.
        """

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
                        time.sleep(1)
                    list_item_dict["Attachment List"] = attachemts
                else:
                    list_item_dict[col] = row[required_cols[col]["Internal Name"]]
            items_list.append(list_item_dict)
        return items_list