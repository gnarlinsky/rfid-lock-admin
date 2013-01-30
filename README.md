Djock
=====

Django interface to manage RFID lock users

Just fire it up:

    $ rm djock.db #if it exists
    $ ./manage.py syncdb
    $ ./manage.py loaddata <your_fixture.json>   # or leave blank to load from djock_app/fixtures/init_data.json
    $ ./manage.py runserver         
