import os
import customtkinter as ctk
from dotenv import find_dotenv, load_dotenv
from auth.auth import LoginHandler
from utils.methods import str_to_bool
from connector.sharepoint_connector import SharePointConnector
from gui.dialogs import InputDialog
from sharepoint.list.list import List


def main():

    # initializing env vars
    load_dotenv(find_dotenv(), override=True)
    (
        site_url,
        list_name,
        username,
        password,
        domain
    ) = None, None, None, None, None

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

    print(list_items)

if __name__=='__main__':
    main()