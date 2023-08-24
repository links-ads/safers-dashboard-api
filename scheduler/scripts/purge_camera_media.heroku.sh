#!/bin/bash

# script to run purge_camera_media command from heroku-scheduler
# (need a separate script in order to cope w/ cron's minimal environment)

export DJANGO_SETTINGS_MODULE=config.settings

cd /app/server
python manage.py purge_camera_media --logging
