#!/bin/bash -e

docker run --rm \
  -e NAME="waggle-bk-registration" \
  -e DESCRIPTION="Register with Beekeeper server" \
  -v "$PWD:/repo" \
  waggle/waggle-deb-builder:latest
