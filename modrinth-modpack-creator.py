import urllib.request
from utils import *

api = "https://staging-api.modrinth.com/v2"

spliter = " &/& "
data_path = "data/"
modpacks_path = "modpacks/"


def filter_on(files, path, contain_data):
    return [file for file in files if all(data in file[path] for data in contain_data)]


def accepted_filter_on(files, path, contain_data: list):
    if not accepted_filter:
        return filter_on(files, path, contain_data)
    
    res = []
    for file in files:
        file_data = file[path]
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
        if id not in resourcepacks_id:
            resourcepacks_id.append(id)
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


def setup_target_mod():
    lines = read_file("mods.txt")
    print(f'detected mods in file : {len(lines)}')

    to_write = []
    for line in lines:
        mod_name = line.split(f"{spliter}")[0]

        if is_already_save(mod_name):
            add_to_list(get_id_save(mod_name), mod_name, "mod")
            continue

        r = request(f'{api}/search', params={'categories' : loader_info[0], 'project_type' : "mod", 'query': mod_name})
        if r["total_hits"] == 0:
            print(f"mod not found : {mod_name}")
            print(r)
            continue
            
        r = filter_on(r["hits"], "title", mod_name)

        if isinstance(r, dict):
            print(f"mod not found : {mod_name}")
            print(r)
            continue

        mod = r[0]
        mod_id = mod['project_id']
        mod_name = mod['title']
        modrinth_link = "https://modrinth.com/mod/"+mod["slug"]

        if not is_already_save(mod_name):
            to_write.append(f'{mod_name}{spliter}{mod_id}{spliter}{modrinth_link}')

        add_to_list(mod_id, mod_name, "mod")

    if len(to_write) > 0:
        write_file(to_write, data_path, "mods_id.txt")


def setup_target_resourcepacks():
    lines = read_file("resourcepacks.txt")
    print(f'detected resourcepacks in file : {len(lines)}')

    to_write = []
    for line in lines:
        resourcepack = line.split(f"{spliter}")[0]

        if is_already_save(resourcepack):
            add_to_list(get_id_save(resourcepack), resourcepack, "resourcepack")
            continue

        r = request(f'{api}/search', params={'categories' : loader_info[0], 'project_type' : "resourcepack", 'query': resourcepack})
        if r["total_hits"] == 0:
            print(f"resourcepack not found : {resourcepack}")
            print(r)
            continue
            
        r = filter_on(r["hits"], "title", resourcepack)

        if isinstance(r, dict):
            print(f"resourcepack not found : {resourcepack}")
            print(r)
            continue

        mod = r[0]
        mod_id = mod['project_id']
        resourcepack = mod['title']
        modrinth_link = "https://modrinth.com/resourcepack/"+mod["slug"]

        if not is_already_save(resourcepack):
            to_write.append(f'{resourcepack}{spliter}{mod_id}{spliter}{modrinth_link}')
        add_to_list(mod_id, resourcepack, "resourcepack")

    if len(to_write) > 0:
        write_file(to_write, data_path, "resourcepacks_id.txt")


def setup_target_modpack_mod():
    lines = read_file("modpacks.txt")
    print(f'detected modpacks in file : {len(lines)}')

    loader_version = loader_info[0]
    game_version = loader_info[1]
    to_filter = [game_version]
    if accepted_filter:
        to_filter += modpack_info_data_supp

    to_write_modpacks = []
    to_write_mods = []
    to_write_resourcepacks = []
    for line in lines:
        modpack_id = -1
        modpack_name = line.split(f"{spliter}")[0]

        if is_already_save(modpack_name):
            modpack_id = get_id_save(modpack_name)

        r = []
        
        if modpack_id == -1:
            r = request(f'{api}/search', params={'categories' : loader_info[0], 'project_type' : "modpack", 'query': modpack_name})
            if r["total_hits"] == 0:
                print(f"modpack not found : {modpack_name}")
                print(r)
                continue
                
            r = filter_on(r["hits"], "title", modpack_name)

            if isinstance(r, dict):
                print(f"modpack not found : {modpack_name}")
                print(r)
                continue

            modpack = r[0]
            modpack_id = modpack['project_id']
            modpack_name = modpack['title']
            modrinth_link = "https://modrinth.com/modpack/"+modpack["slug"]

            if not is_already_save(project_name):
                to_write_modpacks.append(f'{modpack_name}{spliter}{modpack_id}{spliter}{modrinth_link}')
        
        dependencies = request(f'{api}/project/{modpack_id}/dependencies')["projects"]
        dependencies = accepted_filter_on(dependencies, "loaders", [loader_version])
        dependencies = accepted_filter_on(dependencies, "game_versions", to_filter)
        
        for dependency in dependencies:
            project_name = dependency["title"]
            project_id = dependency["project_id"]
            project_type = dependency["project_type"]

            modrinth_link = f"https://modrinth.com/{project_type}/{dependency["slug"]}"
            to_write = f'{project_name}{spliter}{project_id}{spliter}{modrinth_link}'
            
            if not is_already_save(project_name):
                if project_type == "mod":
                    to_write_mods.append(to_write)
                elif project_type == "resourcepack":
                    to_write_resourcepacks.append(to_write)
                else:
                    continue

            add_to_list(project_id, project_name, project_type)
    
    if len(to_write_modpacks) > 0:
        write_file(to_write_modpacks, data_path, "modpacks_id.txt")

    if len(to_write_mods) > 0:
        write_file(to_write_mods, data_path, "mods_id.txt")

    if len(to_write_resourcepacks) > 0:
        write_file(to_write_resourcepacks, data_path, "resourcepacks_id.txt")


def setup_mod_id():
    loader_name = loader_info[0]
    loader_id = mods_loader_type[loader_name]
    game_version = loader_info[1]

    def setup_mod(mod_id):
        file = request(f'{api}/mods/{mod_id}/files', params={'sort': 'dateCreated', 'sortDescending' : 'true', 'gameFlavorId' : loader_id,
                                                                                 'removeAlphas': modpack_info_remove_alpha})
        if "data" not in file:
            print(f'{get_name_save(mod_id)} not found in {loader_name} {game_version}')
            return
        
        to_filter = [game_version]
        if accepted_filter:
            to_filter += modpack_info_data_supp

        file = accepted_filter_on(file["data"], "gameVersions", to_filter)
        file = accepted_filter_on(file["data"], "loader", "TODO : HERE")
        if len(file) == 0:
            print(f'{get_name_save(mod_id)} not found in {loader_name} {game_version}')
            return
        
        dependencies = request(f'{api}/mods/{mod_id}/dependencies')

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
        setup_mod(mod_id)


def setup_texturepacks_id():
    game_version = loader_info[1]

    def setup_texture(mod_id):
        file = request(f'{api}/mods/{mod_id}/files', params={'sort': 'dateCreated', 'sortDescending' : 'true', 'removeAlphas': modpack_info_remove_alpha})
        if "data" not in file:
            print(f'{get_name_save(mod_id)} not found in {game_version}')
            return

        to_filter = [game_version]
        if accepted_filter:
            to_filter += modpack_info_data_supp
        file = accepted_filter_on(file["data"], "gameVersions", to_filter)
        if len(file) == 0:
            print(f'{get_name_save(mod_id)} not found in {game_version}')
            return
        
        file = file[0]
        file_id = file["id"]
        files.append((int(mod_id), int(file_id)))

    for texture_id in resourcepacks_id:
        setup_texture(texture_id)


def create_mods_pack():
    delete_folder_if_exist(modpacks_path)
    os.mkdir(modpacks_path)

    build_info = modpack_info["build"]
    modpack_inf = modpack_info["modpack"]

    modpack_version = modpack_inf["version"]
    modpack_author = modpack_inf["author"]
    modpack_name = modpack_inf["name"].replace("$VERSION", modpack_version)

    minecraft_version = modpack_info["minecraft"]["version"]
    
    if build_info["curseforge-modpack-zip"] == True:
        create_files_if_not_exist(modpacks_path, ["manifest.json", "modlist.html"])

        loader_version = ""
        if loader_info[0] == "Fabric":
            loader_version = f'fabric-{request("https://meta.fabricmc.net/v2/versions/loader/")[0]["version"]}'

        manifest = {
            "minecraft": {
                "version": minecraft_version,
                "modLoaders": [
                {
                    "id": loader_version,
                    "primary": True
                }
                ]
            },
            "manifestType": "minecraftModpack",
            "manifestVersion": 1,
            "name": modpack_name,
            "version": modpack_version,
            "author": modpack_author,
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
        
        write_file([json.dumps(manifest, indent=1)], modpacks_path, "manifest.json")
        write_file([modlist], modpacks_path, "modlist.html")

        file_path = f'{modpacks_path}/curseforge'
        os.mkdir(file_path)

        shutil.make_archive(f"{file_path}/{modpack_name}-{modpack_version}", 'zip', modpacks_path)
    
    if build_info["classic-zip-folder"] == True:
        default_file_path = modpacks_path+"classic/"
        os.mkdir(default_file_path)
        os.mkdir(default_file_path+"mods/")
        os.mkdir(default_file_path+"resourcepacks/")

        for file in files:
            mod_id = file[0]
            file_id = file[1]
            file_data = request(f"{api}/mods/{mod_id}/files/{file_id}")["data"]

            file_name = file_data["fileName"]
            file_url = file_data["downloadUrl"]
            
            file_path = default_file_path
            if file_name.endswith(".jar"):
                file_path += "mods/"
            else:
                file_path += "resourcepacks/"
            
            urllib.request.urlretrieve(file_url, file_path+file_name)
        shutil.make_archive(f"{default_file_path}/{modpack_name}-{modpack_version}", 'zip', default_file_path)


if __name__ == "__main__":
    create_files_if_not_exist(data_path, ["mods_id.txt", "modpacks_id.txt", "resourcepacks_id.txt"])
    
    modpack_info = read_yaml_file("config.yml")
    modpack_info_data_supp = modpack_info["minecraft"]["accepted"]
    modpack_info_remove_alpha = str(modpack_info["minecraft"]["remove-alpha"]).lower()
    accepted_filter = len(modpack_info_remove_alpha) > 0

    # name : id
    content_id, link_id = get_id_files_content()

    mods_id = []
    resourcepacks_id = []

    # all mods links to download
    files = []

    loader_info = [modpack_info["minecraft"]["loader"].lower(), modpack_info["minecraft"]["version"]]
    print(f'detected info : {loader_info}')

    setup_target_modpack_mod(loader_info)
    setup_target_mod(mods_loader_type[loader_info[0]])
    setup_target_resourcepacks()
    print(f'detected mods on curseforge : {len(mods_id)}')

    setup_mod_id()
    setup_texturepacks_id()
    print(f'\ntotal mods to download : {len(mods_id)}')
    print(f'total texturepacks to download : {len(resourcepacks_id)}')
    print(f'\ntotal requests : {get_total_request()}')

    print(mods_id)

    create_mods_pack()
    #write_file(files, data_path, "infmods.txt")
