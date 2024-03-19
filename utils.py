import requests
import os
import time
from pathlib import Path
import yaml
import json
import shutil
from zipfile import ZipFile 
import ast


counter_request = 0
total_request = 0


def delete_folder_if_exist(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory, ignore_errors=True)


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
    if counter_request >= 15:
        counter_request = 0
        time.sleep(1)

    r = requests.get(path, params)
    counter_request += 1
    total_request += 1
    return r.json()


def download_url_file(url, destination, nom_fichier=None):
    try:
        reponse = requests.get(url)
        if reponse.status_code == 200:
            if nom_fichier is None:
                nom_fichier = os.path.basename(url)
            destination_fichier = os.path.join(destination, nom_fichier)
            with open(destination_fichier, 'wb') as fichier:
                fichier.write(reponse.content)
    except Exception as e:
        print(f"Download error : {e}")


def unzip_file(path_from, path_to):
    with ZipFile(path_from, 'r') as zip_file: 
        zip_file.extractall(path=path_to)
    delete_files_if_exist([path_from])


def get_files(path, type=None):
    if not os.path.isdir(path):
        return []
    
    fichiers = []

    for element in os.listdir(path):
        chemin = os.path.join(path, element)
        
        if type is None:
            if os.path.isfile(chemin):
                fichiers.append(chemin)
        else:
            if os.path.isfile(chemin) and str(element).endswith("."+type):
                fichiers.append(chemin)
    
    return fichiers


def extract_txt_data(file):
    datas = {}

    with open(file, 'r') as f:
        lignes = f.readlines()

        for ligne in lignes:
            ligne = ligne.strip()

            key = ligne[:ligne.index(":")]
            if '[' in ligne and ']' in ligne:
                data = ligne[ligne.index("[")+1:ligne.index("]")].split(",")
            else:
                data = ligne[ligne.index(":")+1:]

            datas[key] = data

    return datas


def merge_options(data1: dict, data2: dict):
    data = data1.copy()
    for key, val in data2.items():
        try:
            if data[key] is not None and isinstance(data[key], list):
                data[key] += val
                continue
        except:
            pass
        data[key] = val
    return data


def dict_to_txt(dictionary, file_path):
    with open(file_path, 'w') as file:
        for key, value in dictionary.items():
            if isinstance(value, list):
                value = '[' + ', '.join(map(str, value)) + ']'
            line = f"{key}:{value}\n"
            file.write(line)


def copy_file(source, destination):
    shutil.copy(source, destination)


def get_total_request():
    return total_request
