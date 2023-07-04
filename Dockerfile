FROM phusion/baseimage:jammy-1.0.1

ENV APP_HOME=/home/app

RUN useradd -ms /bin/bash app && usermod -aG www-data app

# Install base packages
RUN install_clean build-essential postgresql-client \
  software-properties-common figlet toilet tmux \
  python3 python3-dev python3-setuptools python3-wheel python3-pip \
  python3-gdal python3-venv nginx curl htop less git gpg
RUN pip install pdm --no-cache-dir


USER app
WORKDIR $APP_HOME

# set all services to be off (0); they can be explicitly enabled (1) at runtime
ENV ENABLE_DJANGO=0
ENV ENABLE_GUNICORN=0
ENV ENABLE_UWSGI=0
ENV ENABLE_RMQ_WORKER=0
ENV ENABLE_CRON=0

# copy runtime scripts...
COPY --chown=root:root run-django.sh $APP_HOME/
COPY --chown=root:root run-celery.sh $APP_HOME/
COPY --chown=root:root run-gunicorn.sh $APP_HOME/
# COPY --chown=root:root run-uwsgi.sh $APP_HOME/
COPY --chown=root:root run-rmq-worker.sh $APP_HOME/

USER root


# run startup script as per https://github.com/phusion/baseimage-docker#running_startup_scripts
RUN mkdir -p /etc/my_init.d
COPY startup.sh /etc/my_init.d/startup.sh
