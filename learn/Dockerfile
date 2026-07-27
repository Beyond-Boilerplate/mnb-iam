# Static Meridian IAM Academy (markdown lessons → HTML)
FROM python:3.12-alpine AS build
WORKDIR /src
COPY docs/lessons /src/docs/lessons
COPY learn /src/learn
RUN python3 /src/learn/build.py

FROM nginx:1.27-alpine
COPY learn/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/learn/dist/ /usr/share/nginx/html/
EXPOSE 8080
HEALTHCHECK CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
