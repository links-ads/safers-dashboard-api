#!/bin/bash
set -euo pipefail

cd $APP_HOME/server

export PIPENV_DONT_LOAD_ENV=1

setuser app pipenv run ./manage.py migrate
setuser app pipenv run ./manage.py createcachetable
setuser app pipenv run ./manage.py update_site
setuser app pipenv run ./manage.py collectstatic --no-input --link

exec /sbin/setuser app \
    uwsgi \
    --venv "$(pipenv --venv)" \
    --uwsgi-socket /tmp/uwsgi.sock \
    --chmod-socket=666 \
    --module wsgi:application \
    --need-app \
    --processes 4 \
    --master
