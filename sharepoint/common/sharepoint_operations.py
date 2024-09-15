import requests
from logger.custom_logger import get_logger

class SharePointOperations:

    """
    A utility class that provides static methods to interact with SharePoint lists for handling attachments. This class includes methods to retrieve, download, upload, and delete attachments from a specific SharePoint list item.

    Static Methods:
        1. get_attachments(site_url: str, source_name: str, item_id: int, session: requests.Session) -> list
        - Retrieves the list of attachments for a specified item in a SharePoint list.
        
        2. download_attachments(site_url: str, source_name: str, item_id: int, attachment_name_list: list, session: requests.Session, download_location: str) -> None
        - Downloads the specified attachments from a SharePoint list item and saves them to the given download location on the local system.
        
        3. upload_attachments(site_url: str, source_name: str, item_id: int, attachment_list: list, digest_value: str, session: requests.Session) -> None
        - Uploads a list of attachments to a specified item in a SharePoint list.

        4. delete_attachments(site_url: str, list_name: str, item_id: int, attachment_name_list: list, digest_value: str, session: requests.Session) -> None
        - Deletes the specified attachments from a given item in a SharePoint list.

    Usage Example:
    ```
        site_url = "https://example.sharepoint.com/sites/mysite"
        list_name = "Documents"
        item_id = 123
        session = requests.Session()
        digest_value = "formDigestValue123"

        # Get list of attachments
        attachments = SharePointOperations.get_attachments(site_url, list_name, item_id, session)

        # Download specific attachments
        download_location = "C:/Downloads"
        SharePointOperations.download_attachments(site_url, list_name, item_id, ["file1.pdf"], session, download_location)

        # Upload new attachments
        SharePointOperations.upload_attachments(site_url, list_name, item_id, ["C:/files/file1.pdf"], digest_value, session)

        # Delete attachments
        SharePointOperations.delete_attachments(site_url, list_name, item_id, ["file1.pdf"], digest_value, session)
    ```
    Notes:
        - All methods require a valid `requests.Session` object that is authenticated and authorized to access the SharePoint site.
        - The `digest_value` parameter is required for upload and delete operations, and it should be obtained from a valid SharePoint session.
        - Ensure that paths for file uploads and downloads are correct and accessible on the system.
    """


    logger = get_logger('SharePointOperations')

    @staticmethod
    def get_attachments(
        site_url: str, source_name: str, item_id: int, session: requests.Session
    ) -> list:
        
        """
        Description:
            This method retrieves the list of attachments for a specific item in a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site where the list is hosted. This should include the protocol (e.g., https://).
            - source_name (str): The name of the SharePoint list from which to retrieve the attachments.
            - item_id (int): The unique ID of the item within the SharePoint list for which attachments are to be fetched.
            - session (requests.Session): An authenticated session object used to make requests to SharePoint. This session should have proper authorization to access the specified list.

        Returns:
            - list: A list of attachments related to the specified item. Each attachment may contain metadata such as the attachment URL, file name, and file size.

        Usage Example:

            ```
            site_url = "https://example.sharepoint.com/sites/mysite"
            source_name = "Documents"
            item_id = 123
            session = requests.Session()

            attachments = get_attachments(site_url, source_name, item_id, session)

            for attachment in attachments:
                print(attachment["FileName"], attachment["ServerRelativeUrl"])
            ```

        Notes:
            - Ensure that the session object passed has valid authentication and necessary permissions to access the list items.
            - This method assumes that SharePoint REST API is used to retrieve the attachments.
        """

        attachemnt_list = []
        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}_api/web/lists/getbytitle('{source_name}')/Items({item_id})/AttachmentFiles"

        response = session.get(endpoint, headers=headers)
        response.raise_for_status()

        data = response.json()
        attachments = data.get("d", {}).get("results", [])
        for attachemnt in attachments:
            filename = attachemnt["FileName"]
            attachemnt_list.append(filename)

        return attachemnt_list

    @staticmethod
    def download_attachments(
        site_url: str,
        source_name: str,
        item_id: int,
        attachment_name_list: list,
        session: requests.Session,
        download_location: str,
    ) -> None:
        
        """
        Description:
            This method downloads the specified attachments from a SharePoint list item and saves them to the given download location on the local system.

        Parameters:
            - site_url (str): The base URL of the SharePoint site where the list is hosted. This should include the protocol (e.g., https://).
            - source_name (str): The name of the SharePoint list from which to download the attachments.
            - item_id (int): The unique ID of the item within the SharePoint list for which attachments are to be downloaded.
            - attachment_name_list (list): A list of attachment file names that need to be downloaded.
            - session (requests.Session): An authenticated session object used to make requests to SharePoint. This session should have proper authorization to access the specified list.
            - download_location (str): The path where the attachments will be saved locally.

        Returns:
            - None: This method doesn't return anything. It downloads the specified attachments and saves them to the specified location.

        Usage Example:
        ```
            site_url = "https://example.sharepoint.com/sites/mysite"
            source_name = "Documents"
            item_id = 123
            attachment_name_list = ["file1.pdf", "file2.docx"]
            session = requests.Session()
            download_location = "C:/Downloads"

            download_attachments(site_url, source_name, item_id, attachment_name_list, session, download_location)
        ```
        Notes:
            - Ensure the session object has valid authentication and necessary permissions to access and download the attachments.
            - Make sure that the download location path exists and is writable.
            - Only the attachments specified in `attachment_name_list` will be downloaded.
        """


        headers = {"Accept": "application/json; odata=verbose"}

        for filename in attachment_name_list:
            endpoint = f"{site_url}_api/web/lists/getbytitle('{source_name}')/Items({item_id})/AttachmentFiles('{filename}')/$value"
            response = session.get(endpoint, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                with open(f"{download_location}\\{filename}", "wb") as f:
                    f.write(response.content)
            else:
                SharePointOperations.logger.error('Something went wrong! %s', response.json())

    @staticmethod
    def upload_attachments(
        site_url: str,
        source_name: str,
        item_id: int,
        attachment_list: list,
        digest_value: str,
        session: requests.Session,
    ) -> None:
        
        """
        Description:
            This method uploads a list of attachments to a specified item in a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site where the list is hosted. This should include the protocol (e.g., https://).
            - source_name (str): The name of the SharePoint list to which the attachments will be uploaded.
            - item_id (int): The unique ID of the item within the SharePoint list where attachments will be uploaded.
            - attachment_list (list): A list of file paths representing the attachments to be uploaded.
            - digest_value (str): The form digest value required for authentication when making POST requests to SharePoint. This value ensures that the session is valid.
            - session (requests.Session): An authenticated session object used to make requests to SharePoint. This session should have proper authorization to upload attachments.

        Returns:
            - None: This method doesn't return anything. It uploads the specified attachments to the specified SharePoint list item.

        Usage Example:
        ```
            site_url = "https://example.sharepoint.com/sites/mysite"
            source_name = "Documents"
            item_id = 123
            attachment_list = ["C:/files/file1.pdf", "C:/files/file2.docx"]
            digest_value = "formDigestValue123"
            session = requests.Session()

            upload_attachments(site_url, source_name, item_id, attachment_list, digest_value, session)
        ```
        Notes:
            - Ensure that the session object has valid authentication and necessary permissions to upload attachments.
            - The `digest_value` is necessary to authenticate POST requests to SharePoint, and should be obtained from a valid SharePoint session.
            - Only files specified in `attachment_list` will be uploaded to the SharePoint list item.
            - The file paths in `attachment_list` should be accessible and valid on the local system.
        """

        request_digest = digest_value
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest,
        }
        attachments_to_be_uploaded = len(attachment_list)

        for file in attachment_list:
            SharePointOperations.logger.info("Attachments left for insertion %s", attachments_to_be_uploaded)
            file_name = file.split("/")[-1]

            with open(file, "rb") as f:
                response = session.post(
                    f"{site_url}_api/web/lists/getbytitle('{source_name}')/Items({item_id})/AttachmentFiles/add(FileName='{file_name}')",
                    headers=headers,
                    data=f,
                )
                response.raise_for_status()

            if response.status_code != 200:
                SharePointOperations.logger.error("Failed to upload %s", file_name)
            else:
                SharePointOperations.logger.success("Uploaded attachment %s", file_name)
            attachments_to_be_uploaded -= 1

    def delete_attachments(
        site_url: str,
        list_name: str,
        item_id: int,
        attachment_name_list: list,
        digest_value: str,
        session: requests.Session,
    ) -> None:

        """
        Description:
            This method deletes the specified attachments from a given item in a SharePoint list.

        Parameters:
            - site_url (str): The base URL of the SharePoint site where the list is hosted. This should include the protocol (e.g., https://).
            - list_name (str): The name of the SharePoint list from which attachments are to be deleted.
            - item_id (int): The unique ID of the item within the SharePoint list from which attachments will be deleted.
            - attachment_name_list (list): A list of attachment file names that need to be deleted from the item.
            - digest_value (str): The form digest value required for authentication when making POST requests to SharePoint. This ensures that the session is valid.
            - session (requests.Session): An authenticated session object used to make requests to SharePoint. This session should have proper authorization to delete attachments.

        Returns:
            - None: This method does not return anything. It deletes the specified attachments from the specified item.

        Usage Example:
        ```
            site_url = "https://example.sharepoint.com/sites/mysite"
            list_name = "Documents"
            item_id = 123
            attachment_name_list = ["file1.pdf", "file2.docx"]
            digest_value = "formDigestValue123"
            session = requests.Session()

            delete_attachments(site_url, list_name, item_id, attachment_name_list, digest_value, session)
        ```
        Notes:
            - Ensure that the session object has valid authentication and necessary permissions to delete the attachments.
            - The `digest_value` is necessary to authenticate POST requests to SharePoint, and should be obtained from a valid SharePoint session.
            - Only the attachments specified in `attachment_name_list` will be deleted.
        """

        request_digest = digest_value
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "IF-MATCH": "*",
            "X-HTTP-Method": "DELETE",
            "X-RequestDigest": request_digest,
        }
        for filename in attachment_name_list:
            response = session.post(
                f"{site_url}_api/web/lists/getbytitle('{list_name}')/Items({item_id})/AttachmentFiles('{filename}')",
                headers=headers,
            )
            response.raise_for_status()
            if not response.status_code == 200:
                SharePointOperations.logger.error("Failed to delete old attachment %s", filename)
            else:
                SharePointOperations.logger.success("Successfully deleted attachment %s", filename)
