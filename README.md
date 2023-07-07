# safers-dashboard-api

This API provides the backend for the safers-dashboard-app.

- [safers-dashboard-api](#safers-dashboard-api)
  - [components](#components)
    - [database](#database)
    - [auth](#auth)
    - [broker](#broker)
    - [worker](#worker)
    - [scheduler](#scheduler)
    - [server](#server)
    - [storage](#storage)
  - [Development](#development)
    - [IDE Integration](#ide-integration)
    - [Virtual Environment](#virtual-environment)
    - [Local Settings](#local-settings)
    - [Permissions](#permissions)
    - [Testing](#testing)
    - [Running](#running)
      - [Configure the Superuser](#configure-the-superuser)
      - [Configure the Site](#configure-the-site)
      - [Configure DataTypes](#configure-datatypes)
      - [Run the Services](#run-the-services)
  - [backups](#backups)
  - [localization](#localization)
  - [profiling](#profiling)

## components

### database

**PostGIS** database is used for safers-dashboard-api.
### auth

**FusionAuth** is used for authentication.  This can be run locally for development (but not much else will work in safers because all the other components need to authenticate against tokens genreated from the _deployed_ authentication server).

When run locally, the local **PostGres** database, "safers-auth-db", must also be run.

The local instance of **FusionAuth** is bootstrapped using **kickstart**.  Kickstart will only run if the default API Key is unset.  This means that even if you change the "auth/kickstart.json" file you will have to manually recreate the authentication database.  The following command will do this: `docker container ls | grep safers-auth | awk '{print $1}' | xargs docker rm --force`.

When using the lcoal instance of **FusionAuth**, you must also populate "auth/.env" with the following environment variables:

```
FUSIONAUTH_ADMIN_EMAIL="admin@astrosat.net"
FUSIONAUTH_ADMIN_PASSWORD="password" 
FUSIONAUTH_API_KEY
FUSIONAUTH_APPLICATION_ID
FUSIONAUTH_CLIENT_ID
FUSIONAUTH_CLIENT_SECRET
FUSIONAUTH_TENANT_ID
FUSIONAUTH_TENANT_NAME
FUSIONAUTH_URL
FUSIONAUTH_INTERNAL_URL
FUSIONAUTH_EXTERNAL_URL
FUSIONAUTH_REDIRECT_URL
```

(These should match the values in "server/.env" and "client/.env".)

If bootstrapping succeeeds, you should see the following sort of output:

```
--------------------------------------------------------------------------------------
----------------------------------- Kickstarting ? -----------------------------------
--------------------------------------------------------------------------------------
io.fusionauth.api.service.system.kickstart.KickstartRunner - Summary:
- Created API key ending in [...HSnO]
- Completed [POST] request to [/api/tenant/<tenant-id>]
- Completed [POST] request to [/api/application/<applications-id>]
- Completed [POST] request to [/api/user/registration/]
```

The **FusionAuth** Admin should be available at https://localhost:9011.

As mentioned above, though, all of this is probably superfluous since very little of the dashboard will actually work if not authenticated using the _deployed_ instace of **FusionAuth**.

### broker

RabbitMQ

### worker

The RMQ app uses `pika` to monitor the SAFERS Message Queue.  Upon receipt of a message with a registered routing_key the handlers defined in `rmq.py#BINDING_KEYS` are called. 


### scheduler


The managemnt comamnd `manage.py purge_camera_media` should be run periodically to remove outdated camera_media objects.  

In development this is done by a separate **scheduler** service that uses `cron` to run `./scheduler/scripts/purge_camera_media.development.sh`.  In deployment, this is done by **heroku scheduler** which runs `./scheduler/scripts/purge_camera_media.deployment.sh`.


### server

Django / Django-Rest-Framework

### storage

AWS S3

## Development

### IDE Integration


A standard configuration for **VSCode** is included w/ this repository at ".vscode/settings.json" and ".editorconfig".  This ensures that linting, etc. works the same for all developers; It prevents local configuration discrepencies from cluttering up git diffs.

A standard set of extensions should also be used in **VSCode** by all developers.  These can be loaded in one go by using the [Astrosat VSCode Extensions Repository](https://github.com/astrosat/astrosat-vscode-extensions).

### Virtual Environment

This project uses `pdm`.  Unlike traditional python package and dependency managers, it doesn't create a complete virutal environment - instead it uses the existing python interpreter and isolates python packages in a local directory.  Docker mounts that directory ("server/__pypackages__") into the container.

One annoyance about this is that the binaries in the venv (like `yapf` for instance) will use the python interpreter from the container; VSCode, which runs on the local filesystem, cannot access that interpreter.  Therefore, those binaries should be re-installed using the global interpreter specified by pyenv.  This is not ideal, but it works.

One other minor annoyance is that although `pdm` is build to support PEP-582 it will default to using standard virtual environments unless PEP-582 is enabled globally.  Rather than impose that restriction on developers, this repository includes an empty "server/__pypackages__" directory which will force `pdm` to use PEP-582. More information can be found here: [https://pdm.fming.dev/latest/usage/pep582/](https://pdm.fming.dev/latest/usage/pep582/)

To add a package use `pdm add <package>` or `pdm add -dG <group> <package>`.

### Local Settings

The Django Server uses various environment variables as settings.  These are all automatically generated for CI and deployment.  But during development, users must provide them in "server/.env".  Here are some examples:

* DJANGO_SECRET_KEY
* DATABASE_URL="postgis://safers_user:safers_pwd@safers-db:5432/safers_db"
* FUSIONAUTH_API_KEY
* FUSIONAUTH_APPLICATION_ID
* FUSIONAUTH_CLIENT_ID
* FUSIONAUTH_CLIENT_SECRET
* FUSIONAUTH_TENANT_ID
* FUSIONAUTH_TENANT_NAME
* FUSIONAUTH_URL="https://auth.safers-project.cloud"
* FUSION_AUTH_EXTERNAL_URL="https://auth.safers-project.cloud"
* FUSION_AUTH_INTERNAL_URL="https://auth.safers-project.cloud"
* DJANGO_RMQ_TRANSPORT="amqp"
* DJANGO_RMQ_HOST="bus.safers-project.cloud"
* DJANGO_RMQ_PORT=5674
* DJANGO_RMQ_EXCHANGE="safers.b2b"
* DJANGO_RMQ_VHOST
* DJANGO_RMQ_QUEUE
* DJANGO_RMQ_USERNAME
* DJANGO_RMQ_PASSWORD
* DJANGO_RMQ_APP_ID="dsh"

### Permissions

The server directory is mounted as a volume inside the docker container.  In order to facilitate this, though, the "app" user in the container must have the same user id and group id as the local user.  A ".env" file at the same level as the Dockerfile is used to store these values.  The following command can generate that ".env" file:

```bash
echo -e "RUN_AS_UID=$(id -u)\nRUN_AS_GID=$(id -g)"  >> .env
```

Failure to do this may result in permissions errors when Django tries to copy static or media files or when the local user tries to modify files in the virtual environment.


### Testing

This project uses `pytest` rather than the built-in Django testing framework to test the server code.  This can be run locally via `pdm run test`.  This will provide terminal output detailing each test run and providing a stack trace for any failing test.  It will also produce a pretty HTML report for that test run.  Previous test runs are archived in "server/archive" and the report allows you to compare current test results with archived tests.

The test are run in **github** whenever code is pushed.  Again, this will provide both terminal output in the workflow trace and an HTML report as an artifact.  The latter can be downloaded and viewed in the browser.  At this time, reports genreated in CI will not include any archived test results.


### Running

#### Configure the Superuser

In order to interact with the Django Admin you must first create a superuser:

`docker-compose exec safers-server pdm run ./manage.py createsuperuser`

You will be prompted for an email and password.  It is recommended to use "admin@astrosat.net" and "password" during development.


#### Configure the Site

Every domain that a Django Project is deployed to is associated with a `Site` instance.  In **orbison** every `Site` has a `SiteProfile` associated with it.  

It is a good idea to set the default site (the one that `settings.SITE_ID` references) to the development server by running `docker-compose exec orbison-server pdm run ./manage.py update_site --domain localhost:8000 --name DEVELOPMENT`.

Additionally, in order to ensure uniqueness among message ids in RabbitMQ, the `SiteProfile` contains a `code` attribute.  This should be set in the Django Admin; just ensure the code is also registered with the deployed instance of **RabbitMQ**.

#### Configure DataTypes

In order to show both operational and on-demand Data Layers, a `DataType` must be registerd.  The current set of data_types is stored in a remote spreadsheet [[datamappingform_imp.xlsx](https://istitutoboella.sharepoint.com/:x:/r/sites/ProjectSAFERS/_layouts/15/Doc.aspx?sourcedoc=%7BCB97483F-5F2A-473A-B5D8-EA7DE982E5BF%7D&file=datamappingform_imp.xlsx&action=default&mobileredirect=true)].  The admin action "Import DataTypes from CSV" can take that content and import it into the database; Note this is a brittle process, so backing up the database beforehand is recommended.
#### Run the Services

safers-dashboard-api is run locally via docker-compose.  It is recommended, though not necessary, to run each service in a separate terminal pane so that each container's output is easily distinguished.

Prior to running make sure that you have followed the instructions in [Local Settings](#local-settings) and [Permissions](#permissions).

The following command will run a service: `docker-compose up <service-name>`

Having run the server, if you need to interact with it via the termnial you may use the following command:  `docker-compose exec safers-server pdm run ./manage.py <command>`

The server should be available in the browser at **[http://localhost:8000](http://localhost:8000)**.
## backups

Periodic backups of the database and the media files are taken by the scheduler.  This utilises the "django-dbbackup" library.  

The filename format is "safers-dashboard-api-&lt;type&gt;_&lt;timestamp&gt;" where "type" is one of "db" or "media".  

The Django storages framework is used to store the backup files.  In development these are stored in `MEDIA_ROOT/backups`; They can be accessed directly from the local filesystem.  In deployment, these are stored in S3; They can listed using: `aws --profile &lt;profile name&gt; s3 ls s3://&lt;bucket-name&gt;/backups/`
and downloaded using: `aws --profile &lt;profile name&gt; s3api get-object --bucket &lt;bucket-name&gt; --key backups/&lt;backup-file&gt; &lt;backup-file&gt;`.



## localization

Localization is enabled in **safers-dashboard-app**.  This localizes text used in the frontend, _not_ the backend.  The current set of localizations is stored in a remote spreadsheet [[dashboard-translations.xlsx](https://istitutoboella.sharepoint.com/:x:/r/sites/ProjectSAFERS/_layouts/15/Doc.aspx?sourcedoc=%7BBE15948D-43F1-4772-9D66-76215E5943A7%7D&file=dashboard-translations.xlsx&action=default&mobileredirect=true)].  There are scripts in **safers-dashboard-app** which take that content and import it; Note this is a manual process.

## profiling

Profiling is handled using **silk*.  Request info can be monitored by going to "http://localhost:8000/silk".  All requests will provide high level timing information.  Actual profiling must be enabled on a per-view basis using the `silk_profile` decorator and/or context manager.

