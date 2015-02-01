import simplejson

from django.test import TestCase
from django.test.client import Client
from rfid_lock_management.models import NewKeycardScan, AccessTime
from test_helpers import t_info


class LockCommunicationTests(TestCase):
    fixtures = ['initial.json']

    def setUp(self):
        self.client = Client()
        t_info("TestCase LockCommunicationTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)

    #
    #  test_authent_rfid* tests: RFID authentication
    #
    def test_authent_rfid(self):
        """ RFID associated with door, is active """
        response = self.client.get("/checkdoor/2/checkrfid/9999999992/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "1")

    def test_authent_rfid_door_does_not_exist(self):
        """ Door does not exist  """
        response = self.client.get("/checkdoor/10/checkrfid/1123456789/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "0")

    def test_authent_rfid_does_not_exist(self):
        """ RFID does not exist """
        response = self.client.get("/checkdoor/2/checkrfid/9123456789/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "0")

    def test_authent_rfid__wrong_door(self):
        """ RFID not associated with door 2, is active """
        response = self.client.get("/checkdoor/2/checkrfid/1122135122/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "0")

    def test_authent_rfid_inactive_right_door(self):
        """ RFID was associated with door, but now inactive """
        response = self.client.get("/checkdoor/2/checkrfid/9999999991/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "0")

    def test_authent_rfid_wrong_format_in_url(self):
        """
        RFID is in wrong format (i.e. url wrong format, so not found error)
        """
        response = self.client.get("/checkdoor/2/checkrfid/abc123/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, "")

    def test_authent_rfid_door_wrong_format_in_url(self):
        """ Door id in wrong format (i.e. URL is in the wrong format,
        so not found error)
        """
        response = self.client.get("/checkdoor/aaaaa/checkrfid/1123456789/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, "")

    def test_authent_but_waiting_for_scan(self):
        """ Check: since the latest NewKeycardScan object is waiting_for_scan,
        don't attempt to authenticate, just return 0; do not create an AccessTime
        """
        # create NewKeycardScan object, making up the assigning user id
        # using assigner_user_id vs assigner_user only because we're using a
        # fixture!
        nks_obj = NewKeycardScan.objects.create(
            assigner_user_id=1, waiting_for_scan=True)

        # how many AccessTime objects before request
        len_before = len(AccessTime.objects.all())

        response = self.client.get("/checkdoor/1/checkrfid/5555555555/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "0")

        # There should be the same number of AccessTime objects after the
        # request
        len_after = len(AccessTime.objects.all())
        self.assertEqual(len_before, len_after)

    #
    #  test_all_allowed* tests: get all allowed for a particular door
    #
    def test_all_allowed_non_existing_door(self):
        """ get all allowed RFIDs for door that does not exist """
        response = self.client.get("/door/10/getallowed/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '\0')
            #'{"doorid": 10, "allowed_rfids": ""}')

    def test_all_allowed_wrong_format(self):
        """ get all allowed RFIDs for door in wrong format (incorrect url) """
        response = self.client.get("/door/aaaa/getallowed/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, "")

    def test_get_allowed_rfids_has_null_terminator(self):
        """ Does get_allowed_rfids() return a rfids separated by spaces, with a
        null terminator?  """
        # TODO: not the most elegant test...
        response = self.client.get('/door/1/getallowed/')

        # verify there is a null terminator at the end of the response string
        actual_rfids = response.content
        self.assertEqual('\0', actual_rfids[-1:])

    def test_all_allowed_existing_door(self):
        """ get all allowed RFIDs for existing door """
        response = self.client.get('/door/1/getallowed/')
        self.assertEqual(response.status_code, 200)

        # grab the rfids from actual, removing the null terminator
        actual_rfids = response.content
        actual_rfids = actual_rfids[:-1]
        actual_rfids_sorted_list = sorted(actual_rfids.split())
        actual_rfids_as_string = ' '.join(actual_rfids_sorted_list)

        # both actual and expected should be sorted so we can compare them
        self.assertEqual('1122135122 1122135199',
                         actual_rfids_as_string)
        #self.assertEqual(response.content,
        #    '{"doorid": 2, "allowed_rfids": ["1122135199", "9999999992"]}')

    def test_all_allowed_inactive_not_allowed(self):
        """ list of allowed RFIDs does not contain any inactive ones """
        response = self.client.get("/door/3/getallowed/")
        self.assertEqual(response.status_code, 200)
        #allowed = simplejson.loads(response.content)['allowed_rfids']
        # should not contain the inactive RFID 9999999991
        # remove null terminator
        self.assertNotIn('9999999991', response.content[-1:])
