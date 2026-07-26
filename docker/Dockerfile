# syntax=docker/dockerfile:1.6
# Thin app image: customization overlay on identityiq-base (no GA re-expand).
# Requires: ghcr.io/beyond-boilerplate/identityiq-base:8.5 (or IIQ_BASE_IMAGE build-arg)

ARG IIQ_BASE_IMAGE=ghcr.io/beyond-boilerplate/identityiq-base:8.5

FROM ${IIQ_BASE_IMAGE} AS iiq-base

# ----- SSB customization (JDK + Ant); seed extract from base stock -----
FROM eclipse-temurin:11-jdk-jammy AS ssb
RUN apt-get update \
  && apt-get install -y --no-install-recommends unzip zip ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY --from=iiq-base /opt/iiq-stock /opt/iiq-stock
COPY --from=iiq-base /opt/ga-placeholder/identityiq-8.5.zip /opt/ga-placeholder/identityiq-8.5.zip

# Tooling layers first (cache-friendly)
COPY build.xml build.sh build.bat build.properties servers.properties ./
COPY lib ./lib
COPY scripts ./scripts
COPY sandbox.ignorefiles.properties sandbox.target.properties ./
COPY sandbox.iiq.properties homelab.iiq.properties homelab.target.properties homelab.ignorefiles.properties ./

# Customizations last — these change often
COPY web ./web
COPY src ./src
COPY config ./config

ARG SPTARGET=homelab
ENV SPTARGET=${SPTARGET}

# Seed build/extract so SSB skips GA zip expand; placeholder zip satisfies availability check.
# Do NOT run "clean" — that deletes extract and forces a full GA expand.
RUN mkdir -p build/extract base/ga base/patch base/efix/8.5 \
  && cp -a /opt/iiq-stock/. build/extract/ \
  && cp /opt/ga-placeholder/identityiq-8.5.zip base/ga/identityiq-8.5.zip \
  && chmod +x build.sh lib/ant/bin/ant lib/ant/bin/antRun \
  && ./build.sh -Dtarget=${SPTARGET} war \
  && test -f build/deploy/identityiq.war \
  && mkdir -p /out/identityiq \
  && unzip -q build/deploy/identityiq.war -d /out/identityiq

# ----- Runtime: reuse base Tomcat user/layout; replace IIQ tree only -----
FROM ${IIQ_BASE_IMAGE}

USER root
COPY --from=ssb /out/identityiq/ "${IIQ_HOME}/"
COPY docker/setenv.sh "${CATALINA_HOME}/bin/setenv.sh"
COPY docker/entrypoint.sh /entrypoint.sh
# Avoid chown -R of entire tree when possible — ownership on overlay only
RUN chmod +x "${CATALINA_HOME}/bin/setenv.sh" /entrypoint.sh \
  && chown -R iiq:iiq "${IIQ_HOME}" \
    "${CATALINA_HOME}/bin/setenv.sh" /entrypoint.sh

USER iiq
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
