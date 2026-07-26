# syntax=docker/dockerfile:1.6
# Thin app image: customization overlay on identityiq-base (no GA re-expand).
# Uses SSB "main" (not war) so we avoid packaging+re-unzip of the full tree.

ARG IIQ_BASE_IMAGE=ghcr.io/beyond-boilerplate/identityiq-base:8.5

FROM ${IIQ_BASE_IMAGE} AS iiq-base

FROM eclipse-temurin:11-jdk-jammy AS ssb
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Tooling first (cache-friendly)
COPY build.xml build.sh build.bat build.properties servers.properties ./
COPY lib ./lib
COPY scripts ./scripts
COPY sandbox.ignorefiles.properties sandbox.target.properties ./
COPY sandbox.iiq.properties homelab.iiq.properties homelab.target.properties homelab.ignorefiles.properties ./
COPY web ./web
COPY src ./src
COPY config ./config

# Seed extract from base stock; placeholder zip satisfies SSB availability check.
# Do NOT run "clean" — that deletes extract and forces a full GA expand.
COPY --from=iiq-base /opt/iiq-stock /tmp/iiq-stock
COPY --from=iiq-base /opt/ga-placeholder/identityiq-8.5.zip /tmp/identityiq-8.5.zip

ARG SPTARGET=homelab
ENV SPTARGET=${SPTARGET}

RUN mkdir -p build/extract base/ga base/patch base/efix/8.5 \
  && cp -a /tmp/iiq-stock/. build/extract/ \
  && rm -rf /tmp/iiq-stock \
  && cp /tmp/identityiq-8.5.zip base/ga/identityiq-8.5.zip \
  && rm -f /tmp/identityiq-8.5.zip \
  && chmod +x build.sh lib/ant/bin/ant lib/ant/bin/antRun \
  && ./build.sh -Dtarget=${SPTARGET} main \
  && test -d build/extract/WEB-INF \
  && mv build/extract /out-identityiq \
  && rm -rf build

FROM ${IIQ_BASE_IMAGE}

USER root
# Replace stock tree with customized extract (no full-tree chown of base layers)
RUN rm -rf "${IIQ_HOME}" && mkdir -p "${IIQ_HOME}"
COPY --from=ssb /out-identityiq/ "${IIQ_HOME}/"
COPY docker/setenv.sh "${CATALINA_HOME}/bin/setenv.sh"
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x "${CATALINA_HOME}/bin/setenv.sh" /entrypoint.sh \
  && chown -R iiq:iiq "${IIQ_HOME}" \
    "${CATALINA_HOME}/bin/setenv.sh" /entrypoint.sh

USER iiq
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
