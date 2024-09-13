import time
from connector.sharepoint_connector import SharePointConnector

class List(SharePointConnector):
    def __init__(self, site_url, list_name, cookie_dict):
        super().__init__(
            site_url=site_url,
            cookie_dict=cookie_dict
        )
        self.list_name = list_name
        self.list_item_dtype_property_name = 'ListItemEntityTypeFullName'
        self.list_item_data_type = self.get_list_property(self.list_item_property_name)
        self.list_column_internal_name_mapping = self.__get_field_mappings()
        self.column_datatypes = self.__get_column_datatypes()


    def insert_items(self, insert_list):
        self.logger.info('Total items retrieved from excel: %s', len(insert_list))
        request_digest = self.digest_value
        time.sleep(1)
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose",
            "X-RequestDigest": request_digest
        }
        items_to_be_inserted = len(insert_list)
        self.logger.info('Starting insertion...')

        processed_insert_list = self.prepare_data(insert_list)
        
        for item in processed_insert_list:
            idetifier = item['Title']
            payload = {
            '__metadata': {'type': self.list_item_data_type}
            }

            if items_to_be_inserted % 100 == 0:
                self.logger.info('Waiting for some time to avoid MS timeout')
                time.sleep(30)
            if items_to_be_inserted % 10 == 0:
                self.logger.info('Items left for insertion %s', items_to_be_inserted)

            for key, value in item.items():
                payload[key] = value

            response = self.session.post(
                f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            time.sleep(2)
            self.logger.success('Successfully inserted item %s', idetifier)
            if response.status_code != 201:
                self.logger.error('Unable to add item %s', response.json())
            items_to_be_inserted -= 1


    def get_list_property(self, property_name):
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')"
        headers = {
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
        }

        response = self.session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        output = data.get('d', {}).get(property_name, None)
        time.sleep(0.5)
        return output
        
    def __get_field_mappings(self):
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/fields?$filter=Hidden eq false and ReadOnlyField eq false"
        headers = {
        'Accept': 'application/json;odata=verbose',
        'Content-Type': 'application/json;odata=verbose',
        }

        response = self.session.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()

        fields = data.get('d', {}).get('results', [])
        field_mappings = {field['Title']: field['InternalName'] for field in fields}
        time.sleep(0.5)
        return field_mappings
    
    def get_list_items(self):
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items"
        headers = {
        'Accept': 'application/json;odata=verbose',
        'Content-Type': 'application/json;odata=verbose',
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
                self.logger.critical("List not found! Please double check your list name.")
                exit()
            else:
                self.logger.critical("Something went wrong!")
            time.sleep(2)
        items_retrieved = len(all_items)
        self.logger.success("Total %s items retrieved from the List", items_retrieved)

        return all_items
    
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
            if internal_name not in ['ContentType']:
                required_cols[title] = {"Internal Name": internal_name, "Data Type": data_type}
        time.sleep(0.5)

        return required_cols
    
    def prepare_data(self, insert_list):
        processed_insert_list = []
        for item in insert_list:
            processed_item_dict = {}
            for key, value in item.items():
                data_type = self.list_field_dict[key]['Data Type']
                internal_name = self.list_field_dict[key]['Internal Name']

                if data_type == 'Text':
                    if not isinstance(value, str):
                        value = str(value)
                elif data_type == 'Number':
                    if not isinstance(value, int) or not isinstance(value, float):
                        try:
                            value = float(value)
                        except ValueError:
                            value = None
                elif data_type == 'DateTime':
                    pass
                elif data_type == 'Choice':
                    pass
                elif data_type == 'Attachments':
                    pass
                else:
                    pass
                if value is not None:
                    processed_item_dict[internal_name] = value
            processed_insert_list.append(processed_item_dict)
        return processed_insert_list