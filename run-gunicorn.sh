#!/bin/bash
set -euo pipefail

until echo > /dev/tcp/safers-db/5432; do sleep 1; done

cd $APP_HOME/server

setuser app pdm run ./manage.py createcachetable
setuser app pdm run ./manage.py migrate
setuser app pdm run ./manage.py collectstatic --no-input --link

exec /sbin/setuser app gunicorn config.wsgi

