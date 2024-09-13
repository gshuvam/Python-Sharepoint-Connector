import uuid
from requests import Session
from sharepoint.list_operations import ListOperations


class BatchOperations:
    @staticmethod
    def __get_request_digest(site_url: str, session: Session) -> str:
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }
        response = session.post(f"{site_url}/_api/contextinfo", headers=headers)
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
    ):
        batch_endpoint = f"{site_url}_api/$batch"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }
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

    @staticmethod
    def __create_insert_batch(
        site_url: str,
        list_name: str,
        insert_list: list,
        batch_guid: str,
        session: Session,
    ) -> str:
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
    ):
        batch_endpoint = f"{site_url}_api/$batch"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }
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

    @staticmethod
    def __create_update_batch(
        site_url: str,
        list_name: str,
        update_dict: dict[str, list],
        batch_guid: str,
        session: Session,
    ) -> str:
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
    ):
        def dict_batches(input_dict, batch_size):
            items = list(input_dict.items())
            for i in range(0, len(items), batch_size):
                yield dict(items[i : i + batch_size])

        batch_endpoint = f"{site_url}_api/$batch"
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
        }
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
