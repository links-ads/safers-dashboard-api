# safers-dashboard-api

This API provides the backend for the safers-dashboard-app.

- [safers-dashboard-api](#safers-dashboard-api)
  - [components](#components)
    - [server](#server)
    - [auth](#auth)
    - [broker](#broker)
    - [worker](#worker)
    - [scheduler](#scheduler)
    - [storage](#storage)
  - [configuration](#configuration)
    - [superuser](#superuser)
    - [environment variables](#environment-variables)
    - [RMQ Keys](#rmq-keys)
    - [Fixtures](#fixtures)
    - [DataTypes](#datatypes)
  - [backups](#backups)
  - [localization](#localization)
  - [profiling](#profiling)
  - [logging](#logging)

## components

### server

Django / Django-Rest-Framework

### auth

FusionAuth

### broker

RabbitMQ

### worker

The RMQ app uses `pika` to monitor the SAFERS Message Queue.  Upon receipt of a message with a registered routing_key the handlers defined in `rmq.py#BINDING_KEYS` are called. 


### scheduler


The managemnt comamnd `manage.py purge_camera_media` should be run periodically to remove outdated camera_media objects.  

In development this is done by a separate **scheduler** service that uses `cron` to run `./scheduler/scripts/purge_camera_media.development.sh`.  In deployment, this is done by **heroku scheduler** which runs `./scheduler/scripts/purge_camera_media.deployment.sh`.

### storage

AWS S3

## configuration

### superuser

To setup the `admin` user so as to log into the `Django Admin Console` on http://localhost:8000/admin. Run the command to create the superuser `docker-compose exec server pipenv run ./server/manage.py createsuperuser`, this will create the user, but by default, the user will not be authorized, so you also need to run `docker-compose exec server pipenv run ./server/manage.py assign_groups --username admin --regex --groups admin`
### environment variables

several environment variables are required for **safers-dashboard-api**:

* DJANGO_SECRET_KEY
* DATABASE_URL="postgis://safers_user:safers_pwd@db:5432/safers_db"
* ACCOUNT_CONFIRM_EMAIL_CLIENT_URL="http://localhost:3000/auth/confirm-email/{key}"
* ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL="http://localhost:3000/auth/password/reset/{key}/{uid}"
* CLIENT_HOST="http://localhost:3000"
* FUSION_AUTH_API_KEY
* FUSION_AUTH_CLIENT_ID
* FUSION_AUTH_CLIENT_SECRET
* FUSION_AUTH_TENANT_ID
* FUSION_AUTH_TENANT_NAME
* FUSION_AUTH_EXTERNAL_BASE_URL="https://auth.safers-project.cloud"
* FUSION_AUTH_INTERNAL_BASE_URL="https://auth.safers-project.cloud"
* DJANGO_RMQ_TRANSPORT="amqp"
* DJANGO_RMQ_HOST="bus.safers-project.cloud"
* DJANGO_RMQ_PORT=5674
* DJANGO_RMQ_EXCHANGE="safers.b2b"
* DJANGO_RMQ_VHOST
* DJANGO_RMQ_QUEUE
* DJANGO_RMQ_USERNAME
* DJANGO_RMQ_PASSWORD
* DJANGO_RMQ_APP_ID="dsh"
* DJANGO_SENTRY_DSN
* DJANGO_SENTRY_EVN

### RMQ Keys

In addition, in order to ensure uniqueness among message ids, a `SiteProfile` should be configured.  This can be done in the Django Admin; simply ensure the profiles `code` is a unique string value.

### Fixtures

Finally, several fixtures are used to bootstrap the application:
* ./server/safers/users/fixtures/roles_fixture.json
* ./server/safers/users/fixtures/organizations_fixture.json
* ./server/safers/data/fixtures/datatypes_fixtures.json
* ./server/safers/aois/fixtures/aois_fixture.json
* ./server/safers/cameras/fixtures/cameras_fixture.json
* ./server/safers/chatbot/fixtures/chatbot_categories_fixture.json

these can all be added by running: `docker-compose exec server pipenv run ./server/manage.py configure`

### DataTypes

In order to show both operational and on-demand Data Layers, a `DataType` must be registerd.  The current set of data_types is stored in a remote spreadsheet [[datamappingform_imp.xlsx](https://istitutoboella.sharepoint.com/:x:/r/sites/ProjectSAFERS/_layouts/15/Doc.aspx?sourcedoc=%7BCB97483F-5F2A-473A-B5D8-EA7DE982E5BF%7D&file=datamappingform_imp.xlsx&action=default&mobileredirect=true)].  The admin action "Import DataTypes from CSV" can take that content and import it into the database; Note this is a brittle process, so backing up the database beforehand is recommended.

## backups

Periodic backups of the database and the media files are taken by the scheduler.  This utilises the "django-dbbackup" library.  

The filename format is "safers-dashboard-api-&lt;type&gt;_&lt;timestamp&gt;" where "type" is one of "db" or "media".  

The Django storages framework is used to store the backup files.  In development these are stored in `MEDIA_ROOT/backups`; They can be accessed directly from the local filesystem.  In deployment, these are stored in S3; They can be accessed using the AWS CLI: `aws --profile &lt;profile name&gt; s3 ls s3://&lt;bucket-root&gt;/backups/`.



## localization

Localization is enabled in **safers-dashboard-app**.  This localizes text used in the frontend, _not_ the backend.  The current set of localizations is stored in a remote spreadsheet [[dashboard-translations.xlsx](https://istitutoboella.sharepoint.com/:x:/r/sites/ProjectSAFERS/_layouts/15/Doc.aspx?sourcedoc=%7BBE15948D-43F1-4772-9D66-76215E5943A7%7D&file=dashboard-translations.xlsx&action=default&mobileredirect=true)].  There are scripts in **safers-dashboard-app** which take that content and import it; Note this is a manual process.

## profiling

Profiling is handled using cProfile & django-cprofile-middleware & snakeviz & silk.

- appending `&prof` to a URL will give a profile summary (in development only)
- appending `&prof&download` to a URL will create a file called "view.prof" which can be inspected by running `snakeviz ./path/to/view.prof` outside of docker
- db queries can be monitored by going to "http://localhost:8000/silk"

Alternatively - b/c the above is a bit "unuser-friendly" - django-debug-toolbar is also enabled.  It is a bit limited, obviously, b/c of Django Rest Framework.  For GETs, usage is: `localhost:8000/api/<whatever>/?format=json&debug-toolbar`

## logging

In development, stream-based logging is enabled.

In deployment, `sentry.io` is enabled.  This requires the environment variables `DJANGO_SENTRY_DSN` and `DJANGO_SENTRY_ENV` to be set.
