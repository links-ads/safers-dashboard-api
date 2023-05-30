#!/bin/bash
set -euo pipefail

cd $APP_HOME/server

# runs the RMQ message handler as a server

export DJANGO_SETTINGS_MODULE=config.settings

exec /sbin/setuser app pdm run python3 -m safers.rmq.server
