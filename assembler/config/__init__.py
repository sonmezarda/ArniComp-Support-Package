import json

config_file = "config/config.json"

def get_config_file():
    file = open(config_file, 'r')    
    return json.loads(file.read())

config = get_config_file()
instructions = config["instructions"]
argcode_types = config["argcode_types"]
opcode_types = config["opcode_types"]