FROM phusion/baseimage:focal-1.0.0-amd64

ENV APP_HOME=/home/app/

RUN useradd -ms /bin/bash app && usermod -aG www-data app

# Install base packages
RUN install_clean gettext postgresql-client \
  build-essential python3 python3-dev python3-gdal python3-setuptools \
  python3-wheel python3-pip python3-venv nginx htop less git gpg \
  software-properties-common tmux nodejs yarn

# Install uwsgi
RUN pip3 install --upgrade \
  uwsgi \
  pipenv==2021.5.29

USER app

ENV PIPENV_DONT_LOAD_ENV=1
ENV PIPENV_NO_SPIN=1
ENV PIPENV_VENV_IN_PROJECT=1

# All services are off by default, must be enabled at runtime
ENV ENABLE_CELERY=0
ENV ENABLE_DJANGO=0
ENV ENABLE_UWSGI=0

WORKDIR $APP_HOME

# install deps
COPY --chown=app:app ./Pipfile* $APP_HOME/
RUN cd $APP_HOME && pipenv install --dev
ENV PIPENV_PIPFILE=$APP_HOME/Pipfile


COPY --chown=root:root run-django.sh $APP_HOME/
COPY --chown=root:root run-celery.sh $APP_HOME/
COPY --chown=root:root run-gunicorn.sh $APP_HOME/
# COPY --chown=root:root run-uwsgi.sh $APP_HOME/

USER root


# run startup script as per https://github.com/phusion/baseimage-docker#running_startup_scripts
RUN mkdir -p /etc/my_init.d
COPY startup.sh /etc/my_init.d/startup.sh
