from datetime import datetime, timedelta
import simplejson
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
#from django.utils.timezone import utc
from django.test import TestCase
from django.test.client import Client
from rfid_lock_management.models import *
from test_helpers import t_info

class ChartDataTests(TestCase):
    fixtures = ['initial.json']

    def setUp(self):
        t_info("TestCase ChartDataTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)
        self.client = Client()

    def test_chartify(self):
        """
        Does chartify() return response with the correct(ly formatted) data
        for HighChart plot of access times?
        """
        # login as staff user in fixture
        self.client.login(username='moe', password='moe')
        response = self.client.get("/chart/")
        #response.context['chart_data']

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'text/html; charset=utf-8')

        # tooltip hardcoded in view as well
        tooltip = {'followPointer': 'false', 'pointFormat': '"{point.user}"'}
        all_doors_series = []
        for door in Door.objects.all():
            # get the data points for this door
            at_this_door = AccessTime.objects.filter(door=door)
            data_points_values_list = at_this_door.values_list('data_point')
            data = [simplejson.loads(dp[0]) for dp in data_points_values_list]
            # create door series
            door_series = {'name': '"%s"' % door.name,
                           'data': data,
                           'tooltip': tooltip}
            # append to list of all door series
            all_doors_series.append(door_series)

        t_info("Check response context for chart_type string", 4)
        # the one we're really interested in
        self.assertEqual(response.context['chart_data'],
            simplejson.dumps(all_doors_series, indent=""))


class NewKeycardScanTests(TestCase):
    def setUp(self):
        t_info("TestCase NewKeycardScanTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)
        self.client = Client()

        t_info("Creating staff user doing this......", 3)
        self.staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')

        t_info("logging in as staff user....", 3)
        self.client.login(username='johnny_staff', password='my_password')

    def test_initiate_new_keycard_scan_but_no_lockuser(self):
        """
        Lockuser with specified id does not exist:
        - check for appropriate response
        - and that a new NewKeycardScan object is not created
        """
        t_info("There's no LockUser with pk 1, right?", 4)
        self.assertFalse(LockUser.objects.filter(pk=1))

        num_new_keycard_scan_obj_before = len(NewKeycardScan.objects.all())

        t_info("Getting response..........", 3)
        response = self.client.get("/start_scan/1/")  # lockuser object id is 1

        # check that NewKeycardScan object has NOT been created (by comparing
        # before and after NewKeycardScan objects count)
        t_info("Check that a NewKeycardScan object has not been created", 4)
        num_new_keycard_scan_obj_after = len(NewKeycardScan.objects.all())
        self.assertEqual(num_new_keycard_scan_obj_before,
            num_new_keycard_scan_obj_after)

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'application/json')

        t_info("Check response content", 4)
        self.assertFalse(simplejson.loads(response.content)['success'])
        self.assertEqual(simplejson.loads(response.content)['error_mess'],
            "This lock user was probably not found in the system.")

    def test_initiate_new_keycard_scan_but_lockuser_has_keycard(self):
        """
        Lockuser with specified id already has an assigned keycard: check for
        appropriate response and that a new NewKeycardScan object is not
        created
        """
        t_info("No LockUsers at all, right?", 4)
        self.assertEqual(len(LockUser.objects.all()), 0)

        t_info("Creating new lockuser..........", 3)
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')

        t_info("...with pk 1", 4)
        self.assertEqual(lu.pk, 1)

        t_info("Now there should be one LockUser, the one we just"
                " made....", 4)
        self.assertEqual(LockUser.objects.all()[0], lu)

        t_info("...with pk 1", 4)
        self.assertEqual(LockUser.objects.all()[0].pk, 1)

        t_info("Creating new RFIDkeycard and assigning to our "
                "LockUser..........", 3)
        rk = RFIDkeycard.objects.create(
            the_rfid="1111111111", lockuser=lu, assigner=self.staff_only_user)

        t_info("Make sure this LockUser already has a keycard", 4)
        self.assertTrue(lu.is_active())   # or lu.get_current_rfid()...

        num_new_keycard_scan_obj_before = len(NewKeycardScan.objects.all())

        t_info("Getting response..........", 3)
        response = self.client.get("/start_scan/1/")  # lockuser object id is 1

        # Parallels test_initiate_new_keycard_scan
        t_info("Check that a NewKeycardScan object has not been "
                "created", 4)
        num_new_keycard_scan_obj_after = len(NewKeycardScan.objects.all())
        self.assertEqual(num_new_keycard_scan_obj_before,
            num_new_keycard_scan_obj_after)

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'application/json')

        t_info("Check response content", 4)
        self.assertFalse(simplejson.loads(response.content)['success'])
        self.assertEqual(simplejson.loads(response.content)['error_mess'],
            "This lock user is already assigned a keycard.")

    def test_initiate_new_keycard_scan(self):
        """
        Lockuser with specified id exists, does not have assigned keycard:
        - check for appropriate response
        - and that a new NewKeycardScan object is created,
        - and it has correct attributes (waiting_for_scan = True;
          assigner_user = request.user)
        """
        t_info("No LockUsers at all, right?", 4)
        self.assertEqual(len(LockUser.objects.all()), 0)
        t_info("Creating new lockuser..........", 3)
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        t_info("...with pk 1", 4)
        self.assertEqual(lu.pk, 1)

        t_info("There should be no NewKeycardScan objects to begin with", 4)
        self.assertFalse(NewKeycardScan.objects.all())

        t_info("Getting response..........", 3)
        response = self.client.get("/start_scan/1/")  # lockuser object id is 1

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("There should be a new NewKeycardScan object now...", 4)
        self.assertEqual(len(NewKeycardScan.objects.all()), 1)

        t_info("...with pk 1", 4)
        new_nks_obj = NewKeycardScan.objects.all()[0]
        self.assertEqual(new_nks_obj.pk, 1)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'application/json')

        t_info("Check response content", 4)
        self.assertEqual(simplejson.loads(response.content)['success'], True)
        self.assertEqual(simplejson.loads(response.content)['new_scan_pk'], 1)

        t_info("Check that NewKeycardScan object has correct attributes", 4)
        self.assertTrue(new_nks_obj.waiting_for_scan)
        self.assertEqual(new_nks_obj.assigner_user, self.staff_only_user)


    ################################################
    # test_finished_new_keycard_scan* tests summary
    ################################################
    # views.finished__new_keycard_scan can return one of six HttpResponses:
    #   response_data = {'success':True, 'rfid':new_scan.rfid}
    #   response_data = {'success':False, 
    #                    'error_mess':"No NewKeycardScan objects at all"};
    #   response_data = {'success':False,
    #                    'error_mess':"No NewKeycardScan obj with pk %d" %
    #                    new_scan_pk}
    #   response_data = {'success':False,
    #                    'error_mess':"NewKeycardScan does not have rfid"}
    #   response_data = {'success':False,
    #                    'error_mess':"A keycard with the same RFID is already"
    #                       " assigned to %s." % k.lockuser}
    #   response_data = {'success':False,
    #                    'error_mess':"Sorry, the system timed out. You have "
    #                       " %d minutes to scan the card, then hit 'Done'
    #
    # Issue #b (verifying model fields)
    def test_finished_new_keycard_scan(self):
        """
        Everything went ok (no active keycard with this RFID num already;
        a NewKeycardScan object with this pk does exist and has an RFID num;
        not timed out), so can assign keycard.
        """
        new_scan_pk = 1
        new_rfid = "9999999999"

        t_info("Creating new NewKeycardScan object we should have"
                          "at this point..........", 3)
        new_nks_obj = NewKeycardScan.objects.create(
            rfid=new_rfid, assigner_user_id=self.staff_only_user.pk)

        t_info("Make sure it has the pk from URL", 4)
        self.assertEqual(new_nks_obj.pk, new_scan_pk)

        t_info("Getting response..........", 3)
        response = self.client.get("/done_scan/%d/" % new_scan_pk)

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'application/json')

        t_info("Check response content", 4)
        self.assertEqual(simplejson.loads(response.content)['success'], True)
        self.assertEqual(simplejson.loads(response.content)['rfid'], new_rfid)

        t_info("Getting the changed NewKeycardScan obj........", 3)
        new_nks_obj = NewKeycardScan.objects.get(pk=1)

        t_info("Check that NewKeycardScan object has correct attributes", 4)
        self.assertFalse(new_nks_obj.waiting_for_scan)
        self.assertTrue(new_nks_obj.ready_to_assign)

    def test_finished_new_keycard_scan_no_keycardscan_obj_with_pk(self):
        """ No NewKeycardScan object with the pk specified in the URL """
        new_scan_pk = 1

        t_info("Check that there is no NewKeycardScan object with "
            "pk specified in the URL", 4)
        self.assertFalse(NewKeycardScan.objects.filter(pk=new_scan_pk))

        t_info("Getting response..........", 3)
        response = self.client.get("/done_scan/%d/" % new_scan_pk)

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'application/json')

        t_info("Check response content", 4)
        self.assertEqual(simplejson.loads(response.content)['success'], False)
        self.assertEqual(simplejson.loads(response.content)['error_mess'],
            "No NewKeycardScan obj with pk %d." % new_scan_pk)

    def test_finished_new_keycard_scan_timed_out(self):
        """ Longer than x minutes to scan new card -- timed out """
        t_info("Creating NewKeycardScan object; setting creation "
        "time to 1 sec more than the time-out time......", 3)
        new_nks_obj = NewKeycardScan.objects.create(
            rfid="1111111111", assigner_user_id=self.staff_only_user.pk)
        min_till_timeout = 2.0
        time_delta = timedelta(minutes=min_till_timeout, seconds=1)
        fake_time_initiated = (datetime.datetime.now() - time_delta)
        new_nks_obj.time_initiated = fake_time_initiated
        new_nks_obj.save()

        t_info("Getting response..........", 3)
        response = self.client.get("/done_scan/%d/" % new_nks_obj.pk)

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'application/json')

        t_info("Check response content", 4)
        self.assertEqual(simplejson.loads(response.content)['success'], False)
        # self.assertEqual(simplejson.loads(response.content)['error_mess'],
        # "Sorry, the system timed out. You have %d minutes to scan the card,
        # then hit 'Done.' "  % default_timeout_minutes)
        self.assertEqual(simplejson.loads(response.content)['error_mess'],
            "Sorry, the system timed out. You have {} minutes to scan the card, "
            "then hit 'Done.' ".format(min_till_timeout))

    def test_finished_new_keycard_scan_obj_does_not_have_rfid(self):
        """ NewKeycardScan object did not get an RFID num """
        t_info("Creating new NewKeycardScan object we should have at this point", 3)
        new_nks_obj = NewKeycardScan.objects.create(
            assigner_user_id=self.staff_only_user.pk)

        t_info("...and it does not have an rfid", 4)
        self.assertFalse(new_nks_obj.rfid)
        response = self.client.get("/done_scan/%d/" % new_nks_obj.pk)

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'application/json')

        t_info("Check response content", 4)
        self.assertEqual(simplejson.loads(response.content)['success'], False)
        self.assertEqual(simplejson.loads(response.content)['error_mess'],
            "NewKeycardScan does not have RFID.")

    def test_finished_new_keycard_scan_keycard_with_same_rfid_exists(self):
        """
        A keycard with the same RFID is already assigned to another
        lockuser
        """
        # create the RFIDkeycard whose rfid is the same as the one trying to
        # assign; create the lockuser with that rfid
        t_info("Creating new lockuser..........", 3)
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')

        # attempting to assign this one, but it already belongs to an active lock user
        duplicate_rfid = "1111111111"
        new_scan_pk = 1

        t_info("Creating new RFIDkeycard and assigning to our "
                "LockUser..........", 3)
        rk = RFIDkeycard.objects.create(
            the_rfid=duplicate_rfid, lockuser=lu, assigner=self.staff_only_user)

        t_info("Make sure this LockUser has this keycard", 4)
        self.assertTrue(lu.is_active())   # or lu.get_current_rfid()...

        t_info("Creating new NewKeycardScan object we should have "
                "at this point..........", 3)
        new_nks_obj = NewKeycardScan.objects.create(
            rfid=duplicate_rfid, assigner_user_id=self.staff_only_user.pk)

        t_info("Check that the NewKeycardScan object with pk "
                "specified in the URL has the duplicate rfid", 4)
        # todo:  or is this actually covered in NewKeycardScan model tests?
        self.assertTrue(NewKeycardScan.objects.filter(pk=new_scan_pk,
            rfid=duplicate_rfid))

        t_info("Getting response..........", 3)
        response = self.client.get("/done_scan/%d/" % new_nks_obj.pk)

        t_info("Check response status code", 4)
        self.assertEqual(response.status_code, 200)

        t_info("Check response content type", 4)
        self.assertEqual(response['content-type'], 'application/json')

        t_info("Check response content", 4)
        self.assertEqual(simplejson.loads(response.content)['success'], False)
        self.assertEqual(simplejson.loads(response.content)['error_mess'],
            "A keycard with the same RFID is already assigned to %s." % lu)
