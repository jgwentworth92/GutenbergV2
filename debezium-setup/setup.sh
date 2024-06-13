#!/bin/bash

# Create the secrets file
echo "Creating secrets file..."
echo "hostname=${POSTGRES_HOSTNAME}" >> /secrets/postgres.properties
echo "port=${POSTGRES_PORT}" >> /secrets/postgres.properties
echo "user=${POSTGRES_USER}" >> /secrets/postgres.properties
echo "db=${POSTGRES_DB}" >> /secrets/postgres.properties
echo "password=${POSTGRES_PASSWORD}" >> /secrets/postgres.properties

echo "Starting Debezium..."
/docker-entrypoint.sh start
