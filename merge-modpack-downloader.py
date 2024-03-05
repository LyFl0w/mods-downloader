import requests
import json
import time

modsLoaderType =  {"Forge" : 1, "Cauldron" : 2, "LiteLoader" : 3, "Fabric" : 4, "Quilt" : 5, "NeoForge" : 6}
api = "https://api.curse.tools/v1/cf"
curse_forge_api = "https://www.curseforge.com/api/v1"
counter_request = 0
total_request = 0


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
    

def filter_on(files, path, contain_data):
    return [file for file in files if all(data in file[path] for data in contain_data)]


def get_name_id(path, filter, params=None):
        r = request(f'{api}/{path}', params)
        data = r["data"]
        data = filter_on(data, "name", [filter])
        return data[0]["id"]


def setup_target_mod(mods_id, mods_name, file_path):
    minecraft_id = get_name_id("games", "Minecraft")
    mods_categorie_id = get_name_id("categories", "Mods", params={'gameId' : minecraft_id})
    modpacks_categorie_id = get_name_id("categories", "Modpacks", params={'gameId' : minecraft_id})

    def get_class_id(name: str):
        if name.startswith("p:"):
            return (modpacks_categorie_id, name[2:])
        return (mods_categorie_id, name)


    with open(file_path, 'r') as file:
        lines = file.readlines()
        loader_info = lines[0][:-1].split(" ")
        loader_id = modsLoaderType[loader_info[0]]
        
        for line in lines[1:]:
            class_id, search = get_class_id(line.split(" - ")[0])
            print(class_id, search)
            index = 0
            r = []
            
            while len(r) == 0 and index + 50 <= 10_000:
                r = request(f'{curse_forge_api}/mods/search', params={'gameId' : minecraft_id, 'classId' : class_id, 'filterText': search,
                                                            'gameFlavorId' : loader_id, 'index': index, 'sortField': 1})
                if "data" not in r:
                    break

                r = filter_on(r["data"], "name", search)
                index += 50

            if isinstance(r, dict) or index + 50 > 10_000:
                print(f"mod not found : {search}")
                continue

            mod = r[0]
            mod_id = mod['id']

            mods_id.append(mod_id)
            mods_name[mod_id] = search
        
        return loader_info, len(lines)-1


def setup_mod_id(mods_id, require_depencies, incompatible_dependencies, mods_link, mods_name, loader_info):
    loader_id = modsLoaderType[loader_info[0]]
    game_version = loader_info[1]

    def setup_mod(mod_id):
        download_url = request(f'{curse_forge_api}/mods/{mod_id}/files', params={'sort': 'dateCreated', 'sortDescending' : 'true', 'gameFlavorId' : loader_id,
                                                                                 'removeAlphas': 'true'})
        if "data" not in download_url:
            print(f'{mods_name[mod_id]} not found in {loader_info[0]} {game_version}')
            return
        
        download_url = filter_on(download_url["data"], "gameVersions", loader_info)
        if len(download_url) == 0:
            print(f'{mods_name[mod_id]} not found in {loader_info[0]} {game_version}')
            return
        download_url = download_url[0]

        dependencies = request(f'{curse_forge_api}/mods/{mod_id}/dependencies')

        if "data" in dependencies:
            for dependency in dependencies["data"]:
                dependency_name = dependency["name"]
                dependency_id = dependency["id"]
                relation = dependency["type"]
                
                mods_name[dependency_id] = dependency_name

                data = (mod_id, dependency_id)
                is_already = False
                if relation == "RequiredDependency":
                    for _, require_depency in require_depencies:
                        if require_depency == dependency_id:
                            is_already = True
                            break

                    if not is_already:
                        require_depencies.append(data)

                elif relation == "Incompatible":
                    for _, require_depency in incompatible_dependencies:
                        if require_depency == dependency_id:
                            is_already = True
                            break

                    if not is_already:
                        incompatible_dependencies.append(data)

        total_id = str(download_url["id"])
        first_id = total_id[:4].lstrip('0')
        second_id = total_id[4:].lstrip('0')
        #download_id = str(download_url["id"])
        #mods_link.append((mod_id, download_id))
        mods_link.append(f'https://mediafilez.forgecdn.net/files/{first_id}/{second_id}/{download_url["fileName"].replace("+", "%2B")}')


    for mod_id in mods_id:
        setup_mod(mod_id)
    
    for require_depency in require_depencies:
        setup_mod(require_depency[1])


def check_incompatibility(mods_id, require_depencies, incompatible_dependencies):

    def detect_incompatibilities(target, mods_id, require_dependencies):
        target_id, incompatible_id = target
        incompatibilities = [target_id]

        # Vérifier si le mod cible est dans les dépendances requises
        for (mod_id, required_id) in require_dependencies:
            if incompatible_id == required_id :
                incompatibilities.append(required_id)

        # Vérifier les incompatibilités directes avec le mod cible

        return incompatibilities
    

    check_result = False

    for mod_id in incompatible_dependencies:
        detected_incompatibilities = detect_incompatibilities(mod_id, mods_id, require_depencies)
        if len(detected_incompatibilities) > 1:
            check_result = True
            print(f"Incompatibilités détectées avec le mod {mods_name[mod_id[1]]}:")
            for incompatibility in detected_incompatibilities:
                print(f"- Mod {mods_name[incompatibility]}")
    
    return check_result


def write_links_to_file(links, file_path):
    with open(file_path, 'w') as file:
        for link in links:
            file.write(link + '\n')


if __name__ == "__main__":
    # mods id contain in file
    mods_id = []

    # id : string
    mods_name = {}

    # (target_id, require_id)
    require_depencies = []

    # (target_id, incompatible_id)
    incompatible_dependencies = []

    # all mods links to download
    mods_link = []

    data_pack_link = []

    loader_info, mods_number = setup_target_mod(mods_id, mods_name, "mods.txt")
    print(f'detected info : {loader_info}')
    print(f'detected mods in file : {mods_number}')
    print(f'detected mods by name on curseforge : {len(mods_id)}')
    print(f'names : {mods_name}')
    print(f'total requests : {total_request}')

    setup_mod_id(mods_id, require_depencies, incompatible_dependencies, mods_link, mods_name, loader_info)
    print(f'names : {mods_name}')
    print(f'total mods to download : {len(mods_link)}')
    print(f'require : {require_depencies}')
    print(f'incompatibility : {incompatible_dependencies}')
    print(f'total requests : {total_request}')

    if check_incompatibility(mods_id, require_depencies, incompatible_dependencies):
        print("S'il vous plait, mettez à jour votre liste de mods !")
        #exit(-1)

    write_links_to_file(mods_link, "mods_link.txt")
