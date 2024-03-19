import urllib.request
from utils import *

api = "https://api.modrinth.com/v2"

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

            if not is_already_save(modpack_name):
                to_write_modpacks.append(f'{modpack_name}{spliter}{modpack_id}{spliter}{modrinth_link}')
        
        dependencies_version = request(f'{api}/project/{modpack_id}/version', {"loaders" : [loader_version]})
        dependencies_version = accepted_filter_on(dependencies_version, "game_versions", to_filter)

        if len(dependencies_version) == 0:
            print(f"{modpack_name} not found in {loader_version} {to_filter}")
            continue
        

        latest_dependencies = [dependency["project_id"] for dependency in dependencies_version[0]["dependencies"]]
        all_dependencies = request(f'{api}/project/{modpack_id}/dependencies')["projects"]
        
        for dependency in all_dependencies:
            project_id = dependency["id"]

            if project_id not in latest_dependencies:
                continue
            latest_dependencies.remove(project_id)

            project_name = dependency["title"]
            project_type = dependency["project_type"]

            modrinth_link = f'https://modrinth.com/{project_type}/{dependency["slug"]}'
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
    game_version = loader_info[1]

    to_filter = [game_version]
    if accepted_filter:
        to_filter += modpack_info_data_supp 

    def setup_mod(mod_id):
        file = request(f'{api}/project/{mod_id}/version?loaders=["{loader_name}"]&game_versions={to_filter}'.replace("\'", "\""))

        if len(file) == 0:
            print(f'{get_name_save(mod_id)} not found in {loader_name} {game_version}')
            return
        
        for mc_version in to_filter:
            for filter_file in file:
                try :
                    if mc_version in filter_file['game_versions']:
                        file = filter_file
                        break
                except:
                    pass

        project_dependencies = file["dependencies"]
        if len(project_dependencies) != 0:
            all_dependencies = request(f'{api}/project/{mod_id}/dependencies')["projects"]

            to_write = []
            for dependency in project_dependencies:

                if dependency["dependency_type"] != "required":
                    continue
                
                project_id = dependency["project_id"]
                dependency = filter_on(all_dependencies, "id", [project_id])[0]

                project_name = dependency["title"]

                modrinth_link = f'https://modrinth.com/mod/{dependency["slug"]}'

                if not is_already_save(project_name):
                    to_write.append(f'{project_name}{spliter}{project_id}{spliter}{modrinth_link}')
                add_to_list(project_id, project_name, "mod")

            if len(to_write) > 0: 
                write_file(to_write, data_path, "mods_id.txt")
        
        datas = file["files"][0]

        data = {
            "path": "mods/"+datas["filename"],
            "hashes" : datas["hashes"],
            "downloads": [datas["url"]],
            "fileSize": datas["size"]
        }

        files.append(data)

    for mod_id in mods_id:
        setup_mod(mod_id)


def setup_texturepacks_id():
    game_version = loader_info[1]

    to_filter = [game_version]
    if accepted_filter:
        to_filter += modpack_info_data_supp 

    def setup_texture(texture_id):
        file = request(f'{api}/project/{texture_id}/version?game_versions={to_filter}'.replace("\'", "\""))

        if len(file) == 0:
            print(f'{get_name_save(texture_id)} not found in {game_version}')
            return
        
        for mc_version in to_filter:
            for filter_file in file:
                try :
                    if mc_version in filter_file['game_versions']:
                        file = filter_file
                        break
                except:
                    pass
        
        datas = file["files"][0]

        data = {
            "path": "resourcepacks/"+datas["filename"],
            "hashes" : datas["hashes"],
            "downloads": [datas["url"]],
            "fileSize": datas["size"]
        }

        files.append(data)

    for texture_id in resourcepacks_id:
        setup_texture(texture_id)


def create_mods_pack():
    delete_folder_if_exist(modpacks_path)
    os.mkdir(modpacks_path)

    build_info = modpack_info["build"]
    modpack_inf = modpack_info["modpack"]

    modpack_version = modpack_inf["version"]
    modpack_author = modpack_inf["author"]
    modpack_summary = modpack_inf["summary"] + " - by " + modpack_author
    modpack_name = modpack_inf["name"].replace("$VERSION", modpack_version)

    minecraft_version = modpack_info["minecraft"]["version"]
    
    if build_info["modrinth-modpack-zip"] == True:
        create_files_if_not_exist(modpacks_path, ["modrinth.index.json"])

        loader_version = ""
        if loader_info[0] == "fabric":
            loader_version = request("https://meta.fabricmc.net/v2/versions/loader/")[0]["version"]

        manifest = {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": modpack_version,
            "name": modpack_name,
            "summary": modpack_summary,

            "files": [file for file in files],

            "dependencies": {
                "minecraft": minecraft_version,
                "fabric-loader": loader_version
            }
        }
        
        write_file([json.dumps(manifest, indent=4)], modpacks_path, "modrinth.index.json")

        file_path = f'{modpacks_path}/modrinth'
        os.mkdir(file_path)

        shutil.make_archive(f"{file_path}/{modpack_name}", 'zip', modpacks_path)
    
    if build_info["classic-zip-folder"] == True and False:
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

    setup_target_modpack_mod()
    setup_target_mod()
    setup_target_resourcepacks()
    print(f'detected mods on modrinth : {len(mods_id)}')

    setup_mod_id()
    #print("files : \n", files)
    setup_texturepacks_id()
    print(f'\ntotal mods to download : {len(mods_id)}')
    print(f'total texturepacks to download : {len(resourcepacks_id)}')
    print(f'\ntotal requests : {get_total_request()}')

    print(mods_id)

    create_mods_pack()
    #write_file(files, data_path, "infmods.txt")
