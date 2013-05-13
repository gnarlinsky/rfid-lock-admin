import simplejson
from datetime import datetime, timedelta
from termcolor import colored
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import utc
from django.test import TestCase
from django.test.client import Client
from rfid_lock_management.misc_helpers import get_arg_default
from rfid_lock_management.models import RFIDkeycard, LockUser, Door, AccessTime, NewKeycardScan

class ChartDataTests(TestCase):
    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']
    
    def setUp(self):
        print colored("\nTestCase ChartDataTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") 
        self.client = Client()

    def test_chartify(self):
        """ Does chartify() return response with the correct(ly formatted) data for HighChart plot of access times? """
        # login as staff user in fixture
        self.client.login(username='moe',password='moe')
        response = self.client.get("/chart/") 
        response.context['chart_data']

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'text/html; charset=utf-8')

        # tooltip hardcoded in view as well
        tooltip = {   'followPointer': 'false', 'pointFormat': '"{point.user}"'}
        all_doors_series = []
        for door in Door.objects.all():
            # get the data points for this door
            at_this_door = AccessTime.objects.filter(door=door)
            data_points_values_list = at_this_door.values_list('data_point')
            data =   [simplejson.loads(dp[0]) for dp in data_points_values_list]
            # create door series
            door_series = { 'name':'"%s"' % door.name, 'data':data, 'tooltip':tooltip}
            # append to list of all door series
            all_doors_series.append(door_series)
        print colored("\tCheck response context for chart_type string","blue") # the one we're really interested in
        self.assertEqual(response.context['chart_data'], simplejson.dumps(all_doors_series,indent=""))

     
class NewKeycardScanTests(TestCase):
        #fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

        #######################################################################
        # test_initiate_new_keycard_scan* tests summary: 
        #######################################################################
        # url(r'start_scan/(?P<lockuser_object_id>\d+)/$',views.initiate_new_keycard_scan),
        # views.initiate_new_keycard_scan can return one of three HttpResponses: (HttpResponse(simplejson.dumps(response_data), content_type="application/json")): 
        #   response_data = {'success':True, 'new_scan_pk':n.pk}
        #       (lockuser with specified id does not already have an assigned keycard; a NewKeycardScan object must be created with n.waiting_for_scan = True and n.assigner_user = request.user)
        #   response_data = {'success':False, "error_mess":"WTF? There's no lock user?"}
        #       (lockuser with the specified id does not exist; a new NewKeycardScan object is not created))
        #   response_data = {'success':False, 'error_mess':"This lock user is already assigned a keycard! You shouldn't have even gotten this far!"} 
        #       (lockuser with specified id already has an assigned keycard; a new NewKeycardScan object is not created)
        #######################################################################

    def setUp(self):
        print colored("\nTestCase NewKeycardScanTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") # or you could just set verbosity=2 with maa nage.py...
        self.client = Client()

        print colored("Creating staff user doing this......","cyan")
        self.staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')

        print colored("logging in as staff user....","cyan")
        self.client.login(username='johnny_staff',password='my_password')

    def test_initiate_new_keycard_scan_but_no_lockuser(self):
        """  
        Lockuser with specified id does not exist: 
        - check for appropriate response 
        - and that a new NewKeycardScan object is not created 
        """
        print colored("\tThere's no LockUser with pk 1, right?", "blue")
        self.assertFalse(LockUser.objects.filter(pk=1))

        num_new_keycard_scan_obj_before = len(NewKeycardScan.objects.all())

        print colored("\tGetting response..........","cyan")
        response = self.client.get("/start_scan/1/")  # lockuser object id is 1

        # check that NewKeycardScan object has NOT been created (by comparing before and after NewKeycardScan objects count)
        print colored("\tCheck that a NewKeycardScan object has not been created","blue")
        num_new_keycard_scan_obj_after = len(NewKeycardScan.objects.all())
        self.assertEqual(num_new_keycard_scan_obj_before, num_new_keycard_scan_obj_after)

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'application/json')

        print colored("\tCheck response content","blue")
        self.assertFalse(simplejson.loads(response.content)['success'])
        self.assertEqual(simplejson.loads(response.content)['error_mess'],"This lock user was probably not found in the system.") 

    def test_initiate_new_keycard_scan_but_lockuser_has_keycard(self):
        """  Lockuser with specified id already has an assigned keycard: 
               check for appropriate response 
               and that a new NewKeycardScan object is not created """ 

        print colored("\tNo LockUsers at all, right?","blue")
        self.assertEqual(len(LockUser.objects.all()),0)

        print colored("\tCreating new lockuser..........","cyan")
        lu=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        print colored("\t...with pk 1","blue")
        self.assertEqual(lu.pk, 1)

        print colored("\tNow there should be one LockUser, the one we just made....","blue")
        self.assertEqual(LockUser.objects.all()[0], lu)
        print colored("\t...with pk 1","blue")
        self.assertEqual(LockUser.objects.all()[0].pk, 1)

        print colored("\tCreating new RFIDkeycard and assigning to our LockUser..........","cyan")
        rk = RFIDkeycard.objects.create(the_rfid="1111111111",lockuser=lu,assigner=self.staff_only_user)
        print colored("\tMake sure this LockUser already has a keycard", "blue")
        self.assertTrue(lu.is_active())   # or lu.get_current_rfid()...

        num_new_keycard_scan_obj_before = len(NewKeycardScan.objects.all())
        print colored("\tGetting response..........","cyan")
        response = self.client.get("/start_scan/1/")  # lockuser object id is 1

        # Parallels test_initiate_new_keycard_scan
        print colored("\tCheck that a NewKeycardScan object has not been created","blue")
        num_new_keycard_scan_obj_after = len(NewKeycardScan.objects.all())
        self.assertEqual(num_new_keycard_scan_obj_before, num_new_keycard_scan_obj_after)

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'application/json')

        print colored("\tCheck response content","blue")
        self.assertFalse(simplejson.loads(response.content)['success'])
        self.assertEqual(simplejson.loads(response.content)['error_mess'],"This lock user is already assigned a keycard.")

    def test_initiate_new_keycard_scan(self):
        """  
        Lockuser with specified id exists, does not have assigned keycard: 
        - check for appropriate response 
        - and that a new NewKeycardScan object is created, 
        - and it has correct attributes (waiting_for_scan = True; assigner_user = request.user) 
        """
        print colored("\tNo LockUsers at all, right?","blue")
        self.assertEqual(len(LockUser.objects.all()),0)
        print colored("\tCreating new lockuser..........","cyan")
        lu=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        print colored("\t...with pk 1","blue")
        self.assertEqual(lu.pk, 1)

        print colored("\tThere should be no NewKeycardScan objects to begin with","blue")
        self.assertFalse(NewKeycardScan.objects.all())

        print colored("\tGetting response..........","cyan")
        response = self.client.get("/start_scan/1/")  # lockuser object id is 1

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tThere should be a new NewKeycardScan object now...","blue")
        self.assertEqual(len(NewKeycardScan.objects.all()),1)
        print colored("\t...with pk 1","blue")
        new_nks_obj = NewKeycardScan.objects.all()[0]
        self.assertEqual(new_nks_obj.pk,1)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'application/json')

        print colored("\tCheck response content","blue")
        self.assertEqual(simplejson.loads(response.content)['success'], True)
        self.assertEqual(simplejson.loads(response.content)['new_scan_pk'], 1)

        print colored("\tCheck that NewKeycardScan object has correct attributes","blue")
        self.assertTrue(new_nks_obj.waiting_for_scan)
        self.assertEqual(new_nks_obj.assigner_user, self.staff_only_user)


    #######################################################################
    # test_finished_new_keycard_scan* tests summary
    #######################################################################
    # url(r'done_scan/(?P<new_scan_pk>\d+)/$',views.finished_new_keycard_scan),
    #######################################################################
    # views.finished__new_keycard_scan can return one of six HttpResponses: (HttpResponse(simplejson.dumps(response_data), content_type="application/json")): 
    #   response_data = {'success':True, 'rfid':new_scan.rfid}
    #   response_data = {'success':False, 'error_mess':"No NewKeycardScan objects at all"};
    #   response_data = {'success':False, 'error_mess':"No NewKeycardScan obj with pk " + new_scan_pk}
    #   response_data = {'success':False, 'error_mess':"NewKeycardScan does not have rfid"}
    #   response_data = {'success':False, 'error_mess':"A keycard with the same RFID is already assigned to %s." % k.lockuser} # to do
    #   response_data = {'success':False, 'error_mess':"Sorry, the system timed out. You have %d minutes to scan the card, then hit 'Done'
    #######################################################################

    # Issue #b (verifying model fields)
    def test_finished_new_keycard_scan(self):
        """ 
        Everything went ok (no active keycard with this RFID num already;
        a NewKeycardScan object with this pk does exist and has an RFID num; 
        not timed out), so can assign keycard. 
        """
        new_scan_pk = 1
        new_rfid = "9999999999"

        print colored("\tCreating new NewKeycardScan object we should have at this point..........","cyan")
        new_nks_obj = NewKeycardScan.objects.create(rfid=new_rfid,assigner_user_id=self.staff_only_user.pk)

        print colored("\tMake sure it has the pk from URL","blue")
        self.assertEqual(new_nks_obj.pk, new_scan_pk)

        print colored("\tGetting response..........","cyan")
        response = self.client.get("/done_scan/%d/" % new_scan_pk)  

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'application/json')

        print colored("\tCheck response content","blue")
        self.assertEqual(simplejson.loads(response.content)['success'],True)
        self.assertEqual(simplejson.loads(response.content)['rfid'], new_rfid)

        print colored("\tGetting the changed NewKeycardScan obj........","cyan")
        new_nks_obj = NewKeycardScan.objects.get(pk=1)

        print colored("\tCheck that NewKeycardScan object has correct attributes","blue")
        self.assertFalse(new_nks_obj.waiting_for_scan)
        self.assertTrue(new_nks_obj.ready_to_assign)

    def test_finished_new_keycard_scan_no_keycardscan_obj_with_pk(self):
        """ No NewKeycardScan object with the pk specified in the URL """
        new_scan_pk = 1

        print colored("\tCheck that there is no NewKeycardScan object with pk specified in the URL","blue")
        self.assertFalse(NewKeycardScan.objects.filter(pk=new_scan_pk))

        print colored("\tGetting response..........","cyan")
        response = self.client.get("/done_scan/%d/" % new_scan_pk)  

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'application/json')

        print colored("\tCheck response content","blue")
        self.assertEqual(simplejson.loads(response.content)['success'], False)
        self.assertEqual(simplejson.loads(response.content)['error_mess'], "No NewKeycardScan obj with pk %d." % new_scan_pk)

    def test_finished_new_keycard_scan_timed_out(self):
        """ Longer than x minutes to scan new card -- timed out """
        print colored("\tCreating new NewKeycardScan object; setting its creation time to 1 sec more than the time-out time.........","cyan")
        new_nks_obj = NewKeycardScan.objects.create(rfid="1111111111",assigner_user_id=self.staff_only_user.pk)
        
        # get the default minutes timeout by looking at the timeout default 
        # argument in timed_out method of NewKeycardScan.
        default_timeout_minutes = get_arg_default(NewKeycardScan.timed_out,'minutes')
        fake_time_initiated = (datetime.now() - timedelta(minutes=default_timeout_minutes, seconds=1)).replace(tzinfo=utc)
        new_nks_obj.time_initiated = fake_time_initiated
        new_nks_obj.save()

        print colored("\tGetting response..........","cyan")
        response = self.client.get("/done_scan/%d/" % new_nks_obj.pk)  

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'application/json')

        print colored("\tCheck response content","blue")
        self.assertEqual(simplejson.loads(response.content)['success'], False)
        self.assertEqual(simplejson.loads(response.content)['error_mess'], "Sorry, the system timed out. You have %d minutes to scan the card, then hit 'Done.' "  % default_timeout_minutes)

    def test_finished_new_keycard_scan_keycardscan_obj_does_not_have_rfid(self):
        """ NewKeycardScan object did not get an RFID num """
        print colored("\tCreating new NewKeycardScan object we should have at this point","cyan")
        new_nks_obj = NewKeycardScan.objects.create(assigner_user_id=self.staff_only_user.pk)

        print colored("\t...and it does not have an rfid","blue")
        self.assertFalse(new_nks_obj.rfid)
        response = self.client.get("/done_scan/%d/" % new_nks_obj.pk)  

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'application/json')

        print colored("\tCheck response content","blue")
        self.assertEqual(simplejson.loads(response.content)['success'], False)
        self.assertEqual(simplejson.loads(response.content)['error_mess'], "NewKeycardScan does not have RFID.")

    def test_finished_new_keycard_scan_keycard_with_same_rfid_exists(self):
        """ A keycard with the same RFID is already assigned to another lockuser """
        # create the RFIDkeycard whose rfid is the same as the one trying to assign;
        # create the lockuser with that rfid 
        print colored("\tCreating new lockuser..........","cyan")
        lu=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')

        duplicate_rfid = "1111111111"  # we're attempting to assign this one, but it already belongs to an active lock user
        new_scan_pk = 1

        print colored("\tCreating new RFIDkeycard and assigning to our LockUser..........","cyan")
        rk = RFIDkeycard.objects.create(the_rfid=duplicate_rfid,lockuser=lu,assigner=self.staff_only_user)

        print colored("\tMake sure this LockUser has this keycard", "blue")
        self.assertTrue(lu.is_active())   # or lu.get_current_rfid()...

        print colored("\tCreating new NewKeycardScan object we should have at this point..........","cyan")
        new_nks_obj = NewKeycardScan.objects.create(rfid=duplicate_rfid,assigner_user_id=self.staff_only_user.pk)

        print colored("\tCheck that the NewKeycardScan object with pk specified in the URL has the duplicate rfid","blue")
        # todo:  or is this actually covered in NewKeycardScan model tests? 
        self.assertTrue(NewKeycardScan.objects.filter(pk=new_scan_pk,rfid=duplicate_rfid))

        print colored("\tGetting response..........","cyan")
        response = self.client.get("/done_scan/%d/" % new_nks_obj.pk)  

        print colored("\tCheck response status code","blue")
        self.assertEqual(response.status_code, 200)

        print colored("\tCheck response content type","blue")
        self.assertEqual(response['content-type'],'application/json')

        print colored("\tCheck response content","blue")
        self.assertEqual(simplejson.loads(response.content)['success'], False)
        self.assertEqual(simplejson.loads(response.content)['error_mess'], "A keycard with the same RFID is already assigned to %s." % lu)
