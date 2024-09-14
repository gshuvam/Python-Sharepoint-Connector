import requests

class SharePointOperations:
    @staticmethod
    def get_attachments(
        site_url: str, source_name: str, item_id: int, session: requests.Session
    ) -> list:
        attachemnt_list = []
        headers = {"Accept": "application/json; odata=verbose"}
        endpoint = f"{site_url}/_api/web/lists/getbytitle('{source_name}')/Items({item_id})/AttachmentFiles"

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
        headers = {"Accept": "application/json; odata=verbose"}

        for filename in attachment_name_list:
            endpoint = f"{site_url}/_api/web/lists/getbytitle('{source_name}')/Items({item_id})/AttachmentFiles('{filename}')/$value"
            response = session.get(endpoint, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                with open(f"{download_location}\\{filename}", "wb") as f:
                    f.write(response.content)
            else:
                print(response.status_code)

    @staticmethod
    def upload_attachments(
        site_url: str,
        source_name: str,
        item_id: int,
        attachment_list: list,
        digest_value: str,
        session: requests.Session,
    ) -> None:
        request_digest = digest_value
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest,
        }
        attachments_to_be_uploaded = len(attachment_list)

        for file in attachment_list:
            print("Attachments left for insertion %s", attachments_to_be_uploaded)
            file_name = file.split("/")[-1]

            with open(file, "rb") as f:
                response = session.post(
                    f"{site_url}/_api/web/lists/getbytitle('{source_name}')/Items({item_id})/AttachmentFiles/add(FileName='{file_name}')",
                    headers=headers,
                    data=f,
                )
                response.raise_for_status()

            if response.status_code != 200:
                print("Failed to upload %s", file_name)
            else:
                print("Uploaded attachment %s", file_name)
            attachments_to_be_uploaded -= 1

    def delete_attachments(
        site_url: str,
        list_name: str,
        item_id: int,
        attachment_name_list: list,
        digest_value: str,
        session: requests.Session,
    ) -> None:
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
                f"{site_url}/_api/web/lists/getbytitle('{list_name}')/Items({item_id})/AttachmentFiles('{filename}')",
                headers=headers,
            )
            response.raise_for_status()
            if not response.status_code == 200:
                print("Failed to delete old attachment %s", filename)
            else:
                print("Successfully deleted old attachment %s", filename)
