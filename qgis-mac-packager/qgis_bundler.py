# 2018 Peter Petrik (zilolv at gmail dot com)
# GNU General Public License 2 any later version

import argparse
import glob
import os

import qgisBundlerTools.otool as otool
import qgisBundlerTools.install_name_tool as install_name_tool
import qgisBundlerTools.utils as utils
from steps import *
from get_computer_info import *

parser = argparse.ArgumentParser(description='Create QGIS Application bundle')

parser.add_argument('--qgis_install_tree',
                    required=True,
                    help='make install destination (QGIS.app)')
parser.add_argument('--output_directory',
                    required=True,
                    help='output directory for resulting QGIS.app files')
parser.add_argument('--python',
                    required=True,
                    help='directory with python framework to bundle, something like /usr/local/Cellar/python/3.7.0/Frameworks/Python.framework/Versions/3.7/Python')
parser.add_argument('--pyqt',
                    required=True,
                    help='directory with pyqt packages to bundle, something like /usr/local/Cellar/pyqt/5.10.1_1/lib/python3.7/site-packages/PyQt5')
parser.add_argument('--gdal',
                    required=True,
                    help='gdal installation directory')
parser.add_argument('--saga',
                    required=True,
                    help='saga installation directory')
parser.add_argument('--grass7',
                    required=True,
                    help='grass7 installation directory')
parser.add_argument('--rpath_hint',
                    required=False,
                    default="")
parser.add_argument('--start_step',
                    required=False,
                    default=0)
parser.add_argument('--min_os',
                    required=False,
                    default=None,
                    help='min os version to support')
parser.add_argument('--qgisapp_name',
                    required=True,
                    help='name of resulting qgis application (QGIS.app, QGIS3.4.app, QGIS3.5.app)')

verbose = False

args = parser.parse_args()

print("QGIS INSTALL TREE: " + args.qgis_install_tree)
print("OUTPUT DIRECTORY: " + args.output_directory)
print("PYTHON: " + args.python)
print("PYQT: " + args.pyqt)
print("GDAL: " + args.gdal)
print("SAGA: " + args.saga)
print("GRASS7: " + args.grass7)
print("APPLE MINOS: "  + str(args.min_os))
print("QGIS.app name: " + str(args.qgisapp_name))

if not os.path.exists(args.python):
    raise QGISBundlerError(args.python + " does not exists")

pyqtHostDir = args.pyqt
if not os.path.exists(os.path.join(pyqtHostDir, "QtCore.so")):
    raise QGISBundlerError(args.pyqt + " does not contain QtCore.so")

pythonHost = args.python
if not os.path.exists(pythonHost):
    raise QGISBundlerError(args.pyqt + " does not contain Python")

if not os.path.exists(os.path.join(args.qgis_install_tree, "QGIS.app")):
    raise QGISBundlerError(args.qgis_install_tree + " does not contain QGIS.app")

if not os.path.exists(args.gdal + "/bin"):
    raise QGISBundlerError(args.gdal + "/bin does not contain GDAL installation")

if not os.path.exists(args.saga + "/bin"):
    raise QGISBundlerError(args.saga + "/bin does not contain SAGA installation")

if not os.path.exists(args.grass7 + "/bin"):
    raise QGISBundlerError(args.grass7 + "/bin does not contain GRASS7 installation")

if "/" in args.qgisapp_name:
    raise QGISBundlerError(args.qgisapp_name + " must not contain path separator")


class Paths:
    def __init__(self, args):
        # bundler path
        self.bundlerDir = os.path.dirname(os.path.realpath(__file__))
        self.bundlerResourcesDir = os.path.join(self.bundlerDir, "resources")

        # original destinations
        self.pyqtHostDir = os.path.realpath(args.pyqt)
        self.pythonHost = os.path.realpath(args.python)
        self.pysitepackages = os.path.join(os.path.dirname(self.pythonHost), "lib", "python3.7", "site-packages")
        self.gdalHost = os.path.realpath(args.gdal)
        self.gdalPythonHost = os.path.realpath(args.gdal + "-python")
        self.sagaHost = os.path.realpath(args.saga)
        self.grass7Host = os.path.realpath(args.grass7)
        self.mysqlDriverHost = "/usr/local/opt/qmysql/lib/qt/plugins/sqldrivers/libqsqlmysql.dylib"
        self.psqlDriverHost = "/usr/local/opt/qpsql/lib/qt/plugins/sqldrivers/libqsqlpsql.dylib"
        self.odbcDriverHost = "/usr/local/opt/qodbc/lib/qt/plugins/sqldrivers/libqsqlodbc.dylib"

        # new bundle destinations
        self.qgisApp = os.path.realpath(os.path.join(args.output_directory, args.qgisapp_name))
        self.contentsDir = os.path.join(self.qgisApp, "Contents")
        self.macosDir = os.path.join(self.contentsDir, "MacOS")
        self.frameworksDir = os.path.join(self.contentsDir, "Frameworks")
        self.libDir = os.path.join(self.macosDir, "lib")
        self.qgisExe = os.path.join(self.macosDir, "QGIS")
        self.pluginsDir = os.path.join(self.contentsDir, "PlugIns")
        self.qgisPluginsDir = os.path.join(self.pluginsDir, "qgis")
        self.resourcesDir = os.path.join(self.contentsDir, "Resources")
        self.pythonDir = os.path.join(self.resourcesDir, "python")
        self.binDir = os.path.join(self.macosDir, "bin")
        self.grass7Dir = os.path.join(self.resourcesDir, "grass7")
        self.gdalDataDir = os.path.join(self.resourcesDir, "gdal")
        self.sqlDriversDir = os.path.join(self.pluginsDir, "sqldrivers")

        # install location
        self.installQgisAppName = args.qgisapp_name
        self.installQgisApp = "/Applications/" + self.installQgisAppName


cp = utils.CopyUtils(os.path.realpath(args.output_directory))
pa = Paths(args)

print(100*"*")
print("STEP 0: Copy QGIS and independent folders to build folder")
print(100*"*")

print ("Cleaning: " + args.output_directory)
if os.path.exists(args.output_directory):
    cp.rmtree(args.output_directory)
    if os.path.exists(args.output_directory + "/.DS_Store"):
        cp.remove(args.output_directory + "/.DS_Store")

print("Copying " + args.qgis_install_tree)
cp.copytree(args.qgis_install_tree, args.output_directory, symlinks=True)
if args.qgisapp_name != "QGIS.app":
    cp.rename(os.path.join(args.output_directory, "QGIS.app"), pa.qgisApp)

if not os.path.exists(pa.qgisApp):
    raise QGISBundlerError(pa.qgisExe + " does not exists")

if not os.path.exists(pa.binDir):
    os.makedirs(pa.binDir)

print("Remove crssync")
if os.path.exists(pa.libDir + "/qgis/crssync"):
    cp.rmtree(pa.libDir + "/qgis")

# https://doc.qt.io/qt-5/sql-driver.html#supported-databases
print("Copying QT SQL Drivers")
if not os.path.exists(pa.sqlDriversDir):
    os.makedirs(pa.sqlDriversDir)
for item in [pa.mysqlDriverHost, pa.psqlDriverHost, pa.odbcDriverHost]:
    if not os.path.exists(item):
        raise QGISBundlerError("Unable to find QT driver " + item)
    cp.copy(item, pa.sqlDriversDir)

print("Copying GDAL" + pa.gdalHost)
for item in os.listdir(pa.gdalHost + "/bin"):
    cp.copy(pa.gdalHost + "/bin/" + item, pa.binDir)
cp.copytree(pa.gdalHost + "/share/gdal", pa.gdalDataDir, symlinks=False)
subprocess.call(['chmod', '-R', '+w', pa.gdalDataDir])

# normally this should be on MacOS/bin/ so logic in GdalUtils.py works,
# but .py file in MacOS/bin halts the signing of the bundle
print("Copying GDAL-PYTHON" + pa.gdalPythonHost)
if not os.path.exists(pa.gdalDataDir + "/bin"):
    os.makedirs(pa.gdalDataDir + "/bin")
if not os.path.exists(pa.binDir):
    cp.makedirs(pa.binDir)
for item in os.listdir(pa.gdalPythonHost + "/bin"):
  if not os.path.isdir(pa.gdalPythonHost + "/bin/" + item):
    cp.copy(pa.gdalPythonHost + "/bin/" + item, pa.gdalDataDir + "/bin/" + item)
    cp.symlink(os.path.relpath(pa.gdalDataDir + "/bin/" + item, pa.binDir), pa.binDir + "/" + item)

print("Copying SAGA " + pa.sagaHost)
cp.copy(pa.sagaHost + "/bin/saga_cmd", pa.binDir)
subprocess.call(['chmod', '-R', '+w', pa.binDir])

print("Copying GRASS7 " + pa.grass7Host)
cp.copytree(pa.grass7Host, pa.grass7Dir, symlinks=True)
# TODO this is really just bash script that points to wrong location
# we should copy also one from libexe/grass and fix this one!
# TODO do not hardcode grass version here!
cp.copy(pa.grass7Host + "/../bin/grass76", pa.grass7Dir + "/bin")
subprocess.call(['chmod', '-R', '+w', pa.grass7Dir])
subprocess.call(['chmod', '-R', '+x', pa.grass7Dir + "/bin"])

print("Remove unneeded qgis_bench.app")
if os.path.exists(pa.binDir + "/qgis_bench.app"):
    cp.rmtree(pa.binDir + "/qgis_bench.app")

print("Append Python site-packages")
append_recursively_site_packages(cp, pa.pysitepackages, pa.pythonDir)

# TODO copy of python site-packages should be rather
# selective an not copy-all and then remove
print("remove not needed python site-packages")
redundantPyPackages = [
    "dropbox*",
    "GitPython*",
    "homebrew-*",
]
for pp in redundantPyPackages:
    for path in glob.glob(pa.pythonDir + "/" + pp):
        print("Removing " + path)
        if os.path.isdir(path):
            cp.rmtree(path)
        else:
            cp.remove(path)


subprocess.call(['chmod', '-R', '+w', pa.pluginsDir])

print("add pyqgis_startup.py to remove MacOS default paths")
startup_script = os.path.join(pa.bundlerResourcesDir, "pyqgis-startup.py")
if not os.path.exists(startup_script):
    raise QGISBundlerError("Missing resource " + startup_script)
cp.copy(startup_script, os.path.join(pa.pythonDir, "pyqgis-startup.py"))

print("Copying PyQt " + pyqtHostDir)
if not os.path.exists(pa.pythonDir + "/PyQt5/Qt.so"):
    raise QGISBundlerError("Inconsistent python with pyqt5, should be copied in previous step")
pyqtpluginfile = os.path.join(pyqtHostDir, os.pardir, os.pardir, os.pardir, os.pardir, "share", "pyqt", "plugins")
cp.copytree(pyqtpluginfile, pa.pluginsDir + "/PyQt5", True)
subprocess.call(['chmod', '-R', '+w', pa.pluginsDir + "/PyQt5"])

# https://github.com/lutraconsulting/qgis-mac-packager/issues/44
# when number 7 changes, change also in steps.py
print("Copying mod_spatiallite")
cp.copy("/usr/local/opt/libspatialite/lib/mod_spatialite.7.dylib", os.path.join(pa.libDir, "mod_spatialite.7.dylib"))


print(100*"*")
print("STEP 1: Analyze the libraries we need to bundle")
print(100*"*")

# Find QT
qtDir = None
for framework in otool.get_binary_dependencies(pa, pa.qgisExe).frameworks:
    if "lib/QtCore.framework" in framework:
        path = os.path.realpath(framework)
        qtDir = path.split("/lib/")[0]
        break
if not qtDir:
    raise QGISBundlerError("Unable to find QT install directory")
print("Found QT: " + qtDir)

# Find QCA dir
qcaDir = None
for framework in otool.get_binary_dependencies(pa, pa.qgisExe).frameworks:
    if "lib/qca" in framework:
        path = os.path.realpath(framework)
        qcaDir = path.split("/lib/")[0]
        break
if not qcaDir:
    raise QGISBundlerError("Unable to find QCA install directory")
print("Found QCA: " + qcaDir)

# Analyze all
sys_libs = set()
libs = set()
frameworks = set()

deps_queue = set()
done_queue = set()

# initial items:
# 1. qgis executable
deps_queue.add(pa.qgisExe)
# 2. all so and dylibs in bundle folder
for root, dirs, files in os.walk(pa.qgisApp):
    for file in files:
        filepath = os.path.join(root, file)
        filename, file_extension = os.path.splitext(filepath)
        if file_extension in [".dylib", ".so"]:
            deps_queue.add(filepath)
# 3. python libraries
deps_queue |= set(glob.glob(os.path.dirname(args.python) + "/lib/python3.7/lib-dynload/*.so"))
# 4. dynamic qt providers
deps_queue |= set(glob.glob(qtDir + "/plugins/*/*.dylib"))
deps_queue |= set(glob.glob(qcaDir + "/lib/qt5/plugins/*/*.dylib"))
# 5. python interpreter
deps_queue.add(pythonHost)
# 6. saga for processing toolbox and other bins
deps_queue |= set(glob.glob(pa.binDir + "/*"))
# 7. grass7
deps_queue |= set(glob.glob(pa.grass7Dir + "/bin/*"))
deps_queue |= set(glob.glob(pa.grass7Dir + "/lib/*.dylib"))
deps_queue |= set(glob.glob(pa.grass7Dir + "/driver/db/*"))
deps_queue |= set(glob.glob(pa.grass7Dir + "/etc/*"))
deps_queue |= set(glob.glob(pa.grass7Dir + "/etc/*/*"))

# DEBUGGING
debug_lib = None
# debug_lib = "libjpeg"

while deps_queue:
    lib = deps_queue.pop()

    if lib.endswith(".py"):
        continue

    lib_fixed = lib
    # patch @rpath, @loader_path and @executable_path
    if "@rpath" in lib_fixed:
        # replace rpath we know from homebrew
        patched_path = lib_fixed.replace("@rpath", "/usr/local/Cellar/lapack/3.8.0_1/lib")
        if os.path.exists(patched_path):
            lib_fixed = patched_path
        # now try the hint?
        lib_fixed = lib_fixed.replace("@rpath", args.rpath_hint)

    lib_fixed = lib_fixed.replace("@executable_path", pa.macosDir)
    lib_fixed = utils.resolve_libpath(pa, lib_fixed)

    if "@loader_path" in lib_fixed:
        raise QGISBundlerError("Ups, broken otool.py? this should be resolved there " + lib_fixed)

    if lib_fixed in done_queue:
        continue

    if not lib_fixed:
        continue

    if os.path.isdir(lib_fixed):
        continue

    extraInfo = "" if lib == lib_fixed else "(" + lib_fixed + ")"
    print("Analyzing " + lib + extraInfo)

    if not os.path.exists(lib_fixed):
        raise QGISBundlerError("Library missing! " + lib_fixed)

    done_queue.add(lib_fixed)

    binaryDependencies = otool.get_binary_dependencies(pa, lib_fixed)

    if debug_lib:
        for l in binaryDependencies.libs:
            if debug_lib in l:
               print(100*"*")
               print("JPEG: {} -- {}".format(debug_lib, lib))

    sys_libs |= set(binaryDependencies.sys_libs)
    libs |= set(binaryDependencies.libs)
    frameworks |= set(binaryDependencies.frameworks)

    deps_queue |= set(binaryDependencies.libs)
    deps_queue |= set(binaryDependencies.frameworks)


msg = "\nLibs:\n\t"
msg += "\n\t".join(sorted(libs))
msg += "\nFrameworks:\n\t"
msg += "\n\t".join(sorted(frameworks))
msg += "\nSysLibs:\n\t"
msg += "\n\t".join(sorted(sys_libs))
print(msg)

print(100*"*")
print("STEP 2: Copy libraries/plugins to bundle")
print(100*"*")

unlinked_libs = set()
unlink_links = set()

for lib in libs:
    # We assume that all libraries with @ are already bundled in QGIS.app
    # TODO in conda they use rpath, so this is not true
    if not lib or "@" in lib:
        continue

    # libraries to lib dir
    # plugins to plugin dir/plugin name/, e.g. PlugIns/qgis, PlugIns/platform, ...
    if "/plugins/" in lib:
        pluginFolder = lib.split("/plugins/")[1]
        pluginFolder = pluginFolder.split("/")[0]
        # Skip this is already copied
        if "libpyqt5qmlplugin.dylib" in lib:
            if os.path.exists(pa.pluginsDir + "/PyQt5/libpyqt5qmlplugin.dylib"):
                target_dir = pa.pluginsDir + "/PyQt5"
            else:
                raise QGISBundlerError("Ups, missing libpyqt5qmlplugin.dylib")
        else:
            target_dir = pa.pluginsDir + "/" + pluginFolder
    else:
        target_dir = pa.libDir

    # only copy if not already in the bundle
    # frameworks are copied elsewhere
    if (pa.qgisApp not in lib) and (".framework" not in lib):
        print("Bundling " + lib + " to " + target_dir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        cp.copy(lib, target_dir)

        new_file = os.path.join(target_dir, os.path.basename(lib))
        subprocess.call(['chmod', '+w', new_file])

    # link to libs folder if the library is somewhere around the bundle dir
    if (pa.qgisApp in lib) and (pa.libDir not in lib):
        link = pa.libDir + "/" + os.path.basename(lib)
        if not os.path.exists(link):
            cp.symlink(os.path.relpath(lib, pa.libDir),
                       link)
            link = os.path.realpath(link)
            if not os.path.exists(link):
                raise QGISBundlerError("Ups, wrongly linked! " + lib)
        else:
            # we already have this lib in the bundle (because there is a link! in lib/), so make sure we do not have it twice!
            existing_link_realpath = os.path.realpath(link)
            if existing_link_realpath != os.path.realpath(lib):
                if utils.files_differ(existing_link_realpath, lib):
                    # libraries with the same name BUT with different contents
                    # so do not have it in libs folder because we do not know which
                    # we HOPE that this happens only for cpython extensions for python modules
                    if not "cpython-37m-darwin" in link:
                        raise QGISBundlerError("multiple libraries with same name but different content " + link + "; " + lib)
                    unlink_links.add(link)
                    unlinked_libs.add(existing_link_realpath)
                    unlinked_libs.add(os.path.realpath(lib))

                else:
                    # same library (binary) --> we need just one
                    # ok, in this case remove the new library and just symlink to the lib
                    cp.remove(lib)
                    relpath = os.path.relpath(existing_link_realpath, os.path.dirname(lib))
                    cp.symlink(relpath,
                               lib)

                    link = os.path.realpath(lib)
                    if not os.path.exists(link):
                        raise QGISBundlerError("Ups, wrongly relinked! " + link)


    # find out if there are no python3.7 plugins in the dir
    plugLibDir = os.path.join(os.path.dirname(lib), "python3.7", "site-packages", "PyQt5")
    if os.path.exists(plugLibDir):
        for file in glob.glob(plugLibDir + "/*.so"):
            basename =  os.path.basename(file)
            destFile = pa.pluginsDir + "/PyQt5/" + basename
            link = pa.pythonDir + "/PyQt5/" + basename
            if not os.path.exists(destFile):
                if os.path.exists(link):
                    print("Linking extra python plugin " + file)
                    relpath = os.path.relpath(link, os.path.dirname(destFile))
                    cp.symlink(relpath,
                               destFile)
                else:
                    raise QGISBundlerError("All PyQt5 modules should be already bundled!" + file)


# these are cpython libs, unlink them it is enough to have them in python site-packages
for lib in unlink_links:
    cp.unlink(lib)

# fix duplicit libraries
# this is really just a workaround,
# because when libraries are copied, we should copy all the link tree
# xy.dylib -> dx.1.0.dylib -> dx.1.0.0.dylib ..but now we copy it 3 times
# and not as links
workarounds = {}

for l in ["libwx_osx_cocoau_core",
          "libwx_osx_cocoau_html",
          "libwx_baseu_xml",
          "libwx_osx_cocoau_adv",
          "libwx_baseu"
          ]:
    lib = pa.libDir + "/{}-3.0.dylib".format(l)
    existing_link_realpath = pa.libDir + "/{}-3.0.0.4.0.dylib".format(l)
    workarounds[lib] = existing_link_realpath

lib = pa.libDir + "/libpq.5.dylib"
existing_link_realpath = pa.libDir + "/libpq.5.10.dylib"
workarounds[lib] = existing_link_realpath

for lib, existing_link_realpath in workarounds.items():
    if not (os.path.exists(lib) and os.path.exists(existing_link_realpath)):
        print("WARNING: Workaround " + lib + "->" + existing_link_realpath + " is no longer valid, maybe you upaded packages?")
        continue

    cp.remove(lib)
    relpath = os.path.relpath(existing_link_realpath, os.path.dirname(lib))
    cp.symlink(relpath, lib)


print(100*"*")
print("STEP 3: Copy frameworks to bundle")
print(100*"*")
for framework in frameworks:
    if not framework:
        continue

    frameworkName, baseFrameworkDir = utils.framework_name(framework)
    new_framework = os.path.join(pa.frameworksDir, frameworkName + ".framework")

    # only copy if not already in the bundle
    if os.path.exists(new_framework):
        print("Skipping " + new_framework + " already exists")
        continue

    # do not copy system libs
    if pa.qgisApp not in baseFrameworkDir:
        print("Bundling " + frameworkName + ": " + framework + "  to " + pa.frameworksDir)
        cp.copytree(baseFrameworkDir, new_framework, symlinks=True)
        subprocess.call(['chmod', '-R', '+w', new_framework])


libPatchedPath = "@executable_path/lib"
relLibPathToFramework = "@executable_path/../Frameworks"

# Now everything should be here
subprocess.call(['chmod', '-R', '+w', pa.qgisApp])

print(100*"*")
print("STEP 4: Fix frameworks linker paths")
print(100*"*")
frameworks = glob.glob(pa.frameworksDir + "/*.framework")
for framework in frameworks:
    print("Patching " + framework)
    frameworkName = os.path.basename(framework)
    frameworkName = frameworkName.replace(".framework", "")

    # patch versions framework
    last_version = None
    versions = sorted(glob.glob(os.path.join(framework, "Versions") + "/*"))
    for version in versions:
        verFramework = os.path.join(version, frameworkName)
        if os.path.exists(verFramework):
            if not os.path.islink(verFramework):
                binaryDependencies = otool.get_binary_dependencies(pa, verFramework)
                subprocess.call(['chmod', '+x', verFramework])
                install_name_tool.fix_lib(verFramework, binaryDependencies, pa.contentsDir, libPatchedPath, relLibPathToFramework)

            if version is not "Current":
                last_version = os.path.basename(version)
        else:
            print("Warning: Missing " + verFramework)

    # patch current version
    currentFramework = os.path.join(framework, frameworkName)
    if os.path.exists(currentFramework):
        if not os.path.islink(verFramework):
            binaryDependencies = otool.get_binary_dependencies(pa, currentFramework)
            install_name_tool.fix_lib(currentFramework, binaryDependencies, pa.contentsDir, libPatchedPath, relLibPathToFramework)
            subprocess.call(['chmod', '+x', currentFramework])
    else:
        if last_version is None:
            print("Warning: Missing " + currentFramework)
        else:
            print("Creating version link for " + currentFramework)
            subprocess.call(["ln", "-s", last_version, framework + "/Versions/Current"])
            subprocess.call(["ln", "-s", "Versions/Current/" + frameworkName, currentFramework])

    # TODO generic?
    # patch helpers (?)
    helper = os.path.join(framework, "Helpers", "QtWebEngineProcess.app" , "Contents", "MacOS", "QtWebEngineProcess")
    if os.path.exists(helper):
        binaryDependencies = otool.get_binary_dependencies(pa, helper)
        install_name_tool.fix_lib(helper, binaryDependencies, pa.contentsDir, libPatchedPath, relLibPathToFramework)
        subprocess.call(['chmod', '+x', helper])

    # TODO generic?
    helper = os.path.join(framework, "Versions/Current/Resources/Python.app/Contents/MacOS/Python")
    if os.path.exists(helper):
        binaryDependencies = otool.get_binary_dependencies(pa, helper)
        install_name_tool.fix_lib(helper, binaryDependencies, pa.contentsDir, libPatchedPath, relLibPathToFramework)
        subprocess.call(['chmod', '+x', helper])
        # add link to MacOS/bin too
        cp.symlink(os.path.relpath(helper, pa.binDir), pa.binDir + "/python")
        cp.symlink(os.path.relpath(helper, pa.binDir), pa.binDir + "/python3")

    helper = os.path.join(framework, "Versions/Current/lib/python3.7/lib-dynload")
    if os.path.exists(helper):
        for bin in glob.glob(helper + "/*.so"):
            binaryDependencies = otool.get_binary_dependencies(pa, bin)
            install_name_tool.fix_lib(bin, binaryDependencies, pa.contentsDir, libPatchedPath, relLibPathToFramework)
            subprocess.call(['chmod', '+x', bin])

            link = pa.libDir + "/" + os.path.basename(bin)
            cp.symlink(os.path.relpath(bin, pa.libDir),
                       link)
            link = os.path.realpath(link)
            if not os.path.exists(link):
                raise QGISBundlerError("Ups, wrongly relinked! " + bin)

    if "Python" in framework:
        filepath = os.path.join(framework, "Versions/Current/lib/python3.7/site-packages" )
        cp.unlink(filepath)
        cp.symlink("../../../../../../Resources/python", filepath)
        filepath = os.path.realpath(filepath)
        if  not os.path.exists(filepath):
            raise QGISBundlerError("Ups, wrongly relinked! " + "site-packages")


print(100*"*")
print("STEP 5: Fix libraries/plugins linker paths")
print(100*"*")
libs = []
for root, dirs, files in os.walk(pa.qgisApp):
    for file in files:
        filepath = os.path.join(root, file)
        if ".framework" not in filepath:
            filename, file_extension = os.path.splitext(filepath)
            if file_extension in [".dylib", ".so"]:
                libs += [filepath]

# note there are some libs here: /Python.framework/Versions/Current/lib/*.dylib but
# those are just links to Current/Python
for lib in libs:
    if not os.path.islink(lib):
        print("Patching " + lib)
        binaryDependencies = otool.get_binary_dependencies(pa, lib)
        install_name_tool.fix_lib(lib, binaryDependencies, pa.contentsDir, libPatchedPath, relLibPathToFramework)
        subprocess.call(['chmod', '+x', lib])

        # TODO what to do with unlinked_libs????
        # now we hope noone references them
    else:
        print("Skipping link " + lib)

print(100*"*")
print("STEP 6: Fix executables linker paths")
print(100*"*")
exes = set()
exes.add(pa.qgisExe)
exes |= set(glob.glob(pa.frameworksDir + "/Python.framework/Versions/Current/bin/*"))
exes |= set(glob.glob(pa.frameworksDir + "/Python.framework/Versions/Current/Resources/Python.app/Contents/MacOS/Python"))
exes |= set(glob.glob(pa.binDir + "/*"))
exes |= set(glob.glob(pa.grass7Dir + "/bin/*"))
exes |= set(glob.glob(pa.grass7Dir + "/driver/db/*"))
exes |= set(glob.glob(pa.grass7Dir + "/etc/*"))
exes |= set(glob.glob(pa.grass7Dir + "/etc/*/*"))

for exe in exes:
    if not os.path.isdir(exe):
        if not os.path.islink(exe):
            print("Patching " + exe)
            binaryDependencies = otool.get_binary_dependencies(pa.qgisApp, exe)
            try:
                install_name_tool.fix_lib(exe, binaryDependencies, pa.contentsDir, libPatchedPath, relLibPathToFramework)
            except subprocess.CalledProcessError:
                # Python.framework/Versions/Current/bin/idle3 is not a Mach-O file ??
                pass
            subprocess.call(['chmod', '+x', exe])

            exeDir = os.path.dirname(exe)
            # as we use @executable_path everywhere,
            # there is a problem
            # because QGIS and bin/* is different directory
            if not os.path.exists(exeDir + "/lib"):
                cp.symlink(os.path.relpath(pa.libDir, exeDir), exeDir + "/lib")
            testLink = os.path.realpath(exeDir + "/lib")
            if testLink != os.path.realpath(pa.libDir):
                raise QGISBundlerError("invalid lib link!")

            # we need to create symlinks to Frameworks, so for example python does not pick system Python 2.7 dylibs
            # https://github.com/lutraconsulting/qgis-mac-packager/issues/60
            if not os.path.exists(exeDir + "/../Frameworks"):
                cp.symlink(os.path.relpath(pa.frameworksDir, os.path.join(exeDir, os.pardir) ), exeDir + "/../Frameworks")
            testLink = os.path.realpath(exeDir + "/../Frameworks")
            if testLink != os.path.realpath(pa.frameworksDir):
                raise QGISBundlerError("invalid frameworks link!")

        else:
            print("Skipping link " + exe)
            subprocess.call(['chmod', '+x', exe])

print(100*"*")
print("STEP 7: Fix QCA_PLUGIN_PATH Qt Plugin path")
print(100*"*")
# It looks like that QCA compiled with QCA_PLUGIN_PATH CMake define
# adds this by default to QT_PLUGIN_PATH. Overwrite this
# in resulting binary library
qcaLib = os.path.join(pa.frameworksDir, "qca-qt5.framework", "qca-qt5")
f = open(qcaLib, 'rb+')
data = f.read()
data=data.replace(bytes(qcaDir + "/lib/qt5/plugins", "utf-8"), bytes(qcaDir + "/xxx/xxx/plugins", "utf-8"))
f.seek(0)
f.write(data)
f.close()

output = subprocess.check_output(["strings", qcaLib], encoding='UTF-8')
if qcaLib in output:
    raise QGISBundlerError("Failed to patch " + qcaLib)


print(100*"*")
print("STEP 8: Clean redundant files")
print(100*"*")
clean_redundant_files(pa, cp)

print(100 * "*")
print("STEP 8: Patch files")
print(100 * "*")
patch_files(pa, args.min_os)


print(100 * "*")
print("STEP 10: Test full tree QGIS.app")
print(100 * "*")
test_full_tree_consistency(pa)

# Wow we are done!
cpt = sum([len(files) for r, d, files in os.walk(pa.qgisApp)])
print ("Done with files bundled " + str(cpt))