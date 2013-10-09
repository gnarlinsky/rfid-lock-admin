The script `cover.sh` (in the top-level directory, on the same level as
`manage.py`) runs both the unit and functional tests (see
:mod:`rfid_lock_management.tests`) and determines test coverage, with detailed
HTML results.

.. code-block:: shell

    $ ./cover.sh 
    Creating test database for alias 'default'...
    .........................................................
    ----------------------------------------------------------------------
    Ran 57 tests in 84.264s

    OK
    Destroying test database for alias 'default'...
    Name                                               Stmts   Miss  Cover   Missing
    --------------------------------------------------------------------------------
    proj_rfid_lock_management/__init__                     0      0   100%   
    proj_rfid_lock_management/settings                    31      0   100%   
    proj_rfid_lock_management/urls                        10      0   100%   
    rfid_lock_management/__init__                          0      0   100%   
    rfid_lock_management/admin                           137      7    95%   79-92
    rfid_lock_management/misc_helpers                      9      7    22%   9-18
    rfid_lock_management/models                          186      0   100%   
    rfid_lock_management/templatetags/__init__             0      0   100%   
    rfid_lock_management/templatetags/custom_filters      35      0   100%   
    rfid_lock_management/views                            98      0   100%   
    --------------------------------------------------------------------------------
    TOTAL                                                506     14    97%   

    ----------------------------------------------------------------------
    HTML results are in htmlcov/index.html


.. note::
    **Cover.sh** - The line ``open htmlcov/index.html`` opens the HTML
    coverage information with your system's default browser. Note this may only work
    in OS X, where the ``open`` command opens directories and files with the
    default application for the file's extension — so you might want to comment out
    that statement.

