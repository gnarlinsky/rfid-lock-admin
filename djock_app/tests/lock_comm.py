from django.test import TestCase
from termcolor import colored
from django.test.client import Client

"""
# to run only some tests: 
#   $ ./manage.py test djock_app.LockUserModelTest
"""

###################
# TO DO: 
###################
#  - additional_tests.py 
# smarter logging/info printing! http://stackoverflow.com/questions/284043/outputting-data-from-unit-test-in-python


class LockCommunicationTests(TestCase):  
    #fixtures = ['rename_back_to_initial_data.json']  # to save the test user so can succeed on login tests
    # TO DO: copy and rename the above to something that makes sense for here

    print colored("\nTestCase LockCommunicationTests", "white","on_green")
    print colored("\n\tTESTS: checking correct response/status for a particular URL - Given URL with door and rfid id's, is the response/status (whether the rfid is good for that door) correct?; given the get_allowed URL with door id, is the status and response (JSON with all allowed rfid's for that door) correct?","blue")
    print colored("\t(In fixture: \
                    \n\t- door with doorid 2 does exist; but no doors with id's aaaaa or 10 \
                    \n\t- rfid 1122135122  does exist; but not abc123, not 9123456789\
                    \n\t- door 2 is associated with 9999999992  and 1122135199  but not with 1122135122 (which does exist, but is associated with a different door) \
                    \n\t- 9999999992  is active \
                    \n\t- 9999999991 is associated with door 2 but is NOT active", \
                "green")

    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

    def setUp(self):
        self.c = Client()
        print colored("\n" + self._testMethodName + ": " + self._testMethodDoc, "cyan") # or you could just set verbosity=2 with manage.py !!!!!!

    ##########################################################
    #  RFID authentication
    ##########################################################
    # todo: comprehensive?
    def test_allowed_non_existing_door(self):
        """ get all allowed rfids for door that does not exist """
        response = self.c.get("/door/10/getallowed/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,'{"doorid": 10, "allowed_rfids": ""}')

    def test_allowed_wrong_format(self):
        """ get all allowed rfids for door in wrong format (incorrect url) """
        response = self.c.get("/door/aaaa/getallowed/")
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.content,"")

    def test_allowed_existing_door(self):
        """ get all allowed rfids for existing door """
        response = self.c.get("/door/2/getallowed/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,'{"doorid": 2, "allowed_rfids": ["1122135199", "9999999992"]}')

    # todo
    #def test_blah(self):
    #    """ get all allowed rfids for existing door (but there aren't any alloweds) """
    #    response = self.c.get("door/aaaa/get_allowed/")
    #    self.assertEqual(response.status_code,404)
    #    self.assertEqual(response.content,"")

    # todo
    #def test_blah(self):
    #    """ list of allowed rfids does not contain any inactive ones """
    #    response = self.c.get("door/aaaa/get_allowed/")
    #    self.assertEqual(response.status_code,404)
    #    self.assertEqual(response.content,"")

    def test_active_rfid_right_door(self):
        """ rfid associated with door, is active """
        response = self.c.get("/checkdoor/2/checkrfid/9999999992/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"1")

    def test_door_does_not_exist(self):
        """ door does not exist  """
        response = self.c.get("/checkdoor/10/checkrfid/1123456789/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")


    def test_rfid_does_not_exist(self):
        """ rfid does not exist """
        response = self.c.get("/checkdoor/2/checkrfid/9123456789/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")

    def test_active_rfid_wrong_door(self):
        """ rfid not associated with door 2, is active """
        response = self.c.get("/checkdoor/2/checkrfid/1122135122/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")

    def test_inactive_rfid_right_door(self):
        """ rfid was associated with door, but now inactive """
        response = self.c.get("/checkdoor/2/checkrfid/9999999991/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")

    def test_door_wrong_format_in_url(self):
        """ door id in wrong format (i.e. url wrong format, so not found error) """
        response = self.c.get("/checkdoor/aaaaa/checkrfid/1123456789/")
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.content,"")

    def test_rfid_wrong_format_in_url(self):
        """ rfid num in wrong format (i.e. url wrong format, so not found error) """
        response = self.c.get("/checkdoor/2/checkrfid/abc123/")
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.content,"")

    # todo:   check alphanumberic ok, e.g. "aaaaaaaaaa"
