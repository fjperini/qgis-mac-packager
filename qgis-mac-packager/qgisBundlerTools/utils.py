# 2018 Peter Petrik (zilolv at gmail dot com)
# GNU General Public License 2 any later version

import os
import shutil
import subprocess

def files_differ(file1, file2):
    try:
        subprocess.check_output(["diff", file1, file2], stderr=subprocess.STDOUT, encoding='UTF-8')
    except subprocess.CalledProcessError as err:
        return True
    return False


def framework_name(framework):
    path = framework
    while path:
        path = os.path.abspath(path)
        if path.endswith(".framework"):
            break
        path = os.path.join(path, os.pardir)

    if not path:
        raise Exception("Wrong framework directory structure!" + framework)

    frameworkName = os.path.basename(path)
    frameworkName = frameworkName.replace(".framework", "")

    return frameworkName, path


def is_text(fn):
    msg = subprocess.Popen(["file", "--mime", fn],
                           stdout=subprocess.PIPE,
                           encoding='UTF-8',
                           errors='replace').communicate()[0]
    # returns something like
    # <path>/libdelimitedtextprovider.so: application/x-mach-binary; charset=binary
    msg = msg.replace(fn, "")
    return "text" in msg


def resolve_libpath(pa, lib_path):
    # loader path should be really resolved here, because
    # it is relative to this binary
    if "@loader_path" in lib_path:
        if os.path.exists(lib_path.replace("@loader_path/../../../MacOS/../Frameworks", pa.frameworksDir)):
            lib_path = lib_path.replace("@loader_path/../../../MacOS/../Frameworks", pa.frameworksDir)
        elif os.path.exists(lib_path.replace("@loader_path/../../MacOS/../Frameworks", pa.frameworksDir)):
            lib_path = lib_path.replace("@loader_path/../../MacOS/../Frameworks", pa.frameworksDir)
        elif os.path.exists(lib_path.replace("@loader_path/../../../MacOS/..", pa.contentsDir)):
            lib_path = lib_path.replace("@loader_path/../../../MacOS/..", pa.contentsDir)
        elif os.path.exists(lib_path.replace("@loader_path/../../..", pa.frameworksDir)):
            lib_path = lib_path.replace("@loader_path/../../..", pa.frameworksDir)
        elif os.path.exists(lib_path.replace("@loader_path/../..", pa.contentsDir)):
            lib_path = lib_path.replace("@loader_path/../..", pa.contentsDir)
        elif os.path.exists("/usr/local/lib" + lib_path.replace("@loader_path/.dylibs", "")):
            lib_path = "/usr/local/lib" + lib_path.replace("@loader_path/.dylibs", "")
        elif os.path.exists("/usr/local/lib" + lib_path.replace("@loader_path/../.dylibs", "")):
            lib_path = "/usr/local/lib" + lib_path.replace("@loader_path/../.dylibs", "")
        elif os.path.exists("/usr/local" + lib_path.replace("@loader_path", "")):
            lib_path = "/usr/local" + lib_path.replace("@loader_path", "")
        elif os.path.exists("/usr/local/lib" + lib_path.replace("@loader_path", "")):
            lib_path = "/usr/local/lib" + lib_path.replace("@loader_path", "")
        elif os.path.exists("/usr/local/opt/opencv@2/lib" + lib_path.replace("@loader_path", "")):
            # opencv@2 is not in /usr/local/lib
            lib_path = "/usr/local/opt/opencv@2/lib" + lib_path.replace("@loader_path", "")
        else:
            # workarounds. Some python packages have bundled their libraries
            # but the libraries are in different version than the libraries
            # from brew packages
            for item in os.listdir(pa.pysitepackages):
                s = os.path.join(pa.pysitepackages, item)
                if os.path.isdir(s):
                    if os.path.exists(s + "/" + lib_path.replace("@loader_path", "")):
                        lib_path = s + "/" + lib_path.replace("@loader_path", "")
                        break
                    if os.path.exists(s + "/.dylibs/" + lib_path.replace("@loader_path", "")):
                        lib_path = s + "/.dylibs/" + lib_path.replace("@loader_path", "")
                        break
                    if os.path.exists(s + "/" + lib_path.replace("@loader_path/..", "")):
                        lib_path = s + "/" + lib_path.replace("@loader_path/..", "")
                        break
                    if os.path.exists(s + "/.dylibs/" + lib_path.replace("@loader_path/..", "")):
                        lib_path = s + "/.dylibs/" + lib_path.replace("@loader_path/..", "")
                        break
    return lib_path


# to make sure we
# NEVER NEVER NEVER
# deletes something outside
# the build directory
class CopyUtils:
    def __init__(self, outdir, verbose=True):
        self.outdir = outdir
        self.verbose = verbose

    def _is_in_out_dir(self, name):
        if self.outdir not in name:
            realpath = os.path.realpath(name)
            if self.outdir not in realpath:
                raise Exception("Trying to do file operation outside bundle directory! " + name)

    def recreate_dir(self, name):
        if os.path.exists(name):
            self.rmtree(name)
            if os.path.exists(name + "/.DS_Store"):
                self.remove(name + "/.DS_Store")
        else:
            os.makedirs(name)

    def rename(self, src, dest):
        self._is_in_out_dir(src)
        self._is_in_out_dir(dest)
        os.rename(src, dest)

    def remove(self, name):
        self._is_in_out_dir(name)
        os.remove(name)

    def rmtree(self, name):
        self._is_in_out_dir(name)
        shutil.rmtree(name)

    def symlink(self, src, dest):
        self._is_in_out_dir(dest)
        if os.path.isabs(src):
            self._is_in_out_dir(src)
        else:
            self._is_in_out_dir(os.path.dirname(dest) + "/" + src)
        try:
            os.symlink(src, dest)
        except:
            print( dest + " -> " + src)
            raise

    def unlink(self, name):
        self._is_in_out_dir(name)
        os.unlink(name)

    def copy(self, src, dest):
        self._is_in_out_dir(dest)
        shutil.copy2(src, dest)

    def copytree(self, src, dest, symlinks):
        self._is_in_out_dir(dest)
        shutil.copytree(src, dest, symlinks=symlinks)

    def rm(self, src):
        if os.path.exists(src):
            self._is_in_out_dir(src)
            if os.path.islink(src):
                self.unlink(src)
            elif os.path.isfile(src):
                self.remove(src)
            else:
                self.rmtree(src)

