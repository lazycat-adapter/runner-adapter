# Build a custom amd64 delivery image from the matching upstream DIND runner.
# SOURCE_VERSION is supplied by lazycat-action from the selected Git tag.
ARG SOURCE_VERSION=6.0.1
FROM docker.io/gitea/runner:${SOURCE_VERSION}-dind

ARG SOURCE_VERSION
LABEL org.opencontainers.image.source="https://gitea.com/gitea/runner" \
      org.opencontainers.image.version="${SOURCE_VERSION}" \
      org.opencontainers.image.title="Gitea Runner for LazyCat"

RUN apk add --no-cache python3 py3-yaml
COPY migrate-config.py /usr/local/lib/lazycat-runner/migrate-config.py
COPY network-setup.sh /usr/local/bin/lazycat-runner-network-setup
RUN chmod 0755 /usr/local/bin/lazycat-runner-network-setup \
    && command -v gitea-runner \
    && command -v docker

# This adapter uses the existing LazyCat engine through the legacy socket mount.
ENV DOCKER_HOST=unix:///var/run/docker.sock
ENTRYPOINT ["/usr/local/bin/run.sh"]
