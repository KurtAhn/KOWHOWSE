#!/usr/bin/env bash

if [ "$1" == "all" ]; then
    rm db.sqlite3
    ./manage.py makemigrations || exit 1
    ./manage.py migrate || exit 1
fi

rm -r media
find kowhowse/migrations/ -path "*.py" -not -name "__init__.py" -delete
./manage.py makemigrations kowhowse || exit 1
./manage.py migrate kowhowse zero || exit 1
./manage.py makemigrations kowhowse || exit 1
./manage.py migrate kowhowse || exit 1
# python manage.py createsurvey || exit 1
