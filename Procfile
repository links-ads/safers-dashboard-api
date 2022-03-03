#web: python manage.py runserver 0.0.0.0:$PORT
web: gunicorn safers-gateway.wsgi
python manage.py runserver 0.0.0.0:$PORT
release: python manage.py migrate

