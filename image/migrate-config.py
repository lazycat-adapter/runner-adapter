"""Merge the LazyCat job network into an existing Runner configuration once."""
from pathlib import Path
import os
import shlex
import shutil
import sys
import tempfile
import yaml

DOCKER_CONFIG = "/lzcsys/data/appvar/cloud.lazycat.app.gitearunner/data/docker-buildx"
SOCKET = "/lzcsys/run/lzc-docker/docker.sock"


def migrate(path):
    original = path.read_bytes() if path.exists() else b""
    config = yaml.safe_load(original) or {}
    config.setdefault("log", {}).setdefault("level", "info")
    config.setdefault("metrics", {}).update(enabled=True, addr=":8099")
    envs = config.setdefault("runner", {}).setdefault("envs", {})
    envs.update(DOCKER_CONFIG="/root/.docker", BUILDX_BUILDER="gitea-runner-build")
    container = config.setdefault("container", {})
    container.update(network="gitea-build", docker_host="-")
    options = container.get("options") or ""
    tokens = shlex.split(options)
    volumes = container.setdefault("valid_volumes", [])
    for src, dest in [(DOCKER_CONFIG, "/root/.docker"), (SOCKET, "/var/run/docker.sock")]:
        mount = f"{src}:{dest}"
        if mount not in tokens and f"--volume={mount}" not in tokens:
            options = f"{options} --volume {mount}".strip()
        if src not in volumes:
            volumes.append(src)
    container["options"] = options
    if original:
        backup = path.with_name("config.before-lazycat-network.yaml")
        if not backup.exists():
            shutil.copy2(path, backup)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as out:
        yaml.safe_dump(config, out, allow_unicode=True, sort_keys=False)
    if path.exists():
        shutil.copymode(path, out.name)
    os.replace(out.name, path)


if __name__ == "__main__":
    migrate(Path(sys.argv[1]))
