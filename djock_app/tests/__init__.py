# In order to avoid running all tests, import and specify on command line, e.g. 
# $ ./manage.py test djock_app.DoorModelTests
from models_tests import DoorModelTests
from admin_tests import LockUserFormTests
from functional_tests import RenameLaterFunctionalTests
