import os
import shutil
from datetime import datetime
# from logger.custom_logger import get_logger
from utils.tools import str_to_bool

class Utils:
    # logger = get_logger('Utils')

    @staticmethod
    def dict_to_tuple(d):
        list_dict = []
        for key, value in sorted(d.items()):
            if key != 'Id':
                if isinstance(value, list):
                    temp = (key, tuple(value))
                else:
                    temp = (key, value)
                list_dict.append(temp)
        return tuple(list_dict)

    @staticmethod
    def prepare_data(item_dict, required_col_dict):
        insert_item = {}
        try:
            for key, value in item_dict.items():
                if key in ('Attachment List', 'Id', 'Attachments'):
                    insert_item[key] = value
                else:
                    if value:
                        if key not in ['Modified']:
                            data_type = required_col_dict[key]['Data Type']
                            internl_name = required_col_dict[key]['Internal Name']

                            if data_type == 'Text':
                                if not isinstance(value, str):
                                    value = str(value)
                            elif data_type == 'Number':
                                if not isinstance(value, int) or not isinstance(value, float):
                                    value = int(value)
                            elif data_type == 'DateTime':
                                pass
                            elif data_type == 'Choice':
                                pass
                            elif data_type == 'Attachments':
                                pass
                            else:
                                pass
                            insert_item[internl_name] = value
        except Exception as e:
            print(e)
        return insert_item

    @staticmethod
    def get_list_diff(a, b, required_destination_cols, primary_key = 'Requirement Id'):
        # required_destination_cols['Requirement Id']['Internal Name']
        dict_b = {item[primary_key]: item for item in b}
        inserts = []
        updates = []
        for item_a in a:
            if item_a.get("Customer Name") and 'kpmg' in item_a['Customer Name'].lower():
                title = item_a[primary_key]
                if title not in dict_b:
                    insert_data = {}
                    insert_data = Utils.prepare_data(item_a, required_destination_cols)
                    insert_data.update(Utils.prepare_data({'Update Flag': 'True'}, required_destination_cols))
                    inserts.append(insert_data)
                else:
                    update_flag = str_to_bool(dict_b[title]['Update Flag'])
                    if update_flag:
                        item_b = dict_b[title]
                        modified_a = datetime.fromisoformat(item_a['Modified'])
                        modified_b = datetime.fromisoformat(item_b['Modified'])

                        need_update = False
                        if modified_a > modified_b:
                            for key in item_a:
                                if key not in ['Id', 'Modified'] and item_a[key] != item_b.get(key):
                                    need_update = True
                                    break
                        
                        if need_update:
                            update_data = {}
                            update_data = Utils.prepare_data(item_a, required_destination_cols)
                            updates.append(update_data)
            
            if len(inserts) + len(b) > len(a):
                #some items has been deleted in list a
                dict_a = {item[primary_key]: item for item in a}
                for item_b in b:
                    title = item_b[primary_key]
                    if title not in dict_a:
                        update_data = {}
                        item_b['Current Status'] = 'Closed'
                        update_data = Utils.prepare_data(item_b, required_destination_cols)
                        updates.append(update_data)
                    
        return inserts, updates

    @staticmethod
    def compare_list_items(a, b):
        set_a = set(Utils.dict_to_tuple(d) for d in a)
        set_b = set(Utils.dict_to_tuple(d) for d in b)

        set_only_a = set_a - set_b
        difference = [d for d in a if Utils.dict_to_tuple(d) in set_only_a]
        return difference

    @staticmethod
    def clear_folder(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. {e}")
