# Beekeeper Registration

Services running on the end-points that register with beekeeper and then
establish a reverse SSH tunnel to beekeeper based on the credentials returned
from that registration.


# create deb package
```bash
docker run -ti --rm -v `pwd`:/workdir -w /workdir ubuntu:20.04 /bin/bash -c 'apt-get update && apt-get install -y git && ./release.sh'
```