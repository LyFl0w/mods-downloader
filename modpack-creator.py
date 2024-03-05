from utils import *

api = "https://api.curse.tools/v1/cf"
curse_forge_api = "https://www.curseforge.com/api/v1"

data_path = "data/"
datapack_path = "datapack/"


def filter_on(files, path, contain_data):
    return [file for file in files if all(data in file[path] for data in contain_data)]


def get_name_id(path, filter, params=None):
        r = request(f'{api}/{path}', params)
        data = r["data"]
        data = filter_on(data, "name", [filter])
        return data[0]["id"]


mods_loader_type =  {"Forge" : 1, "Cauldron" : 2, "LiteLoader" : 3, "Fabric" : 4, "Quilt" : 5, "NeoForge" : 6}
minecraft_id = get_name_id("games", "Minecraft")
mods_categorie_id = get_name_id("categories", "Mods", params={'gameId' : minecraft_id})
modpacks_categorie_id = get_name_id("categories", "Modpacks", params={'gameId' : minecraft_id})


def mod_id_already_save(name):
    pass


def setup_target_mod(mods_id, mods_name, loader_id):
    lines = read_file("mods.txt")
    print(f'detected mods in file : {mods_number}')

    for line in lines:
        mod_name = line.split(" - ")[0]
        index = 0
        r = []
            
        while len(r) == 0 and index + 50 <= 10_000:
            r = request(f'{curse_forge_api}/mods/search', params={'gameId' : minecraft_id, 'classId' : mods_categorie_id, 'filterText': mod_name,
                                                            'gameFlavorId' : loader_id, 'index': index, 'sortField': 1})
            if "data" not in r:
                break

            r = filter_on(r["data"], "name", mod_name)
            index += 50

        if isinstance(r, dict) or index + 50 > 10_000:
            print(f"mod not found : {mod_name}")
            print(r)
            continue

        mod = r[0]
        mod_id = mod['id']

        mods_id.append(mod_id)
        mods_name[mod_id] = mod_name


def setup_target_modpack(loader_id):
    lines = read_file("modpacks.txt")
    print(f'detected modpacks in file : {len(lines)}')

    to_write = []

    for line in lines:
        modpack_name = line.split(" - ")[0]
        index = 0
        r = []
            
        while len(r) == 0 and index + 50 <= 10_000:
            r = request(f'{curse_forge_api}/mods/search', params={'gameId' : minecraft_id, 'classId' : modpacks_categorie_id, 'filterText': modpack_name,
                                                            'gameFlavorId' : loader_id, 'index': index, 'sortField': 1})
            if "data" not in r:
                break

            r = filter_on(r["data"], "name", modpack_name)
            index += 50

        if "data" not in r or index + 50 > 10_000:
            print(f"modpack not found : {modpack_name}")
            print(r)
            continue

        modpack_id = r[0]['id']
        dependencies = request(f'{curse_forge_api}/mods/{modpack_id}/dependencies', params={'type' : 'Include'})["data"]

        for dependency in dependencies:
            mod_id = dependency["id"]
            mod_name = dependency["name"]
            curse_forge_link = "https://www.curseforge.com/minecraft/mc-mods/"+dependency["slug"]
            
            
            to_write.append(f'{mod_name} - {mod_id} - {curse_forge_link}')

    
    write_file(to_write, data_path, "infmods_modpacks.txt")


def setup_mod_id(mods_id, require_depencies, incompatible_dependencies, mods_link, mods_name, loader_info):
    loader_id = mods_loader_type[loader_info[0]]
    game_version = loader_info[1]

    def setup_mod(mod_id):
        download_url = request(f'{curse_forge_api}/mods/{mod_id}/files', params={'sort': 'dateCreated', 'sortDescending' : 'true', 'gameFlavorId' : loader_id,
                                                                                 'removeAlphas': 'true'})
        #print(download_url)
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


if __name__ == "__main__":
    # mods_id -> id - name - links
    create_files_if_not_exist(data_path, ["mods_id.txt", "infmods.txt", "infmods_modpacks.txt"])
    
    # id : string
    mods_name = {}

    # (target_id, require_id)
    require_depencies = []

    # (target_id, incompatible_id)
    incompatible_dependencies = []

    # all mods links to download
    mods_link = []

    loader_info = read_file("config.txt")[0].split(" ")
    loader_info.append(mods_loader_type[loader_info[0]])
    print(f'detected info : {loader_info}')

    setup_target_mod(mods_id, mods_name, loader_info[2])
    print(f'detected mods by name on curseforge : {len(mods_id)}')
    print(f'names : {mods_name}')

    setup_target_modpack(loader_info)

    setup_mod_id(mods_id, require_depencies, incompatible_dependencies, mods_link, mods_name, loader_info)
    print(f'names : {mods_name}')
    print(f'total mods to download : {len(mods_link)}')
    print(f'require : {require_depencies}')
    print(f'incompatibility : {incompatible_dependencies}')
    print(f'\ntotal requests : {total_request}')

    if check_incompatibility(mods_id, require_depencies, incompatible_dependencies):
        print("S'il vous plait, mettez à jour votre liste de mods !")
        #exit(-1)

    write_file(mods_link, data_path, "infmods.txt")
