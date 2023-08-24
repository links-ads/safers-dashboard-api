#!/bin/bash

# script to run purge_camera_media command from cron
# (need a separate script in order to cope w/ cron's minimal environment)

export DJANGO_SETTINGS_MODULE=config.settings
export PIPENV_PIPFILE=/home/app/Pipfile

/usr/local/bin/pipenv run /home/app/server/manage.py purge_camera_media --logging
