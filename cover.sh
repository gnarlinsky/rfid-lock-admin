#!/usr/bin/env bash

coverage run manage.py test djock_app
coverage report -m --include="djock_app/*"
coverage html --include="djock_app/*"
open htmlcov/index.html
