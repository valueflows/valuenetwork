#!/usr/bin/env bash
# CWD should be the root of the git repository

USER="$1"
EMAIL="$2"
PASSWORD="$3"

echo "from django.contrib.auth.models import User; User.objects.create_superuser('$USER', '$EMAIL', '$PASSWORD')" | python manage.py shell
