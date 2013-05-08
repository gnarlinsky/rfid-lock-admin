## About

Django interface to manage RFID lock users

## Quick start

To minimize dependency issues, make a new virtualenv, e.g. 

    $ mkdir ve
    $ virtualenv ve --no-site-packages

activate it, 

    $ source ve/bin/activate

and pip install the requirements.txt. 

    $ pip install -r path/to/requirements.txt


Then fire up the development server:

    $ rm djock.db #if it exists
    $ ./manage.py syncdb
    $ ./manage.py loaddata <your_fixture.json>   # if rfid_lock_management/fixtures/init_data.json exists and you want to use it, just skip this step -- syncdb will load fixtures/init_data.[json/xml/yaml] if it exists.
    $ ./manage.py runserver         

And go to 

    http://localhost:8000/lock
