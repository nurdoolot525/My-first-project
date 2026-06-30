#!/usr/bin/env bash
set -e

python manage.py migrate --noinput
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000
