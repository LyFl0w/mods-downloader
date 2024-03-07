from utils import *

api = "https://api.curse.tools/v1/cf"
curse_forge_api = "https://www.curseforge.com/api/v1"

spliter = " &/& "
data_path = "data/"
datapack_path = "datapack/"


def filter_on(files, path, contain_data):
    return [file for file in files if all(data in file[path] for data in contain_data)]


def accepted_filter_on(files, path, contain_data: list, check_loader=True):
    if not accepted_filter:
        return filter_on(files, path, contain_data)
    
    res = []
    for file in files:
        file_data = file[path]
        if not check_loader or loader_info[0] in file_data:
            for data in contain_data:
                if data.count(".") == 1:
                    if data == file_data:
                        res.append(file)
                        break

                elif data in file_data:
                    res.append(file)
                    break

    tmp_res = filter_on(res, path, [contain_data[0]])
    if len(tmp_res) > 0:
        return tmp_res
    return res


def get_name_id(path, filter, params=None):
        return get_specific_name_id(path, 0, "name", filter, params)


def get_specific_name_id(path, specific, rule, filter, params=None):
        r = request(f'{api}/{path}', params)
        data = r["data"]
        data = filter_on(data, rule, [filter])
        return data[specific]["id"]


accepted_filter = False
mods_loader_type =  {"Forge" : 1, "Cauldron" : 2, "LiteLoader" : 3, "Fabric" : 4, "Quilt" : 5, "NeoForge" : 6}
minecraft_id = get_name_id("games", "Minecraft")
mods_categorie_id = get_name_id("categories", "Mods", params={'gameId' : minecraft_id})
modpacks_categorie_id = get_name_id("categories", "Modpacks", params={'gameId' : minecraft_id})
resourcepacks_categorie_id = get_specific_name_id("categories", 1, "name", "Resource Packs", params={'gameId' : minecraft_id})


def get_id_files_content():
    content = {}
    link = {}
    for file in ["mods_id.txt", "modpacks_id.txt", "resourcepacks_id.txt"]:
        lines = read_file(data_path+file)
        for line in lines:
            split = line.split(f"{spliter}")
            content[split[0]] = split[1]
            link[split[1]] = split[2]
    return content, link


def add_to_list(id, name, file):
    if file.startswith("mod"):
        if id not in mods_id:
            mods_id.append(id)
    elif file.startswith("resourcepack"):
        if id not in textures_id:
            textures_id.append(id)
    else:
        print(f"list not found {file}")
    
    content_id[name] = id


def is_already_save(name):
    return name in content_id.keys()


def get_id_save(name):
    return content_id[name]
    

def get_name_save(id):
    for name_save, id_save in content_id.items():
        if id == id_save:
            return name_save
    return -1


def get_mod_link(mod_id):
    if mod_id in link_id.keys():
        return link_id[mod_id]
    return "Not Found"


def setup_target_mod(loader_id):
    lines = read_file("mods.txt")
    print(f'detected mods in file : {len(lines)}')

    to_write = []
    for line in lines:
        mod_name = line.split(f"{spliter}")[0]

        if is_already_save(mod_name):
            add_to_list(get_id_save(mod_name), mod_name, "mod")
            continue
            
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
        mod_name = mod['name']
        curse_forge_link = "https://www.curseforge.com/minecraft/mc-mods/"+mod["slug"]

        if not is_already_save(mod_name):
            to_write.append(f'{mod_name}{spliter}{mod_id}{spliter}{curse_forge_link}')
        add_to_list(mod_id, mod_name, "mod")

    if len(to_write) > 0:
        write_file(to_write, data_path, "mods_id.txt")


def setup_target_modpack_mod(loader_id):
    lines = read_file("modpacks.txt")
    print(f'detected modpacks in file : {len(lines)}')

    to_write_modpacks = []
    to_write_mods = []
    to_write_textures = []
    for line in lines:
        modpack_id = -1
        modpack_name = line.split(f"{spliter}")[0]

        if is_already_save(modpack_name):
            modpack_id = get_id_save(modpack_name)

        index = 0
        r = []
        
        if modpack_id == -1:
            while len(r) == 0 and index + 50 <= 10_000:
                r = request(f'{curse_forge_api}/mods/search', params={'gameId' : minecraft_id, 'classId' : modpacks_categorie_id, 'filterText': modpack_name,
                                                                'gameFlavorId' : loader_id, 'index': index, 'sortField': 1})
                if "data" not in r:
                    break

                r = filter_on(r["data"], "name", modpack_name)
                index += 50

            if isinstance(r, dict) or index + 50 > 10_000:
                print(f"modpack not found : {modpack_name}")
                print(r)
                continue
            
            modpack = r[0]
            modpack_id = modpack['id']
            curse_forge_link = "https://www.curseforge.com/minecraft/modpacks/"+modpack["slug"]
            to_write_modpacks.append(f'{modpack_name}{spliter}{modpack_id}{spliter}{curse_forge_link}')


        dependencies = request(f'{curse_forge_api}/mods/{modpack_id}/dependencies', params={'type' : 'Include'})["data"]

        for dependency in dependencies:
            mod_name = dependency["name"]
            mod_id = dependency["id"]
            categorie_id = dependency["categoryClass"]["id"]

            curse_forge_link = "https://www.curseforge.com/minecraft"
            to_write = f'{mod_name}{spliter}{mod_id}{spliter}{curse_forge_link}'

            is_not_save = not is_already_save(mod_name)
            cat = ""

            if categorie_id == mods_categorie_id:
                if is_not_save:
                    to_write += "/mc-mods/"+dependency["slug"]
                    to_write_mods.append(to_write)
                
                cat = "mod"
                
            elif categorie_id == resourcepacks_categorie_id:
                if is_not_save:
                    to_write += "/texture-packs/"+dependency["slug"]
                    to_write_textures.append(to_write)
                cat = "resourcepack"
            
            if cat != "":
                add_to_list(mod_id, mod_name, cat)
            else:
                print(f"pas de cat : {mod_name}")
    
    if len(to_write_modpacks) > 0:
        write_file(to_write_modpacks, data_path, "modpacks_id.txt")

    if len(to_write_mods) > 0:
        write_file(to_write_mods, data_path, "mods_id.txt")

    if len(to_write_textures) > 0:
        write_file(to_write_textures, data_path, "resourcepacks_id.txt")


def setup_mod_id():
    loader_name = loader_info[0]
    loader_id = mods_loader_type[loader_name]
    game_version = loader_info[1]

    def setup_mod(mod_id):
        file = request(f'{curse_forge_api}/mods/{mod_id}/files', params={'sort': 'dateCreated', 'sortDescending' : 'true', 'gameFlavorId' : loader_id,
                                                                                 'removeAlphas': modpack_info_remove_alpha})
        if "data" not in file:
            print(f'{get_name_save(mod_id)} not found in {loader_name} {game_version}')
            return
        
        to_filter = [game_version]
        if accepted_filter:
            to_filter += modpack_info_data_supp

        file = accepted_filter_on(file["data"], "gameVersions", to_filter)
        if len(file) == 0:
            print(f'{get_name_save(mod_id)} not found in {loader_name} {game_version}')
            return
        
        dependencies = request(f'{curse_forge_api}/mods/{mod_id}/dependencies')

        if "data" in dependencies:
            to_write = []
            for dependency in dependencies["data"]:
                dependency_name = dependency["name"]
                dependency_id = dependency["id"]
                relation = dependency["type"]
                
                if relation == "RequiredDependency":
                    if not is_already_save(dependency_name):
                        curse_forge_link = "https://www.curseforge.com/minecraft/mc-mods/"+dependency["slug"]
                        to_write.append(f'{dependency_name}{spliter}{dependency_id}{spliter}{curse_forge_link}')
                    if dependency_name == "Kotlin for Forge":
                        print(f"{mod_id} Kotlin for Forge")
                    add_to_list(dependency_id, dependency_name, "mod")

            if len(to_write) > 0: 
                write_file(to_write, data_path, "mods_id.txt")
                
        file = file[0]
        file_id = file["id"]
        files.append((int(mod_id), int(file_id)))

    for mod_id in mods_id:
        print(mod_id)
        setup_mod(mod_id)


def setup_texturepacks_id():
    game_version = loader_info[1]

    def setup_texture(mod_id):
        file = request(f'{curse_forge_api}/mods/{mod_id}/files', params={'sort': 'dateCreated', 'sortDescending' : 'true', 'removeAlphas': modpack_info_remove_alpha})
        if "data" not in file:
            print(f'{get_name_save(mod_id)} not found in {game_version}')
            return

        to_filter = [game_version]
        if accepted_filter:
            to_filter += modpack_info_data_supp
        file = accepted_filter_on(file["data"], "gameVersions", to_filter, False)
        if len(file) == 0:
            print(f'{get_name_save(mod_id)} not found in {game_version}')
            return
        
        file = file[0]
        file_id = file["id"]
        files.append((int(mod_id), int(file_id)))

    for texture_id in textures_id:
        setup_texture(texture_id)


def create_mods_pack():
    delete_folder_if_exist(datapack_path)
    
    os.mkdir(datapack_path)
    create_files_if_not_exist(datapack_path, ["manifest.json", "modlist.html"])

    manifest = {
        "minecraft": {
            "version": modpack_info["minecraft"]["version"],
            "modLoaders": [
            {
                "id": "fabric-0.15.7",
                "primary": True
            }
            ]
        },
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": modpack_info["modpack"]["name"],
        "version": modpack_info["modpack"]["version"],
        "author": modpack_info["modpack"]["author"],
        "files": [],
        "overrides": "overrides"
    }
    

    modlist = "<ul>"
    for file in files:
        project_id = file[0]
        manifest["files"].append({
                "projectID": project_id,
                "fileID": file[1],
                "required": True
            })
        
        modlist += f"\n<li><a href=\"{get_mod_link(str(project_id))}\">{get_name_save(project_id)}</a></li>"
    modlist += "\n</ul>"
    
    write_file([json.dumps(manifest, indent=1)], datapack_path, "manifest.json")
    write_file([modlist], datapack_path, "modlist.html")

    file_name = f'{manifest["name"]}-{manifest["minecraft"]["version"]}-{manifest["version"]}'
    delete_files_if_exist([file_name])
    shutil.make_archive(file_name, 'zip', datapack_path)


if __name__ == "__main__":
    create_files_if_not_exist(data_path, ["mods_id.txt", "modpacks_id.txt", "resourcepacks_id.txt"])
    
    modpack_info = read_yaml_file("config.yml")
    modpack_info_data_supp = modpack_info["minecraft"]["accepted"]
    modpack_info_remove_alpha = str(modpack_info["minecraft"]["remove-alpha"]).lower()
    accepted_filter = len(modpack_info_remove_alpha) > 0

    # name : id
    content_id, link_id = get_id_files_content()

    mods_id = []
    textures_id = []

    # all mods links to download
    files = []

    loader_info = [modpack_info["minecraft"]["loader"], modpack_info["minecraft"]["version"]]
    print(f'detected info : {loader_info}')

    setup_target_modpack_mod(loader_info)
    setup_target_mod(mods_loader_type[loader_info[0]])
    print(f'detected mods on curseforge : {len(mods_id)}')

    setup_mod_id()
    setup_texturepacks_id()
    print(f'\ntotal mods to download : {len(mods_id)}')
    print(f'total texturepacks to download : {len(textures_id)}')
    print(f'\ntotal requests : {get_total_request()}')

    print(mods_id)

    create_mods_pack()
    #write_file(files, data_path, "infmods.txt")
