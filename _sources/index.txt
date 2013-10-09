.. demo documentation master file, created by Nadia Karlinsky


#####################################################
RFID Lock Management Interface - Documentation
#####################################################

.. toctree::
   :maxdepth: 6

   index

About
===============

This volunteer project is a collaboration with my local Makerspace to set up an
RFID lock system for doors in the building that houses the Makerspace. My role
included creating a Django web interface for staff users to manage lock users
and locked spaces, which involves, for example, assigning/un-assigning RFID
keycards; managing lock users' permissions for access to various spaces;
viewing logs and stats about visitors. Apart from the interface, I worked with
other volunteers on communication with the RFID lock system hardware to
authenticate scanned cards.


Created with
=============================================================

Python/Django/SQLite (development version)

Responsively styled with `Bootstrap <http://getbootstrap.com/>`_.

The code is at `https://github.com/gnarlinsky/rfid-lock-admin
<https://github.com/gnarlinsky/rfid-lock-admin>`_.


Setting up and running the application
==========================================

Clone the repository. 

.. code-block:: shell

    $ git clone git@github.com:gnarlinsky/rfid-lock-admin.git

To avoid dependency issues, create a virtualenv and install the required packages.

.. code-block:: shell

    $ cd rfid-lock-admin
    $ virtualenv ve --no-site-packages
    $ source ve/bin/activate      # activate the virtual environment
    $ pip install -r requirements.txt

Create the database and load the initial data.

.. code-block:: shell

    $ python manage.py syncdb
    $ python manage.py loaddata rfid_lock_management/fixtures/initial.json

Run the Django development server. 

.. code-block:: shell

    $ python manage.py runserver   

Go to `http://localhost:8000/lockadmin <http://localhost:8000/lockadmin>`_ to see the application in action.  (You can log in as user "moe" and password "moe") 


Testing and coverage
============================
.. include:: testing_and_coverage.rst

Developer documentation
===============================

API
--------
.. toctree::
   :maxdepth: 4

   main
   other
   tests

RFID keycard authentication
--------------------------------
(link to html with keycard_authentication.pdf)

<a href="keycard_authentication.html">RFID keycard authentication</a>

End user documentation and walkthroughs
==================================================
(link to html with the_interface.pdf)

<a href="the_interface.html">Staff user interface</a>

Meta
=========
This documentation
---------------------
Documentation created with `Sphinx, a Python document generator
<http://sphinx-doc.org/>`_.


Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
