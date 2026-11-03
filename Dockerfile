FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        ca-certificates \
        debootstrap \
        findutils \
        live-build \
        squashfs-tools \
        xorriso \
    && rm -rf /var/lib/apt/lists/*

COPY docker/container-entrypoint.sh /usr/local/bin/devos-container-entrypoint
RUN chmod 0755 /usr/local/bin/devos-container-entrypoint

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/devos-container-entrypoint"]
CMD ["./scripts/build-iso.sh"]
