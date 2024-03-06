import requests
import os
import time
from pathlib import Path
import yaml
import json

counter_request = 0
total_request = 0


def delete_folder_if_exist(directory):
    if os.path.exists(directory):
        os.rmdir(directory)


def delete_files_if_exist(files):
    for file in files:
        if os.path.exists(file):
            os.remove(file)


def create_files_if_not_exist(path=None, files=None):
    start_path = ""
    if path is not None:
        start_path = path
        
    for file in files:
        real_path = get_real_path(start_path, file)
        if not os.path.exists(real_path):
            write_file([], path, file)

def get_real_path(path, file_name):
    if path.endswith("/"):
        return path+file_name
    elif file_name.startswith("./"):
        return path+file_name[1:]
    else:
        return path+"/"+file_name


def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()


def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def write_file(datas, path=None, file_name=None):
    file_path = file_name
    if path is not None:
        Path(path).mkdir(parents=True, exist_ok=True)
        file_path = get_real_path(path, file_name)

    with open(file_path, 'a+') as file:
        for data in datas:
            file.write(data + '\n')


def request(path, params=None):
    global counter_request, total_request

    # module anti spam / ddos
    if counter_request >= 1500:
        counter_request = 0
        time.sleep(1)

    r = requests.get(path, params)
    counter_request += 1
    total_request += 1
    return r.json()