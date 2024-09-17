# Python SharePoint Connector

This repository includes a Python script designed to connect to a SharePoint site and execute various REST API operations, such as creating sites and lists, uploading attachments, and managing SharePoint lists and so on. It works as long as your account has the necessary permissions to perform the actions and Microsoft provides the corresponding REST API. This method does not require admin center permissions or access, such as PowerShell PnP or SharePoint Management Shell, and it doesn't need any Azure app registration.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.x
- Required Python libraries:
  - `requests`
  - `selenium`
  - `undetected-chromedriver`

You can install the required libraries using pip:

```bash
pip install -r 'requirements.txt'
```

## Setup

### 1. Clone the repository:

```bash
git clone https://github.com/your-username/sharepoint-connector.git
cd sharepoint-connector
```

### 2. Update configuration:

Update the necessary configuration parameters such as SharePoint site URL, list names, and credentials in the script. You can use a .env file to store these.

```
TEST = str_to_bool(os.environ.get('TEST'))
DEBUGGING = str_to_bool(os.environ.get('DEBUGGING'))
ENABLE_CACHE = str_to_bool(os.environ.get('ENABLE_CACHE'))
    
if TEST:
    site_url = os.environ.get('SITE_URL')
    list_name = os.environ.get('LIST_NAME')
    domain = os.environ.get('DOMAIN')
    username = os.environ.get('USERNAME')
    password = os.environ.get("PASSWORD")
else:
    site_url = os.environ.get('SITE_URL')
    list_name = os.environ.get('LIST_NAME')
    domain = os.environ.get("TEST_DOMAIN")
    app = ctk.CTk()
    username_dialog = InputDialog(app, 'Username', 'Enter Sharepoint Username')
    username = username_dialog.get_input()
    app.destroy()

cache_file = os.environ.get('CACHE_LOCATION')
key_file = os.environ.get('KEY_LOCATION')
```

## Usage
To establish a session for connecting to SharePoint, instantiate a ```SharePointConnector``` object. Use the ```SharePointConnector.session``` object to make calls to the SharePoint REST API. For ```POST``` operations, ensure you obtain a digest value, which can be accessed via ```SharePointConnector.digest_value```. Alternatively, you can use the snippet below:

```
headers = {
    'Accept': 'application/json;odata=verbose',
    'Content-Type': 'application/json;odata=verbose'
}

response = session.post(f"{sharepoint_site_url}/_api/contextinfo", headers=headers)
request_digest = response.json()['d']['GetContextWebInformation']['FormDigestValue']

```
### Get items from a SharePoint List
```
connector_obj = SharePointConnector(
    site_url=site_url,
    cookie_dict=LoginHandler(
        site_url=site_url,
        username=username,
        password=password,
        DEBUGGING=DEBUGGING,
        cache_file=cache_file,
        key_file=key_file,
        domain=domain
    ).authenticate(
        ENABLE_CACHE=ENABLE_CACHE
    )
)

list_items = List(
        site_url=connector_obj.site_url,
        list_name=list_name,
        sharepoint_connector_object=connector_obj,
    ).get_list_items()
```
### Upload attachments to a list
```
headers = {
    "Accept": "application/json; odata=verbose",
    "Content-Type": "application/json; odata=verbose",
    "X-RequestDigest": request_digest
}

for filename in attachment_list:
    with open(f"{temp_folder}\\{filename}", 'rb') as f:
        response = session.post(
            f"{url}/_api/web/lists/getbytitle('{list_name}')/Items({
                item_id})/AttachmentFiles/add(FileName='{filename}')",
            headers=headers,
            data=f
        )
```
OR
```
SharePointOperations.upload_attachments(
    site_url=site_url,
    source_name=list_name,
    item_id=item_id,
    attachment_list=attachment_list,
    digest_value=connector_obj.digest_value,
    session=connector_obj.session
)
```

## Error Handling

Ensure to handle errors appropriately. If you encounter a version mismatch error or other issues, the script should attempt to resolve them and retry the operation.

## Contributing

If you wish to contribute to this project, please fork the repository and submit a pull request. We welcome improvements and fixes.

## License

This project is licensed under the MIT License.

## Contact

For any questions or suggestions, please contact [me](https://github.com/gshuvam).
