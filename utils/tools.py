import configparser
import ast
from rapidfuzz import process

def read_config(file_path):
    """
    Reads a configuration file and returns a ConfigParser object.

    Args:
        file_path (str): The path to the configuration file.

    Returns:
        configparser.ConfigParser: The configuration parser object containing the configuration data.
    """

    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def write_config(config, file_path):
    """
    Writes the configuration data to a file. Ensures that all mappings are stored as lists.

    Args:
        config (configparser.ConfigParser): The configuration parser object to be written.
        file_path (str): The path to the file where the configuration will be written.

    Actions:
        - Converts the configuration values to lists if they are not already in list format.
        - Writes the modified configuration to the specified file.
    """

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
    """
    Retrieves a list of mappings from the configuration file.

    Args:
        config (configparser.ConfigParser): The configuration parser object.
        section (str): The section in the configuration file.
        option (str): The option under the section whose value is to be retrieved.

    Returns:
        list: A list of values for the specified option. Returns an empty list in case of improper formatting.
    """

    try:
        value = config.get(section, option, fallback="[]")
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        # In case of improper formatting, return an empty list
        return []

def set_mappings(config, section, option, new_value):
    """
    Updates the configuration by adding a new value to the existing list of mappings if it doesn't already exist.

    Args:
        config (configparser.ConfigParser): The configuration parser object.
        section (str): The section in the configuration file.
        option (str): The option under the section whose value is to be updated.
        new_value (str): The new value to be added to the list of mappings.
    
    Actions:
        - Appends the new value to the list of mappings if it is not already present.
        - Updates the configuration object with the new list of mappings.
    """

    current_mappings = get_mappings(config, section, option)
    if new_value not in current_mappings and new_value != '':
        current_mappings.append(new_value)
    config.set(section, option, str(current_mappings))

def str_to_bool(string_value):
    """
    Converts a string representation of a boolean to a boolean value.

    Args:
        string_value (str): The string to convert (e.g., 'true', '1', 'yes', 'y').

    Returns:
        bool: The corresponding boolean value. Returns True for 'true', '1', 'yes', 'y' (case-insensitive),
        and False otherwise.
    """

    return string_value.lower() in ['true', '1', 'yes', 'y']

def map_skill(user_input, predefined_skills, threshold=80):
    """
    Matches a user input skill to a predefined skill list using fuzzy matching.

    Args:
        user_input (str): The skill input provided by the user.
        predefined_skills (list): A list of predefined skills to match against.
        threshold (int, optional): The matching threshold score (default is 80).

    Returns:
        str or None: The best matching skill if the score exceeds the threshold; otherwise, returns None.
    """
    
    best_match, score = process.extractOne(
        user_input,
        predefined_skills,
        score_cutoff=threshold
    )

    if best_match:
        return best_match
    return None