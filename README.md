# safers-dashboard-api

This API provides the backend for the safers-dashboard-app.

## components

### server

Django / Django-Rest-Framework

### auth

FusionAuth

### broker

RabbitMQ

### worker

Pika

### storage

AWS S3

## config

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

In addition, in order to ensure uniqueness among message ids, a `SiteProfile` should be configured.  This can be done in the Django Admin; simply ensure the profiles `code` is a unique string value.

Finally, several fixtures are used to bootstrap the application:
* ./server/safers/users/fixtures/roles_fixture.json
* ./server/safers/users/fixtures/organizations_fixture.json
* ./server/safers/data/fixtures/datatypes_fixtures.json
* ./server/safers/aois/fixtures/aois_fixture.json
* ./server/safers/cameras/fixtures/cameras_fixture.json
* ./server/safers/chatbot/fixtures/chatbot_categories_fixture.json
these can all be added by running: `manage.py configure`

## details

Users can authenticate locally or remotely (via FusionAuth).  Note that only remote users can interact w/ the SAFERS API - so there's really not much point in using the Dashboard as a local user.

The RMQ app uses `pika` to monitor the SAFERS Message Queue.  Upon receipt of a message with a registered routing_key the handlers defined in `rmq.py#BINDING_KEYS` are called. 

The managemnt comamnd `manage.py purge_camera_media` should be run periodically to remove outdated camera_media objects.  This can be done locally via cron.  In deployment, **heroku scheduler** is used for this functionality.

## profiling

Profiling is handled using cProfile & django-cprofile-middleware & snakeviz & silk.

- appending `&prof` to a URL will give a profile summary (in development only)
- appending `&prof&download` to a URL will create a file called "view.prof" which can be inspected by running `snakeviz ./path/to/view.prof` outside of docker
- db queries can be monitored by going to "http://localhost:8000/silk"

Alternatively - b/c the above is a bit "unuser-friendly" - django-debug-toolbar is also enabled.  It is a bit limited, obviously, b/c of Django Rest Framework.  For GETs, usage is: `localhost:8000/api/<whatever>/?format=json&debug-toolbar`
