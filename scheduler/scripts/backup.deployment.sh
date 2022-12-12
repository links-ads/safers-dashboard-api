#!/bin/bash

# script to run backup commands from heroku-scheduler
# (need a separate script in order to cope w/ cron's minimal environment)

export DJANGO_SETTINGS_MODULE=config.settings

cd /app/server
python manage.py dbbackup
python manage.py mediabackup
