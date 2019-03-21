# 2018 Peter Petrik (zilolv at gmail dot com)
# GNU General Public License 2 any later version

import subprocess
import platform
import os
import time

THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def timestamp():
    ts = time.gmtime()
    return time.strftime("%Y-%m-%d %H:%M:%S", ts)


def brew_prefix():
    output = subprocess.check_output(["brew", "--prefix"], encoding='UTF-8')
    homebrew_dir = output.strip()
    if not os.path.isdir(homebrew_dir):
        raise Exception("Missing homebrew folder " + homebrew_dir)
    return homebrew_dir

def xcode():
    output = subprocess.check_output(["system_profiler", "SPDeveloperToolsDataType"], encoding='UTF-8')
    for l in output.split('\n'):
        l = l.strip()
        if l.startswith("Version:"):
            l = l.replace("Version:", "")
            l = l.strip()
            return l
    return "Unknown"

def homebrew_libs():
    # only gdaL2 from osgeo homebrew should be present
    force_error =["gdal"]

    exclude = ["python@2", "bash-completion"]
    libs = []

    homebrew_dir = brew_prefix()

    # List all folders immediately under this folder:
    cellar_dir = os.path.join(homebrew_dir, "Cellar")
    bottles = next(os.walk(cellar_dir))[1]
    for bottle in bottles:
        bottle_dir = os.path.join(cellar_dir, bottle)
        versions = next(os.walk(bottle_dir))[1]
        if len(versions) != 1:
            raise Exception("Multiple versions installed for " + bottle_dir)

        for e in force_error:
            if bottle.endswith(e):
                raise Exception(bottle + " present but it must not be installed on system")

        excluded = False
        for e in exclude:
            if bottle.endswith(e):
                excluded = True
                break
        if excluded:
            continue

        libs += ["- " + bottle + " " + str(versions[0])]

    return "\n".join(sorted(libs))


def check_py_version(name):
    cmd = "import {}; print({}.__version__)".format(name, name)
    try:
        output = subprocess.check_output(["python3", "-c", cmd], stderr=subprocess.PIPE, encoding='UTF-8')
        return output.strip()
    except:
        print("Unable to detect version for " + name)
        return ""


def projdatumgrid():
    cmd = os.path.join(THIS_DIR, os.path.pardir, "scripts", "fetch_proj-datumgrid.bash" )
    try:
        output = subprocess.check_output([cmd, "-version"], stderr=subprocess.PIPE, encoding='UTF-8')
        return output.strip()
    except:
        print("Unable to detect version for proj-datumgrid")
        return ""


def python_libs():
    exclude = ["dropbox", "__pycache__"]
    libs = {}
    homebrew_dir = brew_prefix()

    # List all folders immediately under this folder:
    sitepackages = os.path.join(homebrew_dir, "lib/python3.7/site-packages/")
    pkgs = next(os.walk(sitepackages))[1]
    done_pkgs = []

    while pkgs:
        pkg = pkgs.pop()
        pkg_dir =  os.path.realpath(os.path.join(sitepackages, pkg))
        if pkg_dir in done_pkgs:
            continue
        done_pkgs += [pkg_dir]

        excluded = False
        for e in exclude:
            if e in pkg_dir:
                excluded = True
                break
        if excluded:
            continue

        # e.g. decorator-4.3.0.dist-info
        if "dist-info" in pkg:
            parts = pkg.replace(".dist-info", "").split("-")
            libs[parts[0]] = parts[1]
        elif "-py3.7.egg-info" in pkg:
            # e.g numpy-1.15.4-py3.7.egg-info/
            parts = pkg.replace("-py3.7.egg-info", "").split("-")
            libs[parts[0]] = parts[1]
        # this can contain also site-packages with absolute path
        elif pkg.endswith(".pth"):
            with open(pkg, 'r') as myfile:
                dirname = myfile.read().strip()
            if os.path.isdir(dirname):
                pkgs += [os.path.realpath(dirname)]

        else:
            if os.path.isdir(pkg_dir):
                if pkg not in libs:
                    libs[pkg] = check_py_version(pkg)

    ret = []
    for lk in libs.keys():
        ret += ["- " + lk + " " + libs[lk]]

    return "\n".join(sorted(ret))


def get_computer_info():
    mac_ver = platform.mac_ver()[0]

    msg = ""
    msg += "MacOS version is " + mac_ver + "\n\n"
    msg += "Package was built with XCode " + xcode() + "\n\n"
    msg += "Used Homebrew's packages\n\n"
    msg += homebrew_libs() + "\n\n"
    msg += "Used Proj Datum Grids:\n\n"
    msg += projdatumgrid() + "\n\n"
    msg += "Used Python3 modules\n\n"
    msg += python_libs() + "\n\n"
    msg += "Updated: " + timestamp()

    return msg


# print to stdout
print(get_computer_info())