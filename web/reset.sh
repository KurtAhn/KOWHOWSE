#!/usr/bin/env bash

if [ "$1" == "all" ]; then
    rm db.sqlite3
    ./manage.py makemigrations || exit 1
    ./manage.py migrate || exit 1
fi

rm -r media
find survey/migrations/ -path "*.py" -not -name "__init__.py" -delete
./manage.py makemigrations survey || exit 1
./manage.py migrate survey zero || exit 1
./manage.py makemigrations survey || exit 1
./manage.py migrate survey || exit 1
# python manage.py createsurvey || exit 1
