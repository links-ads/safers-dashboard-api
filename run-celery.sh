#!/bin/bash
set -euo pipefail

# export PIPENV_PIPFILE=$APP_HOME/Pipfile

cd $APP_HOME/server

# runs the task runner and scheduler as a single process
# in the future we will want to seperate this out, so the worker and scheduler
# are independant.

export DJANGO_SETTINGS_MODULE=config.settings

exec /sbin/setuser app \
    pipenv run celery \
    --app=safers.tasks.celery:app worker \
    --beat --scheduler django_celery_beat.schedulers.DatabaseScheduler \
    --loglevel=INFO -n worker.%h
