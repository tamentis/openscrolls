import os.path

cdpath = None

def get_home_dir():
    """
    Return user home directory
    """
    try:
        path = os.path.expanduser("~")
    except:
        path = ""
    for env_var in ("HOME", "USERPROFILE", "TMP"):
        if os.path.isdir(path):
            break
        path = os.environ.get(env_var, "")
    if path:
        return path
    else:
        return "."

def set_cdpath(newcdpath):
    global cdpath
    cdpath = newcdpath
    save_cdpath(cdpath)

def save_cdpath(cdpath):
    if cdpath is None:
        return

    home = get_home_dir()
    fp = open(os.path.join(home, ".openscrolls.conf"), "w")
    fp.write(cdpath)
    fp.close()

def get_cdpath():
    home = get_home_dir()
    try:
        fp = open(os.path.join(home, ".openscrolls.conf"), "r")
        path = str(fp.read()).strip()
        fp.close()
    except:
        path = None
    return path

def get_abspath(filename, path=None):
    if path is None:
        path = cdpath
    if path is None:
        return None

    daggerpath = None
    for sub in os.listdir(path):
        if sub.lower() == "dagger":
            daggerpath = os.path.join(path, sub)
            break
    if daggerpath is None:
        return None

    a2path = None
    for sub in os.listdir(daggerpath):
        if sub.lower() == "arena2":
            a2path = os.path.join(daggerpath, sub)
            break
    if a2path is None:
        return None

    for sub in os.listdir(a2path):
        if sub.lower() == filename.lower():
            return os.path.join(a2path, sub)

    return None
    
cdpath = get_cdpath()
