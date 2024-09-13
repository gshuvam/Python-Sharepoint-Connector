import configparser
import ast
from rapidfuzz import process

def read_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def write_config(config, file_path):
    # Ensure that mappings are stored as lists
    for section in config.sections():
        for option in config.options(section):
            value = config.get(section, option)
            try:
                # Convert value to a list if it's not already
                value_list = ast.literal_eval(value)
                if not isinstance(value_list, list):
                    raise ValueError
                config.set(section, option, str(value_list))
            except (ValueError, SyntaxError):
                # If value is not a list, wrap it in a list
                config.set(section, option, str([value]))
    
    with open(file_path, 'w') as configfile:
        config.write(configfile)


def get_mappings(config, section, option):
    try:
        value = config.get(section, option, fallback="[]")
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        # In case of improper formatting, return an empty list
        return []

def set_mappings(config, section, option, new_value):
    current_mappings = get_mappings(config, section, option)
    if new_value not in current_mappings and new_value != '':
        current_mappings.append(new_value)
    config.set(section, option, str(current_mappings))

def str_to_bool(string_value):
    return string_value.lower() in ['true', '1', 'yes', 'y']

def map_skill(user_input, predefined_skills, threshold=80):
    best_match, score = process.extractOne(
        user_input,
        predefined_skills,
        score_cutoff=threshold
    )

    if best_match:
        return best_match
    return None