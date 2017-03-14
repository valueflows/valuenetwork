#!/usr/bin/env bash
# CWD should be the root of the git repository

./manage.py migrate

# :TODO: fix test fixtures
# ./manage.py loaddata ./fixtures/starters.json
# ./manage.py loaddata ./fixtures/help.json
# ./manage.py test valuenetwork.valueaccounting.tests
