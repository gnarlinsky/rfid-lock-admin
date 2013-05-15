from django.test import TestCase
from termcolor import colored
from django.test.client import Client
import simplejson
from rfid_lock_management.models import NewKeycardScan, AccessTime


class LockCommunicationTests(TestCase):  
    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

    def setUp(self):
        self.client = Client()
        print colored("\nTestCase LockCommunicationTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") # or you could just set verbosity=2 with manage.py...

    #############################################################
    #  test_authent_rfid* tests: RFID authentication
    #############################################################
    def test_authent_rfid(self):
        """ rfid associated with door, is active """
        response = self.client.get("/checkdoor/2/checkrfid/9999999992/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"1")

    def test_authent_rfid_door_does_not_exist(self):
        """ door does not exist  """
        response = self.client.get("/checkdoor/10/checkrfid/1123456789/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")

    def test_authent_rfid_does_not_exist(self):
        """ rfid does not exist """
        response = self.client.get("/checkdoor/2/checkrfid/9123456789/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")

    def test_authent_rfid__wrong_door(self):
        """ rfid not associated with door 2, is active """
        response = self.client.get("/checkdoor/2/checkrfid/1122135122/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")

    def test_authent_rfid_inactive_right_door(self):
        """ rfid was associated with door, but now inactive """
        response = self.client.get("/checkdoor/2/checkrfid/9999999991/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")

    def test_authent_rfid_wrong_format_in_url(self):
        """ rfid num in wrong format (i.e. url wrong format, so not found error) """
        response = self.client.get("/checkdoor/2/checkrfid/abc123/")
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.content,"")

    def test_authent_rfid_door_wrong_format_in_url(self):
        """ door id in wrong format (i.e. url wrong format, so not found error) """
        response = self.client.get("/checkdoor/aaaaa/checkrfid/1123456789/")
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.content,"")

    def test_authent_but_waiting_for_scan(self):
        """ Check: since the latest NewKeycardScan object is waiting_for_scan, 
        don't attempt to authenticate, just return 0/no; do not create an AccessTime 
        """
        # create NewKeycardScan object, making up the assigning user id
        # using assigner_user_id vs assigner_user only because we're using a fixture!
        nks_obj = NewKeycardScan.objects.create(assigner_user_id=1,waiting_for_scan=True)

        # how many AccessTime objects before request
        len_before = len(AccessTime.objects.all())

        response = self.client.get("/checkdoor/1/checkrfid/5555555555/")

        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,"0")

        # There should be the same number of AccessTime objects after the request
        len_after = len(AccessTime.objects.all())
        self.assertEqual(len_before,len_after)  

    #############################################################
    #  test_all_allowed* tests: get all allowed for a particular door
    #############################################################
    def test_all_allowed_non_existing_door(self):
        """ get all allowed rfids for door that does not exist """
        response = self.client.get("/door/10/getallowed/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,'{"doorid": 10, "allowed_rfids": ""}')

    def test_all_allowed_wrong_format(self):
        """ get all allowed rfids for door in wrong format (incorrect url) """
        response = self.client.get("/door/aaaa/getallowed/")
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.content,"")

    def test_all_allowed_existing_door(self):
        """ get all allowed rfids for existing door """
        response = self.client.get("/door/2/getallowed/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,'{"doorid": 2, "allowed_rfids": ["1122135199", "9999999992"]}')

    def test_all_allowed_inactive_not_allowed(self):
        """ list of allowed rfids does not contain any inactive ones """
        response = self.client.get("/door/3/getallowed/")
        self.assertEqual(response.status_code,200)
        allowed = simplejson.loads(response.content)['allowed_rfids']
        #self.assertTrue('9999999991' not in allowed) # should not contain the inactive rfid 9999999991
        self.assertNotIn('9999999991',allowed) # should not contain the inactive rfid 9999999991