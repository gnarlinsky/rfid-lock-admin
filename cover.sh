#!/usr/bin/env bash

coverage run manage.py test rfid_lock_management 

#coverage report -m --include="rfid_lock_management/*" --omit="rfid_lock_management/misc.py,rfid_lock_management/tests/*"

# don't report on django packages, or any other packages that aren't mine
coverage report -m --include="rfid_lock_management/*,proj_rfid_lock_management/*" --omit="rfid_lock_management/tests/*,/Users/gnadia/Insync/gnadia.code@gmail.com/ve/*"

coverage html --include="rfid_lock_management/*,proj_rfid_lock_management/" --omit="rfid_lock_management/tests/*,/Users/gnadia/Insync/gnadia.code@gmail.com/ve/*"

echo ""
echo "HTML results are in htmlcov/index.html"

# note: only os x
open htmlcov/index.html
