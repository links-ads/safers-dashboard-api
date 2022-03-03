#web: python manage.py runserver 0.0.0.0:$PORT
web: cd server && gunicorn safers-gateway.wsgi
release: cd server && python manage.py migrate

