#!/bin/bash
set -euo pipefail

# no need to call `/sbin/setuser` since cron should be run as root

crontab < $APP_HOME/scheduler/crontab
exec cron -f
