import os
import json

def get_var(key, file_path=os.path.join("..", "assets", "vars.private.json")):
    try:
        # Construct the full path to the file in subDirA2

        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            if key in data:
                return data[key]
            else:
                return None  # Key not found in the JSON data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON format in file: {file_path}")
        return None
