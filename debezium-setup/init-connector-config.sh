#!/bin/sh

# Iterate over JSON files and initialize connectors
for file in /kafka/debezium-setup/*.json; do
  echo "Initializing connector from $file"
  curl -X POST -H "Content-Type: application/json" --data @$file http://debezium:8083/connectors
done
