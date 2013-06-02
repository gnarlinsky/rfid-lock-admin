## About

Django interface to manage RFID lock users

## Quick start

Clone the repository. 

    $ git clone git@github.com:gnarlinsky/rfid-lock-admin.git

To avoid dependency issues, create a virtualenv and install the required packages.

    $ cd rfid-lock-admin
    $ virtualenv ve --no-site-packages
    $ source ve/bin/activate      # activate the virtual environment
    $ pip install -r requirements.txt

Create the database and load the initial data.

    $ python manage.py syncdb
    $ python manage.py loaddata rfid_lock_management/fixtures/lockuser_keycard_perm_user_accesstime_door_user.json

Run the Django development server. 

    $ python manage.py runserver   

Go to [http://localhost:8000/lockadmin](http://localhost:8000/lockadmin) to see the application in action. 

