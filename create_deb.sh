#!/bin/bash -e

BASEDIR=$(mktemp -d)
NAME=waggle-registration
ARCH=all

# add package description
mkdir -p ${BASEDIR}/DEBIAN
cat <<EOF > ${BASEDIR}/DEBIAN/control
Package: ${NAME}
Version: ${VERSION_LONG}
Maintainer: sagecontinuum.org
Description: Register with Beehive server
Architecture: ${ARCH}
Priority: optional
Depends: python3-click
EOF

# add control files
cp -p deb/reg/postinst ${BASEDIR}/DEBIAN/
cp -p deb/reg/prerm ${BASEDIR}/DEBIAN/

mkdir -p ${BASEDIR}/etc/systemd/system
mkdir -p ${BASEDIR}/usr/bin

# add core files

cp -p waggle-registration.service ${BASEDIR}/etc/systemd/system/
cp -p waggle-registration.py ${BASEDIR}/usr/bin

sed -e "s/{{VERSION}}/${VERSION_LONG}/; w ${BASEDIR}/usr/bin/waggle-registration.py" ./waggle-registration.py
chmod +x ${BASEDIR}/usr/bin/waggle-registration.py

# build deb
dpkg-deb --root-owner-group --build ${BASEDIR} "${NAME}_${VERSION_SHORT}_${ARCH}.deb"
mv *.deb /output/
