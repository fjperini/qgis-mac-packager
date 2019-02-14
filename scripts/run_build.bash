#!/bin/bash

set -e

# 2018 Peter Petrik (zilolv at gmail dot com)
# GNU General Public License 2 any later version

PWD=`pwd`
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

if (( $# != 4 )); then
    echo "run_build build_dir git_tag release_name qgisapp_name"
fi

BUILD_DIR=$1
GIT=$2
RELEASE=$3
QGISAPP=$4
PACKAGE=qgis_${RELEASE}_${GIT}_${TIMESTAMP}.dmg
MINOS=10.11.0

echo "Building & Packaging QGIS to $BUILD_DIR"
mkdir -p $BUILD_DIR

echo "Building QGIS $GIT for $RELEASE"

echo "Please run brew update manually to get new deps"

cd $DIR/../qgis-mac-packager
echo "Run build"
if true; then
    python3 qgis_builder.py \
       --output_directory $BUILD_DIR \
       --git $GIT --min_os ${MINOS}
fi

echo "Bundle"
if true; then
    python3 qgis_bundler.py \
      --qgis_install_tree $BUILD_DIR/install  \
      --output_directory $BUILD_DIR/bundle  \
      --python /usr/local/opt/python3/Frameworks/Python.framework/Versions/3.7/Python \
      --pyqt /usr/local/opt/pyqt5/lib/python3.7/site-packages/PyQt5 \
      --gdal /usr/local/opt/gdal2 \
      --saga /usr/local/opt/saga-gis-lts \
      --grass7 /usr/local/opt/grass7/grass-base \
      --min_os ${MINOS} \
      --qgisapp_name ${QGISAPP}
fi

echo "Package"
if true; then
    python3 qgis_packager.py \
      --qgisApp $BUILD_DIR/bundle/${QGISAPP} \
      --outname=$BUILD_DIR/$PACKAGE \
      --sign $DIR/../../sign_identity.txt \
      --keychain $DIR/../../qgis.keychain-db
fi

echo "Upload"
if true; then
    python3 qgis_uploader.py \
      --dropbox=$DIR/../../dropbox_token.txt \
      --destination=/$RELEASE/$PACKAGE \
      --package=$BUILD_DIR/$PACKAGE
fi

echo "All done"
cd $PWD