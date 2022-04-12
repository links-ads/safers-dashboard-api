#!/bin/bash
set -euo pipefail

# export PIPENV_PIPFILE=$APP_HOME/Pipfile

cd $APP_HOME/server

# runs the RMQ message handler as a server

export DJANGO_SETTINGS_MODULE=config.settings

exec /sbin/setuser app pipenv run python3 -m safers.rmq.server