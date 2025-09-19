import json

config_file = "config/config.json"

def get_config_file():
    file = open(config_file, 'r')    
    return json.loads(file.read())

