#!/bin/bash -e

# determine full version
BASE_VERSION="$(cat 'version' | xargs).${BUILD_NUMBER:-local}"
GIT_SHA=$(git rev-parse --short HEAD)
DIRTY=$([[ -z $(git status -s) ]] || echo '-dirty')
VERSION=${BASE_VERSION}-${GIT_SHA}${DIRTY}

# Build the registration debian package
BASEDIR=/tmp/reg
NAME=waggle-registration
ARCH=all

mkdir -p ${BASEDIR}/DEBIAN
cat > ${BASEDIR}/DEBIAN/control <<EOL
Package: ${NAME}
Version: ${VERSION}
Maintainer: sagecontinuum.org
Description: Register with Beehive server
Architecture: ${ARCH}
Priority: optional
EOL

cp -p deb/reg/postinst ${BASEDIR}/DEBIAN/
cp -p deb/reg/prerm ${BASEDIR}/DEBIAN/

mkdir -p ${BASEDIR}/etc/systemd/system
mkdir -p ${BASEDIR}/usr/bin
cp -p ROOTFS/etc/systemd/system/waggle-registration.service ${BASEDIR}/etc/systemd/system/
cp -p ROOTFS/usr/bin/waggle-registration ${BASEDIR}/usr/bin

dpkg-deb --root-owner-group --build ${BASEDIR} "${NAME}_${VERSION}_${ARCH}.deb"

# Build the reverse tunnel debian package
BASEDIR=/tmp/reverse
NAME=waggle-reverse-tunnel
ARCH=all

mkdir -p ${BASEDIR}/DEBIAN
cat > ${BASEDIR}/DEBIAN/control <<EOL
Package: ${NAME}
Version: ${VERSION}
Maintainer: sagecontinuum.org
Description: Establish reverse SSH tunnel to Beehive
Architecture: ${ARCH}
Priority: optional
EOL

cp -p deb/reverse/postinst ${BASEDIR}/DEBIAN/
cp -p deb/reverse/prerm ${BASEDIR}/DEBIAN/

mkdir -p ${BASEDIR}/etc/systemd/system
mkdir -p ${BASEDIR}/usr/bin
cp -p ROOTFS/etc/systemd/system/waggle-reverse-tunnel.service ${BASEDIR}/etc/systemd/system/
cp -p ROOTFS/usr/bin/waggle-reverse-tunnel ${BASEDIR}/usr/bin

dpkg-deb --root-owner-group --build ${BASEDIR} "${NAME}_${VERSION}_${ARCH}.deb"
