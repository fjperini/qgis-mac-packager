#!/usr/bin/env bash

set -e

# WARNING!!!
# If we build something we MUST use --build-bottle flag!!!
# https://github.com/lutraconsulting/qgis-mac-packager/issues/25
#
# https://docs.brew.sh/Bottles
# By default, bottles will be built for the oldest CPU supported by the OS/architecture you’re building for
# (Core 2 for 64-bit OSs). This ensures that bottles are compatible with all computers you might distribute
# them to. If you really want your bottles to be optimized for something else, you can pass the --bottle-arch=
# option to build for another architecture; for example, brew install foo --build-bottle --bottle-arch=penryn.
# Just remember that if you build for a newer architecture some of your users might get binaries they can’t
# run and that would be sad!

brew tap osgeo/osgeo4mac

brew install fcgi
brew install git
brew install cmake
brew install ninja
brew install gsl
brew install sip
brew install bison
brew install flex
brew install pkg-config
brew install python

# qt
brew install qt
brew install qjson
brew install osgeo/osgeo4mac/qt5-webkit
brew install osgeo/osgeo4mac/qmysql
brew install osgeo/osgeo4mac/qodbc
brew install osgeo/osgeo4mac/qpsql
brew install pyqt

# pyproj has bug for python3, unable to install from pip3
pip3 install python-dateutil
pip3 install cython
CFLAGS='-std=c99' pip3 install git+https://github.com/jswhit/pyproj.git

# make sure you do not install homebrew-core/gdal since it
# does not support netcdf
# also do not use bottle since it does not have netcdf too!
brew install osgeo/osgeo4mac/gdal2 --build-bottle --with-complete --with-libkml --with-postgresql
brew link gdal2 --force

brew install openvpn
brew install szip
brew install hdf5
brew link --overwrite numpy
brew install scipy
brew install netcdf
brew install gsl
brew install exiv2

# https://github.com/OSGeo/homebrew-osgeo4mac/issues/529
# brew install saga-gis-lts --build-bottle
# should be fixed with https://github.com/OSGeo/homebrew-osgeo4mac/commit/6e1ee285d8619e4d10bbe3ab34b4934f158baf28
brew install osgeo/osgeo4mac/saga-gis-lts

brew install gdal2-python

# https://github.com/lutraconsulting/qgis-mac-packager/issues/45
brew install osgeo/osgeo4mac/mrsid-sdk
brew install osgeo/osgeo4mac/gdal2-mrsid

# https://github.com/lutraconsulting/qgis-mac-packager/issues/59
brew install osgeo/osgeo4mac/ecwjp2-sdk
brew install osgeo/osgeo4mac/gdal2-ecwjp2

# use this link until postgis is build on osgeo
# POSTGIS_FORMULA=https://raw.githubusercontent.com/OSGeo/homebrew-osgeo4mac/530a838c9d93721d0c2d5eee2ddeb702b848184f/Formula/postgis.rb
# brew install $POSTGIS_FORMULA --build-bottle --build-from-source
# should be fixed with https://github.com/OSGeo/homebrew-osgeo4mac/commit/afbffb335d7f4f39bc7d0ac224655871f18c91de
brew install osgeo/osgeo4mac/postgis2

# tools
pip3 install dropbox
pip3 install GitPython
pip3 install owslib
brew install wget

# https://github.com/al45tair/dmgbuild/issues/12
pip install dmgbuild

# qgis deps
# brew install osgeo/osgeo4mac/qgis3 --only-dependencies
# qgis install it brings homebrew-core/gdal dependency back

brew install pyqt5-webkit
# brew install x11
brew install qca
brew install qtkeychain
brew install qscintilla2
brew install qwt
brew install qwtpolar
brew install sqlite
brew install expat
brew install proj
brew install spatialindex
brew install postgresql
brew install libpq
brew install curl
brew install libzip
brew install libtasn1
brew install hicolor-icon-theme
brew install libiconv
brew install geos
brew install libspatialite
brew install openssl
brew install poppler
brew install gnu-sed

# matplotlib
brew install numpy
brew install brewsci/bio/matplotlib

# core providers
brew install gdal2-python

# brew install oracle-client-sdk
brew cask install XQuartz # requirement of grass7
brew install grass7

brew install gettext

#/usr/local/opt/grass7/grass-base/include/grass/glocale.h:9:10: fatal error: 'libintl.h' file not found
brew link gettext --force

brew install gpsbabel
brew install pyspatialite
brew install r

pip3 install certifi
pip3 install chardet
pip3 install idna
pip3 install OWSLib
pip3 install cython
pip3 install pyproj
pip3 install python-dateutil
pip3 install pytz
pip3 install requests
pip3 install six
pip3 install urllib3
pip3 install coverage
pip3 install funcsigs
pip3 install future
pip3 install mock
pip3 install nose2
pip3 install pbr
pip3 install psycopg2
pip3 install PyYAML
pip3 install Jinja2
pip3 install MarkupSafe
pip3 install Pygments
pip3 install termcolor
pip3 install oauthlib
pip3 install pyOpenSSL
pip3 install numpy

# extra python stuff

# part of osgeo4w, but
# not found for pip3
# pip3 install core
# pip3 install gdal-dev
# pip3 install pypiwin32
# pip3 install python-help
# pip3 install python-tcltk
# pip3 install python3-devel
# pip3 install pywin32
# pip3 install wx

# Not sure here, we have brew package for qscintilla already with sip
# pip3 install qscintilla

pip3 install certifi
pip3 install chardet
pip3 install coverage
pip3 install cycler
pip3 install decorator
pip3 install exifread
pip3 install future
pip3 install gdal
pip3 install h5py
pip3 install httplib2
pip3 install idna
pip3 install ipython-genutils
pip3 install jinja2
pip3 install jsonschema
pip3 install jupyter-core
pip3 install kiwisolver
pip3 install markupsafe
pip3 install matplotlib
pip3 install mock
pip3 install mock
pip3 install nbformat
pip3 install networkx
pip3 install nose2
pip3 install numpy
pip3 install owslib
pip3 install pandas
pip3 install pbr
pip3 install pip
pip3 install plotly
pip3 install ply
pip3 install psycopg2
pip3 install pygments
pip3 install pyodbc
pip3 install pyparsing
pip3 install pypubsub
pip3 install pysal
pip3 install pytz
pip3 install pyyaml
pip3 install requests
pip3 install retrying
pip3 install scipy
pip3 install setuptools
pip3 install shapely
pip3 install simplejson
pip3 install six
pip3 install test
pip3 install tools
pip3 install traitlets
pip3 install urllib3
pip3 install xlrd
pip3 install xlwt
pip3 install pillow