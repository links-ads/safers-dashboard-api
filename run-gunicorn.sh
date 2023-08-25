#!/bin/bash
set -euo pipefail

until echo > /dev/tcp/safers-deployment-db/5432; do sleep 1; done

cd $APP_HOME/server

setuser app pdm run ./manage.py createcachetable
setuser app pdm run ./manage.py migrate
setuser app pdm run ./manage.py collectstatic --no-input

exec /sbin/setuser app pdm run gunicorn --bind :8000 config.wsgi
