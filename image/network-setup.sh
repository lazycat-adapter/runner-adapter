#!/bin/sh
set -eu

if [ ! -f /data/.gitearunner-lpk-config-v6 ]; then
  python3 /usr/local/lib/lazycat-runner/migrate-config.py /data/config.yaml
  touch /data/.gitearunner-lpk-config-v6
fi

mkdir -p /data/docker-buildx
export DOCKER_CONFIG=/data/docker-buildx
if ! docker network inspect gitea-build >/dev/null 2>&1; then
  docker network create --driver bridge gitea-build
fi

if ! docker buildx inspect gitea-runner-build >/dev/null 2>&1; then
  docker buildx create --name gitea-runner-build --driver docker-container --driver-opt network=gitea-build
fi
docker buildx inspect --bootstrap gitea-runner-build
