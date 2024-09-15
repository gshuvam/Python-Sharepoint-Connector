import uuid
from requests import Session
from sharepoint.list.list_operations import ListOperations
from logger.custom_logger import get_logger

class BatchOperations:

    """
    The `BatchOperations` class provides static methods for handling batch operations in SharePoint lists. This includes creating and managing batches for delete, insert, and update operations, as well as performing these operations in batches to optimize performance and reduce server load.

    Static Methods:
        - __get_request_digest(site_url: str, session: Session) -> str
        - __create_delete_batch(site_url: str, list_name: str, item_ids: list, batch_guid: str) -> str
        - delete_items_in_batches(site_url: str, list_name: str, items: list, session: Session, batch_size=100) -> None
        - __create_insert_batch(site_url: str, list_name: str, insert_list: list, batch_guid: str, session: Session) -> str
        - insert_items_in_batches(site_url: str, list_name: str, items: list, session: Session, batch_size=100) -> None
        - __create_update_batch(site_url: str, list_name: str, update_dict: dict[str, list], batch_guid: str, session: Session) -> str
        - update_items_in_batches(site_url: str, list_name: str, items: dict[str, list], session: Session, batch_size=100) -> None
    """

    logger = get_logger('BatchOperations')

    @staticmethod
    def __get_request_digest(site_url: str, session: Session) -> str:

        """
        Retrieves the request digest value required for authenticated batch operations with SharePoint.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - session (Session): An authenticated session object for making requests.

        Returns:
            - str: The request digest value.

        Notes:
            - This method is private and used internally to obtain the digest value necessary for batch operations.
            - The digest value is required to authenticate requests made to SharePoint.
        """

        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }
        response = session.post(f"{site_url}_api/contextinfo", headers=headers)
        if response.status_code == 200:
            return response.json()["d"]["GetContextWebInformation"]["FormDigestValue"]
        else:
            raise Exception(
                f"Failed to get request digest: {response.status_code}, {response.text}"
            )

    @staticmethod
    def __create_delete_batch(
        site_url: str, list_name: str, item_ids: list, batch_guid: str
    ) -> str:
        
        """
        Creates a batch request for deleting items from a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - item_ids (list): A list of item IDs to be deleted.
            - batch_guid (str): A unique identifier for the batch request.

        Returns:
            - str: The body content of the batch request for deletion.

        Notes:
            - This method generates body of a batch request for deleting multiple items.
            - The `batch_guid` ensures that the batch request is unique and traceable.
        """

        changeset_guid = str(uuid.uuid4())
        batch_body = []
        batch_body.append(f"--batch_{batch_guid}")
        batch_body.append(
            f"Content-Type: multipart/mixed; boundary=changeset_{changeset_guid}"
        )
        batch_body.append("")

        for item_id in item_ids:
            batch_body.append(f"--changeset_{changeset_guid}")
            batch_body.append("Content-Type: application/http")
            batch_body.append("Content-Transfer-Encoding: binary")
            batch_body.append("")

            batch_body.append(
                f"DELETE {site_url}_api/web/lists/getbytitle('{list_name}')/items({item_id}) HTTP/1.1"
            )
            batch_body.append("IF-MATCH: *")
            batch_body.append("Content-Type: application/json;odata=verbose")
            batch_body.append("")

        batch_body.append(f"--changeset_{changeset_guid}--")
        batch_body.append(f"--batch_{batch_guid}--")

        return "\n".join(batch_body)

    @staticmethod
    def delete_items_in_batches(
        site_url: str, list_name: str, items: list, session: Session, batch_size=100
    ) -> None:
        
        """
        Deletes items from a SharePoint list in batches.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - items (list): A list of items to be deleted, each item should include the ID.
            - session (Session): An authenticated session object for making requests.
            - batch_size (int, optional): The size of each batch request, default is 100.

        Returns:
            - None: This method doesn't return anything but performs batch delete operations.

        Notes:
            - The method handles the deletion of items in specified batch sizes to optimize performance.
            - The `batch_size` parameter controls how many items are included in each batch request.
        """

        batch_endpoint = f"{site_url}_api/$batch"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }
        batch_no = 1
        for i in range(0, len(items), batch_size):
            batch_guid = str(uuid.uuid4())
            batch_items = items[i : i + batch_size]
            item_ids = [item["Id"] for item in batch_items]
            batch_body = BatchOperations.__create_delete_batch(
                site_url=site_url,
                list_name=list_name,
                item_ids=item_ids,
                batch_guid=batch_guid,
            )

            request_digest = BatchOperations.__get_request_digest(
                site_url=site_url, session=session
            )

            batch_headers = headers.copy()
            batch_headers.update(
                {
                    "Content-Type": f"multipart/mixed; boundary=batch_{batch_guid}",
                    "X-RequestDigest": request_digest,
                }
            )

            response = session.post(
                batch_endpoint, headers=batch_headers, data=batch_body
            )
            response.raise_for_status()
            BatchOperations.logger.success('Processed batch %s successfully', batch_no)
            batch_no += 1

    @staticmethod
    def __create_insert_batch(
        site_url: str,
        list_name: str,
        insert_list: list,
        batch_guid: str,
        session: Session,
    ) -> str:
        
        """
        Creates a batch request for inserting items into a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - insert_list (list): A list of dictionaries where each dictionary represents an item to be inserted.
            - batch_guid (str): A unique identifier for the batch request.
            - session (Session): An authenticated session object for making requests.

        Returns:
            - str: The body content of the batch request for insertion.

        Notes:
            - This method generates body of a batch request for inserting multiple items into the list.
            - The `batch_guid` ensures the uniqueness of the batch request.
        """

        changeset_guid = str(uuid.uuid4())
        insert_dict = {
            "__metadata": {
                "type": ListOperations.get_list_data_type(
                    site_url=site_url, list_name=list_name, session=session
                )
            }
        }
        batch_body = []
        batch_body.append(f"--batch_{batch_guid}")
        batch_body.append(
            f"Content-Type: multipart/mixed; boundary=changeset_{changeset_guid}"
        )
        batch_body.append("")

        for item in insert_list:
            body_dict = insert_dict.copy()
            body_dict.update(item)

            batch_body.append(f"--changeset_{changeset_guid}")
            batch_body.append("Content-Type: application/http")
            batch_body.append("Content-Transfer-Encoding: binary")
            batch_body.append("")

            batch_body.append(
                f"POST {site_url}_api/web/lists/getbytitle('{list_name}')/items HTTP/1.1"
            )

            batch_body.append(f"{body_dict}")

            batch_body.append("Content-Type: application/json;odata=verbose")
            batch_body.append("")

        batch_body.append(f"--changeset_{changeset_guid}--")
        batch_body.append(f"--batch_{batch_guid}--")

        return "\n".join(batch_body)

    @staticmethod
    def insert_items_in_batches(
        site_url: str, list_name: str, items: list, session: Session, batch_size=100
    ) -> None:
        
        """
        Inserts items into a SharePoint list in batches.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - items (list): A list of dictionaries where each dictionary represents an item to be inserted.
            - session (Session): An authenticated session object for making requests.
            - batch_size (int, optional): The size of each batch request, default is 100.

        Returns:
            - None: This method doesn't return anything but performs batch insert operations.

        Notes:
            - The method handles the insertion of items in specified batch sizes to improve efficiency.
            - The `batch_size` parameter determines how many items are included in each batch request.
        """

        batch_endpoint = f"{site_url}_api/$batch"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }
        batch_no = 1
        for i in range(0, len(items), batch_size):
            batch_guid = str(uuid.uuid4())
            batch_items = items[i : i + batch_size]
            batch_body = BatchOperations.__create_insert_batch(
                site_url=site_url,
                list_name=list_name,
                insert_list=batch_items,
                batch_guid=batch_guid,
                session=session,
            )

            request_digest = BatchOperations.__get_request_digest(
                site_url=site_url, session=session
            )

            batch_headers = headers.copy()
            batch_headers.update(
                {
                    "Content-Type": f"multipart/mixed; boundary=batch_{batch_guid}",
                    "X-RequestDigest": request_digest,
                }
            )

            response = session.post(
                batch_endpoint, headers=batch_headers, data=batch_body
            )
            response.raise_for_status()
            BatchOperations.logger.success('Processed batch %s successfully', batch_no)
            batch_no += 1

    @staticmethod
    def __create_update_batch(
        site_url: str,
        list_name: str,
        update_dict: dict[str, list],
        batch_guid: str,
        session: Session,
    ) -> str:
        
        """
        Creates a batch request for updating items in a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - update_dict (dict[str, list]): A dictionary where the key is an item ID and the value is a list of fields to update.
            - batch_guid (str): A unique identifier for the batch request.
            - session (Session): An authenticated session object for making requests.

        Returns:
            - str: The body content of the batch request for updating.

        Notes:
            - This method generates body of a batch request for updating multiple items.
            - The `batch_guid` ensures that the batch request is unique and traceable.
        """

        changeset_guid = str(uuid.uuid4())
        insert_dict = {
            "__metadata": {
                "type": ListOperations.get_list_data_type(
                    site_url=site_url, list_name=list_name, session=session
                )
            }
        }
        batch_body = []
        batch_body.append(f"--batch_{batch_guid}")
        batch_body.append(
            f"Content-Type: multipart/mixed; boundary=changeset_{changeset_guid}"
        )
        batch_body.append("")

        for old_id, update_item in update_dict.items():
            body_dict = insert_dict.copy()
            body_dict.update(update_item)

            batch_body.append(f"--changeset_{changeset_guid}")
            batch_body.append("Content-Type: application/http")
            batch_body.append("Content-Transfer-Encoding: binary")
            batch_body.append("")

            batch_body.append(
                f"PATCH {site_url}_api/web/lists/getbytitle('{list_name}')/items({old_id}) HTTP/1.1"
            )

            batch_body.append(f"{body_dict}")

            batch_body.append("Content-Type: application/json;odata=verbose")
            batch_body.append("IF-MATCH: *")
            batch_body.append("X-HTTP-Method: MERGE")
            batch_body.append("")

        batch_body.append(f"--changeset_{changeset_guid}--")
        batch_body.append(f"--batch_{batch_guid}--")

        return "\n".join(batch_body)

    @staticmethod
    def update_items_in_batches(
        site_url: str,
        list_name: str,
        items: dict[str, list],
        session: Session,
        batch_size=100,
    ) -> None:
        
        """
        Updates items in a SharePoint list in batches.

        Parameters:
            - site_url (str): The base URL of the SharePoint site.
            - list_name (str): The name of the SharePoint list.
            - items (dict[str, list]): A dictionary where the key is an item ID and the value is a list of fields to update.
            - session (Session): An authenticated session object for making requests.
            - batch_size (int, optional): The size of each batch request, default is 100.

        Returns:
            - None: This method doesn't return anything but performs batch update operations.

        Notes:
            - The method handles the updating of items in specified batch sizes to optimize performance.
            - The `batch_size` parameter controls how many updates are included in each batch request.
        """

        def dict_batches(input_dict, batch_size):
            items = list(input_dict.items())
            for i in range(0, len(items), batch_size):
                yield dict(items[i : i + batch_size])

        batch_endpoint = f"{site_url}_api/$batch"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }
        batch_no = 1
        for batch in dict_batches(items, batch_size):
            batch_guid = str(uuid.uuid4())
            batch_body = BatchOperations.__create_update_batch(
                site_url=site_url,
                list_name=list_name,
                update_dict=batch,
                batch_guid=batch_guid,
                session=session,
            )

            request_digest = BatchOperations.__get_request_digest(
                site_url=site_url, session=session
            )

            batch_headers = headers.copy()
            batch_headers.update(
                {
                    "Content-Type": f"multipart/mixed; boundary=batch_{batch_guid}",
                    "X-RequestDigest": request_digest,
                }
            )

            response = session.post(
                batch_endpoint, headers=batch_headers, data=batch_body
            )
            response.raise_for_status()
            BatchOperations.logger.success('Processed batch %s successfully', batch_no)
            batch_no += 1
