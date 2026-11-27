#!/bin/sh
set -eu

if ! command -v docker >/dev/null 2>&1 || ! docker buildx version >/dev/null 2>&1; then
  apk update
  apk add --no-cache docker-cli docker-cli-buildx
fi

# The marker prevents a restart from replacing user-edited runner settings.
if [ ! -f /data/.gitearunner-lpk-config-v6 ]; then
  cat > /data/config.yaml <<'EOL'
log:
  level: info
metrics:
  enabled: true
  addr: ":8099"
runner:
  envs:
    DOCKER_CONFIG: /root/.docker
    BUILDX_BUILDER: gitea-runner-build
container:
  network: gitea-build
  docker_host: "-"
  options: "--volume /lzcsys/data/appvar/cloud.lazycat.app.gitearunner/data/docker-buildx:/root/.docker --volume /lzcsys/run/lzc-docker/docker.sock:/var/run/docker.sock"
  valid_volumes:
    - /lzcsys/data/appvar/cloud.lazycat.app.gitearunner/data/docker-buildx
    - /lzcsys/run/lzc-docker/docker.sock
EOL
  touch /data/.gitearunner-lpk-config-v6
fi

mkdir -p /data/docker-buildx
export DOCKER_CONFIG=/data/docker-buildx

if ! docker network inspect gitea-build >/dev/null 2>&1; then
  docker network create --driver bridge gitea-build
fi

docker buildx rm gitea-runner-build >/dev/null 2>&1 || true
docker buildx create \
  --name gitea-runner-build \
  --driver docker-container \
  --driver-opt network=gitea-build \
  --bootstrap
