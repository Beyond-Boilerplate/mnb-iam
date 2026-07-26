#!/bin/sh
# Runtime iiq.properties overlay (homelab CD e2e marker: 2026-07-26)
set -eu

IIQ_PROPS="${IIQ_HOME}/WEB-INF/classes/iiq.properties"

set_prop() {
  key="$1"
  val="$2"
  [ -n "$val" ] || return 0
  # Use awk for safe replacement (values may contain &)
  awk -v k="$key" -v v="$val" '
    BEGIN { FS=OFS="=" }
    $1==k { print k "=" v; found=1; next }
    { print }
    END { if (!found) print k "=" v }
  ' "$IIQ_PROPS" >"${IIQ_PROPS}.tmp" && mv "${IIQ_PROPS}.tmp" "$IIQ_PROPS"
}

set_prop dataSource.url "${IIQ_DB_URL:-}"
set_prop dataSource.username "${IIQ_DB_USER:-}"
set_prop dataSource.password "${IIQ_DB_PASSWORD:-}"
set_prop pluginsDataSource.url "${IIQ_PLUGIN_DB_URL:-}"
set_prop pluginsDataSource.username "${IIQ_PLUGIN_DB_USER:-}"
set_prop pluginsDataSource.password "${IIQ_PLUGIN_DB_PASSWORD:-}"
set_prop dataSourceAccessHistory.url "${IIQ_AH_DB_URL:-}"
set_prop dataSourceAccessHistory.username "${IIQ_AH_DB_USER:-}"
set_prop dataSourceAccessHistory.password "${IIQ_AH_DB_PASSWORD:-}"

if [ "${IIQ_DB_TYPE:-postgresql}" = "postgresql" ]; then
  set_prop dataSource.driverClassName org.postgresql.Driver
  set_prop pluginsDataSource.driverClassName org.postgresql.Driver
  set_prop dataSourceAccessHistory.driverClassName org.postgresql.Driver
  set_prop sessionFactory.hibernateProperties.hibernate.dialect sailpoint.persistence.PostgreSQL10Dialect
  set_prop sessionFactoryAccessHistory.hibernateProperties.hibernate.dialect sailpoint.persistence.PostgreSQL10Dialect
  set_prop scheduler.quartzProperties.org.quartz.jobStore.driverDelegateClass org.quartz.impl.jdbcjobstore.PostgreSQLDelegate
fi

exec catalina.sh run
