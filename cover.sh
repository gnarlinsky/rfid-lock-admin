#!/usr/bin/env bash

coverage run manage.py test djock_app

#coverage report -m --include="djock_app/*" --omit="djock_app/misc.py,djock_app/tests/*"

# don't report on django packages, or any other packages that aren't mine
coverage report -m --include="djock_app/*,proj_djock/*" --omit="djock_app/misc.py,djock_app/tests/*,/Users/gnadia/Insync/gnadia.code@gmail.com/ve/*"

#coverage html --include="djock_app/*" --omit="djock_app/misc.py,djock_app/tests/*"
coverage html --include="djock_app/*,proj_djock/" --omit="djock_app/misc.py,djock_app/tests/*,/Users/gnadia/Insync/gnadia.code@gmail.com/ve/*"

open htmlcov/index.html
