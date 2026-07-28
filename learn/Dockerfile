# Meridian IAM Academy — static lessons + live Verify API (homelab / public).
# Serves learn/dist and POST /api/verify/<lesson> against in-cluster IdentityIQ.
FROM python:3.12-slim-bookworm AS build
WORKDIR /src
COPY docs/lessons /src/docs/lessons
COPY learn /src/learn
RUN python3 /src/learn/build.py

FROM python:3.12-slim-bookworm
ARG KUBECTL_VERSION=v1.29.14
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl \
  && ARCH="$(dpkg --print-architecture)" \
  && case "$ARCH" in amd64) KARCH=amd64 ;; arm64) KARCH=arm64 ;; *) KARCH=amd64 ;; esac \
  && curl -fsSL -o /usr/local/bin/kubectl \
       "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${KARCH}/kubectl" \
  && chmod +x /usr/local/bin/kubectl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /src/learn/dist /app/learn/dist
COPY tools/academy /app/tools/academy
COPY tools/iiq-verify /app/tools/iiq-verify
COPY lab-data /app/lab-data
COPY docs/lessons /app/docs/lessons
COPY config/PACKS.md /app/config/PACKS.md
COPY config/Rule /app/config/Rule

ENV ACADEMY_HOST=0.0.0.0 \
    ACADEMY_PORT=8080 \
    IIQ_BASE_URL=http://identityiq.sailpoint.svc.cluster.local:8080/identityiq \
    IIQ_VERIFY_MODE=k8s \
    NAMESPACE=sailpoint \
    IIQ_DEPLOYMENT=identityiq \
    IIQ_USER=spadmin \
    IIQ_PASSWORD=admin \
    PYTHONUNBUFFERED=1

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --retries=10 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz')" || exit 1

CMD ["python3", "tools/academy/serve.py"]
