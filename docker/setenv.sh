#!/bin/sh
# Managed by Docker image — heap tuned for 2-replica k8s pods
export JAVA_OPTS="${JAVA_OPTS:--Xms1024m -Xmx2048m -Djava.awt.headless=true -Dfile.encoding=UTF-8 --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED --add-exports=java.naming/com.sun.jndi.ldap=ALL-UNNAMED}"
