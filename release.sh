#!/bin/bash -e


# determine full version
VER_LONG=$(git describe --tags --long | cut -c2-)
echo "VER_LONG: ${VER_LONG}"
# note that the first character "v" had to be stripped, debian requires version numbers to start with digit
# (git convention is to use a "v" as prefix in the version number)
# example (without "v"): 2.1.1-2-g146e8fc


VER_SHORT=$(echo ${VER_LONG} | cut -d '-' -f 1)
echo "VER_SHORT: ${VER_SHORT}"
# example: 2.1.1

REL_COMMIT_COUNT=$(echo ${VER_LONG} | cut -d '-' -f 2)
echo "REL_COMMIT_COUNT: ${REL_COMMIT_COUNT}"
# if this is not 0, do not do a release
# example: 2


if [[ ( "${REL_COMMIT_COUNT}_" != "0_" ) && "$1_" != "--force_" ]] ; then
    echo ""
    echo "Error:"
    echo "  The current git commit has not been tagged. Please create a new tag first to ensure a proper unique version number."
    echo "  Use --force to ignore error (for debugging only)"
    echo ""
    exit 1
fi



VER_HASH=$(echo ${VER_LONG} | cut -d '-' -f 1)
echo "VER_SHASH: ${VER_HASH}"


# Build the registration debian package
BASEDIR=/tmp/reg
NAME=waggle-registration
ARCH=all

mkdir -p ${BASEDIR}/DEBIAN
cat > ${BASEDIR}/DEBIAN/control <<EOL
Package: ${NAME}
Version: ${VER_LONG}
Maintainer: sagecontinuum.org
Description: Register with Beehive server
Architecture: ${ARCH}
Priority: optional
EOL

cp -p deb/reg/postinst ${BASEDIR}/DEBIAN/
cp -p deb/reg/prerm ${BASEDIR}/DEBIAN/

mkdir -p ${BASEDIR}/etc/systemd/system
mkdir -p ${BASEDIR}/usr/bin
cp -p waggle-registration.service ${BASEDIR}/etc/systemd/system/
cp -p waggle-registration.py ${BASEDIR}/usr/bin

set -x
dpkg-deb --root-owner-group --build ${BASEDIR} "${NAME}_${VER_SHORT}_${ARCH}.deb"
