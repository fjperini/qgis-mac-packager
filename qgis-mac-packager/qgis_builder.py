# 2018 Peter Petrik (zilolv at gmail dot com)
# GNU General Public License 2 any later version

import argparse
import glob
import os
import shutil
import qgisBundlerTools.utils as utils
import git
import subprocess
import multiprocessing
import sys


class QGISBuildError(Exception):
    pass


class Progress(git.remote.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print('update(%s, %s, %s, %s)'%(op_code, cur_count, max_count, message))



parser = argparse.ArgumentParser(description='Build QGIS Application with cmake')

parser.add_argument('--output_directory',
                    required=True,
                    help='output directory for resulting QGIS.app files')
parser.add_argument('-clean', action='store_true', help="start from clean build directory")
parser.add_argument('--git',
                    required=True,
                    help='git branch/tag/changeset')
parser.add_argument('--min_os',
                    required=False,
                    default=None,
                    help='min os version to support')

verbose = False
enable_tests = False

QGIS_REPO = "https://github.com/qgis/QGIS.git/"

args = parser.parse_args()

print("OUTPUT DIRECTORY: " + args.output_directory)
print("GIT: " + args.git)
print("CLEAN: " + str(args.clean))
print("APPLE MINOS: "  + str(args.min_os))

outDir = os.path.realpath(args.output_directory)
if not os.path.exists(outDir):
    raise QGISBuildError(args.output_directory + " does not exists")

buildDir = os.path.join(outDir, "build")
qgisDir = os.path.join(outDir, "qgis")
installDir = os.path.join(outDir, "install")

cp = utils.CopyUtils(outDir)
print(100*"*")
print("STEP 1: Get QGIS repo " + args.git)
print(100*"*")
if not os.path.exists(qgisDir):
    os.makedirs(qgisDir)
os.chdir(qgisDir)
if os.listdir(qgisDir):
   # dir is not empty
    try:
        repo = git.Repo(qgisDir)
    except git.InvalidGitRepositoryError:
        raise QGISBuildError( qgisDir + 'isn`t git repo')
else:
    # clone
    print("Cloning...")
    git.Repo.clone_from(QGIS_REPO, qgisDir, progress=Progress())

repo = git.Repo(qgisDir)
g = git.Git(qgisDir)
g.checkout(args.git)
try:
    # pull does not work when we have tag, only on branch (e.g. master)
    o = repo.remotes.origin
    o.pull()
except git.exc.GitCommandError:
    print("Failed to pull, probably you are on tag and not branch...")


print(100*"*")
print("STEP 2: Clean the build/install directory ")
print(100*"*")
if args.clean:
    print ("Cleaning: " + buildDir)
    cp.recreate_dir(buildDir)
else:
    print("Skipped, clean build not requested")
    if not os.path.exists(buildDir):
        os.makedirs(buildDir)

# always clean the install directory
print("Cleaning: " + installDir)
cp.recreate_dir(installDir)

print(100*"*")
print("STEP 3: Generate CMAKE build system")
print(100*"*")
os.chdir(buildDir)

prefix_path = "/usr/local/opt/qt;/usr/local/opt/qt5-webkit;/usr/local/opt/osgeo-qscintilla2;/usr/local/opt/qwt;/usr/local/opt/qwtpolar;"
prefix_path += "/usr/local/opt/qca;/usr/local/opt/gdal2;/usr/local/opt/gsl;/usr/local/opt/geos;/usr/local/opt/proj;"
prefix_path += "/usr/local/opt/libspatialite;/usr/local/opt/spatialindex;/usr/local/opt/fcgi;/usr/local/opt/expat;"
prefix_path += "/usr/local/opt/sqlite;/usr/local/opt/flex;/usr/local/opt/bison;/usr/local/opt/libzip;"
prefix_path += "/usr/local/opt/libtasn1;/usr/local/opt/grass7"

for path in prefix_path.split(";"):
    if not os.path.exists(path):
        raise QGISBuildError("Missing " + path)

grass7_prefix = "/usr/local/opt/grass7/grass-base"
if not os.path.exists(grass7_prefix):
    raise QGISBuildError("Missing " + grass7_prefix)

env = {
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/X11/bin",
    "GRASS_PREFIX7": grass7_prefix,
}

# copied from homebrew receipt... is it needed at all?
# keep superenv from stripping (use Cellar prefix)
env["CXXFLAGS"] = "-isystem {}/include".format(grass7_prefix)


cmake_args = ["cmake",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX="+os.path.realpath(installDir),
        "-DCMAKE_PREFIX_PATH="+prefix_path,
        "-DQGIS_MACAPP_BUNDLE=0",
        "-DWITH_3D=TRUE",
        "-DWITH_BINDINGS=TRUE",
        "-DCMAKE_FIND_FRAMEWORK=LAST" # FindGEOS.cmake is confused because it finds geos library but not framework Info.plist
       ]

if not enable_tests:
    # disable unit tests
    cmake_args += ["-DENABLE_TESTS=FALSE"]

if not (args.min_os is None):
    cmake_args += ["-DCMAKE_OSX_DEPLOYMENT_TARGET={}".format(args.min_os)]

cmake_args += [qgisDir]

print("run cmake command:")
print(args)
print("env:")
print(env)

try:
    result = subprocess.run(cmake_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine out/err into stdout; stderr will be None
                universal_newlines=True,
                check=True,
                env=env,
                encoding='UTF-8'
            )
    output = result.stdout
    print(output)

    if "Could not determine GEOS version from framework." in output:
        raise QGISBuildError("Unable to determine GEOS version!!")

    if "Could not find GRASS 7" in output:
        raise QGISBuildError("Unable to determine GRASS7 installation!!")


except subprocess.CalledProcessError as err:
    print(err.output)
    raise

print(100*"*")
cores = multiprocessing.cpu_count() - 1
print("STEP 4: make on " + str(cores) + " cores")
print(100*"*")
os.chdir(buildDir)

make_args = ["make", "-j"+str(cores), "install"]
try:
    result = subprocess.run(make_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine out/err into stdout; stderr will be None
                universal_newlines=True,
                check=True,
                env=env,
                encoding='UTF-8',
                errors='replace'
            )
    output = result.stdout
    print(output)

    if "make: *** [all] Error" in output:
        raise QGISBuildError("Found build error")

except subprocess.CalledProcessError as err:
    print(err.output)
    raise

print("build done")