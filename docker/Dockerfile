# syntax=docker/dockerfile:1.6
# IdentityIQ app image — SSB customization build layered on Tomcat 9 / JDK 11.
# CI must place base/ga/identityiq-8.5.zip before docker build (oras pull from GHCR).

FROM eclipse-temurin:11-jdk-jammy AS ssb
RUN apt-get update \
  && apt-get install -y --no-install-recommends unzip zip ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Layer order: rarely changing SSB tooling first for cache hits
COPY build.xml build.sh build.bat build.properties servers.properties ./
COPY lib ./lib
COPY scripts ./scripts
COPY sandbox.ignorefiles.properties sandbox.target.properties ./
COPY sandbox.iiq.properties homelab.iiq.properties homelab.target.properties homelab.ignorefiles.properties ./
COPY web ./web
COPY src ./src
COPY config ./config
COPY base/ga/identityiq-8.5.zip ./base/ga/identityiq-8.5.zip

ARG SPTARGET=homelab
ENV SPTARGET=${SPTARGET}
RUN chmod +x build.sh lib/ant/bin/ant lib/ant/bin/antRun \
  && ./build.sh -Dtarget=${SPTARGET} clean war \
  && test -f build/deploy/identityiq.war \
  && mkdir -p /out/identityiq \
  && unzip -q build/deploy/identityiq.war -d /out/identityiq

# ----- Runtime -----
FROM tomcat:9.0-jdk11-temurin

ENV CATALINA_HOME=/usr/local/tomcat \
    IIQ_HOME=/usr/local/tomcat/webapps/identityiq \
    JAVA_OPTS="-Xms1024m -Xmx2048m -Djava.awt.headless=true -Dfile.encoding=UTF-8"

RUN rm -rf "${CATALINA_HOME}/webapps/*" \
  && mkdir -p "${IIQ_HOME}"

COPY --from=ssb /out/identityiq/ "${IIQ_HOME}/"
COPY docker/setenv.sh "${CATALINA_HOME}/bin/setenv.sh"
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x "${CATALINA_HOME}/bin/setenv.sh" /entrypoint.sh \
  && groupadd --system iiq && useradd --system --gid iiq --home-dir /usr/local/tomcat iiq \
  && chown -R iiq:iiq /usr/local/tomcat

USER iiq
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
