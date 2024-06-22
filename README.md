# SharePoint Connector

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
pip install requests selenium undetected-chromedriver
```

## Setup

### 1. Clone the repository:

```bash
git clone https://github.com/your-username/sharepoint-connector.git
cd sharepoint-connector
```

### 2. Update configuration:

Update the necessary configuration parameters such as SharePoint site URL, list names, and credentials in the script. You can use a .env file to store these.

## Usage

To create a session and connect to SharePoint, use the ```create_session()``` function. 
Use the session object to call SharePoint REST API. Dont forget to obtain a digest value for ```POST``` operations. 

```
headers = {
    'Accept': 'application/json;odata=verbose',
    'Content-Type': 'application/json;odata=verbose'
}

response = session.post(f"{sharepoint_site_url}/_api/contextinfo", headers=headers)
request_digest = response.json()['d']['GetContextWebInformation']['FormDigestValue']

```

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

## Error Handling

Ensure to handle errors appropriately. If you encounter a version mismatch error or other issues, the script should attempt to resolve them and retry the operation.

## Contributing

If you wish to contribute to this project, please fork the repository and submit a pull request. We welcome improvements and fixes.

## License

This project is licensed under the MIT License.

## Contact

For any questions or suggestions, please contact shuvam1309@gmail.com.
