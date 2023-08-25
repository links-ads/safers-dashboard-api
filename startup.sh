#!/bin/bash
set -eo pipefail

# startup script to determine which service(s) to launch at runtime

# generate ASCII banner
figlet -t "safers-dashboard-api"

# ensure "app" user in the container has same ids as local user outside the container
# (this allows them to both edit files in the mounted volume(s))
if [ ! -z ${RUN_AS_UID} ]; then usermod --uid $RUN_AS_UID app; fi
if [ ! -z ${RUN_AS_GID} ]; then groupmod --gid $RUN_AS_GID app; fi

# install dependencies
cd "${APP_HOME}/server"
setuser app pdm install

if [[ "${ENABLE_DJANGO}" -eq 1 ]]; then
    echo -e "\n### STARTING DJANGO ###\n"
    mkdir -p /etc/service/django
    cp ../run-django.sh /etc/service/django/run
fi

if [[ "${ENABLE_GUNICORN}" -eq 1 ]]; then
    echo -e "\n### STARTING GUNICORN ###\n"
    mkdir -p /etc/service/gunicorn
    cp ../run-gunicorn.sh /etc/service/gunicorn/run
fi

if [[ "${ENABLE_UWSGI}" -eq 1 ]]; then
    echo -e "\n### STARTING UWSGI ###\n"
    mkdir -p /etc/service/uwsgi
    cp ../run-uwsgi.sh /etc/service/uwsgi/run
fi

if [[ "${ENABLE_RMQ_WORKER}" -eq 1 ]]; then
    echo -e "\n### STARTING RMQ WORKER ###\n"
    mkdir -p /etc/service/rmq-worker
    cp ../run-rmq-worker.sh /etc/service/rmq-worker/run
fi

if [[ "${ENABLE_CRON}" -eq 1 ]]; then
    echo -e "\n### STARTING CRON ###\n"
    crontab < $APP_HOME/scheduler/crontab
fi

