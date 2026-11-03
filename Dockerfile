FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive

ARG DEVOS_MIRROR_COUNTRY
ARG DEVOS_DEBIAN_MIRRORS=http://mirror.iranserver.com/debian/|http://mirror.iranserver.com/debian-security/,http://mirror.arvancloud.ir/debian/|http://mirror.arvancloud.ir/debian-security/,http://mirror.famaserver.com/debian/|http://mirror.iranserver.com/debian-security/,http://deb.debian.org/debian/|http://security.debian.org/debian-security/
COPY config/mirrors/${DEVOS_MIRROR_COUNTRY}/pip.conf /etc/pip.conf
COPY docker/install-builder-packages.sh /usr/local/sbin/install-builder-packages

RUN chmod 0755 /usr/local/sbin/install-builder-packages \
    && /usr/local/sbin/install-builder-packages "$DEVOS_DEBIAN_MIRRORS"

COPY docker/container-entrypoint.sh /usr/local/bin/devos-container-entrypoint
RUN chmod 0755 /usr/local/bin/devos-container-entrypoint

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/devos-container-entrypoint"]
CMD ["./scripts/build-iso.sh"]
