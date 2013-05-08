from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from rfid_lock_management.models import RFIDkeycard, LockUser, Door, AccessTime, NewKeycardScan
from termcolor import colored
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta
from django.utils.timezone import utc


"""
# to run only some tests: 
#   $ ./manage.py test rfid_lock_management.LockUserModelTest

#######################################################################################
# TO DO: 
#######################################################################################
#  Note - update relevant to various test to-do's: getting rid of the concept of lockuser deactivation
#######################################################################################
# - Separate functional tests and unit tests into separate .py's? 
# - check if rfid not exactly 10 digits long and reject right away
# - If some aspect of an object is updated, does that change cascade through... 
# - on writing use cases: http://breathingtech.com/2009/writing-use-cases-for-agile-scrum-projects/
#
# - what happens when you have a lockuser with a specific door perm, but you delete the door? 
# - what happens to an rfidkeycard when its active or not active lockuser has been deleted? 
#
# - RFIDkeycard: if date_revoked is not None, deactivate field should be False; otherwise, deactivate
# should be True
#
# - Deactivating a LockUser:  should deactivate LockUser's RFIDkeycard
# - Deactivating RFIDkeycard: should NOT deactivate its LockUser
#
# ----------------------------------------
#  post fk/m2m change: 
# ----------------------------------------
# - can't add a lockuser that already has an active keycard
# - can't add a lockuser/create a lockuser with no door permissions. 
#
# - After deactivating keycard from LockUser's change_form, do we come back to the change_form?
#
# - In the inline form for RFIDkeycards (on LockUser change_form):
#       - show date_created (along with some other fields?) only on
#       existing keycards, not at creation time.
#       - never show date_revoked and certain other fields to staff users
#
# ----------------------------------------
# stuff having to do with overriding save()'s
# ----------------------------------------
# - When assign new keycard, if the LockUser was inactive before, they will automatically become active.
# - If the Lockuser has been deactivated, its current keycard should be deactivated as well.
# - We'll deactivate a LockUser's current keycard here, if deactivate_current_keycard is checked
#   on the LockUser's change_form. 

"""



#######################################################################################
#  Unit tests
#######################################################################################
class DoorModelTests(TestCase):
    #fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

    def setUp(self):
        print colored("\nTestCase DoorModelTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") # or you could just set verbosity=2 with maa nage.py...
    
    def test_unicode(self):
        """ Test that custom __unicode__() method returns name of Door """
        door = Door.objects.create(name='Test door')
        self.assertEqual(unicode(door), 'Test door')

    def test_door_perm_creation(self):
        """ When a new Door is added, create a corresponding Permission (i.e. checking Door's save() method)  """
        door_name = "Test door"
        door = Door(name=door_name)
        door.save()   # explicitly save()'ing (at least for code clarity) rather than Door.objects.create()

        # now check that both door and associated permission exist
        d = Door.objects.filter(name=door_name)
        self.assertTrue(d)

        # note: door_name, not door.name
        p = Permission.objects.filter(codename='can_manage_door_%d' % door.pk, \
                name='Can manage door to %s' % door_name, \
                content_type = ContentType.objects.get(app_label='rfid_lock_management',model='door') )
        self.assertTrue(p)


class AccessTimeModelTests(TestCase):

    def setUp(self):
        print colored("\nTestCase AccessTimeModelTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") # or you could just set verbosity=2 with maa nage.py...

    def test_unicode(self):
        """ Test that custom __unicode__() returns the correctly formatted time """
        time = datetime(2013, 5, 16, 15, 30, 20).replace(tzinfo=utc)
        at = AccessTime.objects.create(access_time=time)
        self.assertEqual(unicode(at), 'May 16, 2013, 03:30 PM')
        # todo:  or test with variables? time.strftime("%B %d, %Y, %I:%M %p") ?


    def test_get_this_lockuser_html(self):
        """ Create AccessTime with specific lockuser; make sure get_this_lockuser_html returns the correct html """
        #lu = LockUser(first_name="Jane", last_name="Doe", email="jdoe@jmail.com")
        #lu.save()
        #at = AccessTime(lockuser=lu)
        #at.save()
        # create(); A convenience method for creating an object and saving it all in one step. 
        lu = LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        at = AccessTime.objects.create(lockuser=lu)
        
        self.assertEqual(at.get_this_lockuser_html(), "<a href='../lockuser/%d/'>%s</a>" % (lu.pk, lu))


class NewKeycardScanModelTests(TestCase):
    def setUp(self):
        print colored("\nTestCase NewKeycardScanModelTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "cyan") 
        # or you could just set verbosity=2 with manage.py...

    def TearDown(self):
        pass

class RFIDkeycardModelTests(TestCase):
    def setUp(self):
        print colored("\nTestCase RFIDkeycardModelTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "cyan") # or you could just set verbosity=2 with manage.py...

    def TearDown(self):
        pass
    
    def test_unicode(self):
        """ Test that custom __unicode__() method returns the rfid num (well, string) """
        # assign lockuser, so can create RFIDkeycard (lockuser is required; also assigner User required)
        lu = LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(the_rfid='abcde12345',lockuser=lu, assigner=staff_only_user)
        self.assertEqual(unicode(rk),'abcde12345')

    def test_get_allowed_doors(self):
        """ Does get_allowed_doors() return the door(s), if any, that the associated lockuser is allowed to access """
        # create the LockUser and Doors
        door1 = Door.objects.create(name='Allowed door')
        door2 = Door.objects.create(name='Prohibited door')
        lu = LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(the_rfid='abcde12345',lockuser=lu, assigner=staff_only_user)


        # only one door allowed
        lu.doors = [door1]
        self.assertEqual(list(rk.get_allowed_doors()),[door1])
        # todo:  here and elsewhere, consider using assertQuerysetEqual() -- see http://stackoverflow.com/a/14189017

        # no doors allowed
        lu.doors = []
        self.assertEqual(list(rk.get_allowed_doors()),[])


    def test_deactivate(self):
        """ On deactivation, is RFIDkeycard object's date revoked and revoker set correctly? """
        # create keycard and associated lockuser
        lu = LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        #print colored("\tCreating staff user doing this......","cyan")
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(the_rfid='abcde12345',lockuser=lu, assigner=staff_only_user)

        # need logged in user so we can assign the revoker
        self.client = Client()
        #print colored("\tLogging in as staff user....","cyan")
        self.client.login(username='johnny_staff',password='my_password')

        

        # comparing times... is there a way to account for lag between, for ex., setting the now variable and executing the surrounding statements... like some kind of approximation? self.assertAlmostEquals? But how much to round/delta?   (todo)....  doing this: 
        # get the time at t1
        # RFIDkeycard.deactivate() at time t2=t1+x
        # assert for RFIDkeycard.date_revoked at time t3=t1+x+y
        # So deactivation happened AT MOST x+y microseconds ago, at time of assertion
        # from docs: assertAlmostEqual(first, second, places=7, msg=None, delta=None) --
        #   'If delta is supplied instead of places then the difference between 
        #   first and second must be less ... than delta.'
        # So, setting delta to the time difference between t1 and t3, or x+y 
        #   -- i.e. now() minus t1


        t1 = datetime.now().replace(tzinfo=utc)

        print colored("\tDeactivating keycard......","cyan")
        rk.deactivate(staff_only_user)

        print colored("\tIs the date revoked correct","blue")
        self.assertAlmostEqual(rk.date_revoked, datetime.now().replace(tzinfo=utc), delta = datetime.now().replace(tzinfo=utc) - t1)


        print colored("\tIs the revoker our user","blue")
        self.assertEqual(rk.revoker, staff_only_user)

        

    def test_is_active(self):
        """ """
        # create keycard and associated lockuser
        lu = LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(the_rfid='abcde12345',lockuser=lu, assigner=staff_only_user)

        # should be active after just created
        self.assertTrue(rk.is_active())

        # set fake date revoked
        now = datetime.now().replace(tzinfo=utc)
        rk.date_revoked = now

        self.assertFalse(rk.is_active())

        
        



class LockUserModelTests(TestCase):
    # here won't be using Selenium; interacting with application at a lower level


    def setUp(self):
        print colored("\nTestCase LockUserModelTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "cyan") # or you could just set verbosity=2 with maa nage.py...

    def TearDown(self):
        pass

    # todo: separate unit tests.......
    def test_creating_new_obj_and_saving_it_to_db(self):
        """ Create new LockUser, set attributes, save to database """

        print colored("\tCan we create new LockUser; set attributes; save it?","blue")
        lockuser = LockUser()
        lockuser.first_name = "Homer"
        lockuser.last_name = "Simpson"
        lockuser.email =  "chunkylover53@aol.com"
        lockuser.address = "742 Evergreen Terrace, Springfield, USA"
        lockuser.phone_number = "(939) 555-5555"   

        lockuser.save()  # i.e., INSERT

        print colored("\tCan we find it in the database again?","blue")
        all_lockusers_in_db = LockUser.objects.all()
        self.assertEqual(len(all_lockusers_in_db),1)
        the_only_lockuser_in_db = all_lockusers_in_db[0]
        self.assertEqual(the_only_lockuser_in_db, lockuser)

        print colored("\tWere the attributes saved?","blue")
        self.assertEqual(the_only_lockuser_in_db.first_name,"Homer")
        self.assertEqual(the_only_lockuser_in_db.last_name,"Simpson")
        self.assertEqual(the_only_lockuser_in_db.email,"chunkylover53@aol.com")
        self.assertEqual(the_only_lockuser_in_db.address,"742 Evergreen Terrace, Springfield, USA")
        self.assertEqual(the_only_lockuser_in_db.phone_number,"(939) 555-5555")
# TO DO: same as above for the other models

    def test_unicode(self):
        """ Test that custom __unicode__() -- i.e. just obj_name -- returns first and last name of lockuser """
        lu = LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        self.assertEqual(unicode(lu), 'Jane Doe')


    def test_is_active(self):
        """ Check if is_active() reflects whether the user is assigned a keycard """
        lu=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        self.assertFalse(lu.is_active())

        # now assigning a keycard
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(the_rfid='abcde12345',lockuser=lu, assigner=staff_only_user)
        self.assertTrue(lu.is_active())

    def test_get_allowed_doors(self):
        """ Does get_allowed_doors() return the door(s), if any, that the lockuser is allowed to access """
        # create the LockUser and Doors and associated/'supporting' objects
        door1 = Door.objects.create(name='Allowed door')
        door2 = Door.objects.create(name='Prohibited door')
        lu = LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(the_rfid='abcde12345',lockuser=lu, assigner=staff_only_user)


        # only one door allowed
        lu.doors = [door1]
        self.assertEqual(list(lu.get_allowed_doors()),[door1])

        # no doors allowed
        lu.doors = []
        self.assertEqual(list(lu.get_allowed_doors()),[])


    def test_get_all_rfids(self):
        """ Does get_all_rfids() returns all RFIDkeycards objects associated with Lockuser """


        lu1=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        lu2=LockUser.objects.create(first_name='John',last_name='Doe',email='jdoe2@gmail.com')
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        # Of these four RFIDkeycards, three are assigned to the LockUser will be testing this with, meaning that three should be in the returned list
        rk1 = RFIDkeycard.objects.create(the_rfid='abcde11111', lockuser=lu1, assigner=staff_only_user)
        rk2 = RFIDkeycard.objects.create(the_rfid='abcde22222', lockuser=lu2, assigner=staff_only_user)
        rk3 = RFIDkeycard.objects.create(the_rfid='abcde33333', lockuser=lu2, assigner=staff_only_user, date_revoked=datetime.now().replace(tzinfo=utc))
        rk4 = RFIDkeycard.objects.create(the_rfid='abcde44444', lockuser=lu2, assigner=staff_only_user, date_revoked=datetime.now().replace(tzinfo=utc))

        # note - below does not evaluate these as equivalent, must list()
        #self.assertEqual(lu2.get_all_rfids(), RFIDkeycard.objects.filter(pk__in=[rk2.pk,rk3.pk,rk4.pk]))
        self.assertEqual(list(lu2.get_all_rfids()), [rk2,rk3,rk4])

    def test_get_all_rfids_html(self):
        """ Check that method returns the correctly formatted html string of all rfids, NOT including the current one """
        # Of these four RFIDkeycards, three are assigned to the LockUser will be testing this with, and one of those is the LockUser's current keycard, meaning that there should only be two in the returned list

        lu1=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        lu2=LockUser.objects.create(first_name='John',last_name='Doe',email='jdoe2@gmail.com')
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk1 = RFIDkeycard.objects.create(the_rfid='abcde11111', lockuser=lu1, assigner=staff_only_user)
        rk2 = RFIDkeycard.objects.create(the_rfid='abcde22222', lockuser=lu2, assigner=staff_only_user)
        rk3 = RFIDkeycard.objects.create(the_rfid='abcde33333', lockuser=lu2, assigner=staff_only_user, date_revoked=datetime.now().replace(tzinfo=utc))
        rk4 = RFIDkeycard.objects.create(the_rfid='abcde44444', lockuser=lu2, assigner=staff_only_user, date_revoked=datetime.now().replace(tzinfo=utc))

        # to do:  see email with questions concerning unit testing stuff/minimum 'units', etc. (i.e. using get_all_rfids() here vs building 'from scratch,' as below: 

        # string should look like:
        # "RFID : %s (activated on %s by %s; revoked on %s by %s)" % (rf,date_assigned, assigner,date_revoked, revoker)
        correct_output_string = \
            "RFID: %s (activated on %s by %s; revoked on %s by %s),<br>" % \
                    (rk3.the_rfid,rk3.date_created.strftime("%B %d, %Y, %I:%M %p"), rk3.assigner,rk3.date_revoked.strftime("%B %d, %Y, %I:%M %p"), rk3.revoker) \
            + "RFID: %s (activated on %s by %s; revoked on %s by %s)" % \
                    (rk4.the_rfid,rk4.date_created.strftime("%B %d, %Y, %I:%M %p"), rk4.assigner,rk4.date_revoked.strftime("%B %d, %Y, %I:%M %p"), rk4.revoker)

        self.assertEqual(lu2.get_all_rfids_html(),correct_output_string)
        # note - the try/except in get_all_rfids_html is really only there because during development it was possible to have a non-current keycard with no date_revoked and no revoker.. So no unit test for that, but something to note for test coverage. 


    def test_get_current_rfid(self):
        """ """
        # Of these four RFIDkeycards, three are assigned to the LockUser will be testing this with, and one of those is the LockUser's current keycard
        lu1=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        lu2=LockUser.objects.create(first_name='John',last_name='Doe',email='jdoe2@gmail.com')
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk1 = RFIDkeycard.objects.create(the_rfid='abcde11111', lockuser=lu1, assigner=staff_only_user)
        rk2 = RFIDkeycard.objects.create(the_rfid='abcde22222', lockuser=lu2, assigner=staff_only_user)
        rk3 = RFIDkeycard.objects.create(the_rfid='abcde33333', lockuser=lu2, assigner=staff_only_user, date_revoked=datetime.now().replace(tzinfo=utc))
        rk4 = RFIDkeycard.objects.create(the_rfid='abcde44444', lockuser=lu2, assigner=staff_only_user, date_revoked=datetime.now().replace(tzinfo=utc))

        self.assertEqual(lu2.get_current_rfid(), rk2) 


    ############################################################
    # to do - pending answering the questions in email
    ############################################################

    def test_prettify_get_current_rfid(self):
        """ """
        lu=LockUser.objects.create(first_name='John',last_name='Doe',email='jdoe2@gmail.com')
        self.assertEqual(lu.prettify_get_current_rfid(), None)
        
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        curr_rfid = RFIDkeycard.objects.create(the_rfid='abcde22222', lockuser=lu, assigner=staff_only_user)
        correct_return_string = "RFID: %s (activated on %s by %s)" % (curr_rfid.the_rfid, curr_rfid.date_created.strftime("%B %d, %Y, %I:%M %p"), curr_rfid.assigner)
        self.assertEqual(lu.prettify_get_current_rfid(), correct_return_string)


    def test_prettify_get_allowed_doors_html_links(self):
        """ """
        door1 = Door.objects.create(name='Space 1')
        door2 = Door.objects.create(name='Space 2')
        door3 = Door.objects.create(name='Space 3')
        lu=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        lu.doors=[door1, door2]
        lu.save()

        correct_return_string = "<a href='../door/%d/'>%s</a>, <a href='../door/%d/'>%s</a>" \
                            %  (door1.pk, door1.name, door2.pk, door2.name)
        self.assertEqual(lu.get_allowed_doors_html_links(),correct_return_string) 




    def test_prettify_get_allowed_doors(self):
        """ """
        door1 = Door.objects.create(name='Space 1')
        door2 = Door.objects.create(name='Space 2')
        door3 = Door.objects.create(name='Space 3')  # not assigned
        lu=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        lu.doors=[door1, door2]
        lu.save()

        correct_return_string = "%s, %s" % (door1.name, door2.name)
        self.assertEqual(lu.prettify_get_allowed_doors(),correct_return_string) 











    def test_get_all_access_times(self):
        """ Are the access times (access_time field for AccessTime object) for this LockUser the same as those returned by get_all_access_times (or None) """
        # create our lockusers
        lu1=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        lu2=LockUser.objects.create(first_name='John',last_name='Doe',email='jdoe2@gmail.com')
        
        # create several access times, including for different lockusers
        at1 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at2 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at3 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at4 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu2)

        # test the result for one lockuser 
        self.assertEqual(lu1.get_all_access_times(), [at1.access_time, at2.access_time, at3.access_time] )

        # Testing the case when there are no access times: delete the access times just created for this lock user
        at1.delete()
        at2.delete()
        at3.delete()

        # and test again
        self.assertEqual(lu1.get_all_access_times(), [])

        # todo?  check that ordered by time.... 


    def test_get_last_access_time(self):
        """ Is the last access time for this LockUser the same as that returned by get_last_access_time (or None) """
        # create our lockusers
        lu1=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        lu2=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe2@gmail.com')
        
        # create several access times, including for different lockusers
        at1 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at2 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at3 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at4 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu2)

        # test the result for one lockuser 
        self.assertEqual(lu1.get_last_access_time(), at3.access_time)

        # Testing the case when there are no access times: delete the access times just created for this lock user
        at1.delete()
        at2.delete()
        at3.delete()

        # and test again
        self.assertEqual(lu1.get_last_access_time(), None)

    def test_prettify_get_last_access_time(self):
        """ Check that this method formats the last access time correctly """
        # create our lockusers
        lu1=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        lu2=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe2@gmail.com')
        
        # create several access times, including for different lockusers
        at1 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at2 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at3 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu1)
        at4 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc), lockuser=lu2)

        # test the result for one lockuser 
        self.assertEqual(lu1.prettify_get_last_access_time(), at3.access_time.strftime("%B %d, %Y, %I:%M %p"))

        # Testing the case when there are no access times: delete the access times just created for this lock user
        at1.delete()
        at2.delete()
        at3.delete()

        # and test again
        self.assertEqual(lu1.prettify_get_last_access_time(), None)



    def test_custom_save_deactivate_keycard(self):
        """ Check that custom save deactivates current keycard """
        ##########################################################
        #  create the objects and 'supporting' objects we need
        ##########################################################
        lu = LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(the_rfid='abcde12345',lockuser=lu, assigner=staff_only_user)

        lu.deactivate_current_keycard = True

        lu.current_keycard_revoker = staff_only_user

        lu.save()
        
        # todo: organization/necessity of below asserts....
        # Now explicitly save() and check that deactivate_current_keycard is now
        #   False; that current_keycard_revoker = None; and that the keycard is
        #   no longer active
        self.assertFalse(lu.deactivate_current_keycard)
        self.assertEqual(lu.current_keycard_revoker, None)

        # refetch to get changes
        rk = RFIDkeycard.objects.get(the_rfid='abcde12345',lockuser=lu, assigner=staff_only_user)
        self.assertFalse(rk.is_active())
        


    def test_custom_save_assign_keycard(self):
        """ Check that custom save assigns (creates and saves) new RFIDkeycard for this LockUser """
        #################################
        # need LockUser, NewKeycardScan with ready_to_assign=True (and its assigner User)
        #################################
        lu=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')
        #print colored("Creating staff user doing this......","cyan")
        staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        new_nks_obj = NewKeycardScan.objects.create(rfid='abcdefghij', assigner_user=staff_only_user,ready_to_assign=True)

        num_rk_before = len(RFIDkeycard.objects.all())

        lu.save()

        # refetch the NewKeycardScan object
        new_nks_obj = NewKeycardScan.objects.get(pk=new_nks_obj.pk)

        # check that the NewKeycardScan object's ready_to_assign is now False
        self.assertFalse(new_nks_obj.ready_to_assign)

        # check that a new RFIDkeycard has been created:  make sure there is one more RFIDkeycard object now
        self.assertEqual(num_rk_before+1, len(RFIDkeycard.objects.all()))

        # check that the new keycard has the right attributes
        new_rk = RFIDkeycard.objects.latest("date_created")
        self.assertEqual(new_rk.lockuser,lu)
        self.assertEqual(new_rk.the_rfid, new_nks_obj.rfid)
        self.assertEqual(new_rk.assigner, new_nks_obj.assigner_user)


    def test_last_access_time_and_link_to_more(self):
        """ Check that method returns the correctly formatted html string """

        # create our lockuser
        lu=LockUser.objects.create(first_name='Jane',last_name='Doe',email='jdoe@gmail.com')

        # no access times for this lock user
        # todo:  or ...   test this after the next assert -- so .delete() the access times
        self.assertEqual(lu.last_access_time_and_link_to_more(), None)
        
        # create several access times
        at1 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc)+timedelta(days=1), lockuser=lu)
        at2 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc)+timedelta(days=2), lockuser=lu)
        at3 = AccessTime.objects.create(access_time = datetime.now().replace(tzinfo=utc)+timedelta(days=3), lockuser=lu)

        link = "<a href='../../accesstime/?lockuser__id__exact=%d'>View all access times</a>" %  lu.id 
        correct_output_string = "%s (%s)" % (at3.access_time.strftime("%B %d, %Y, %I:%M %p") , link)

        self.assertEqual(lu.last_access_time_and_link_to_more(), correct_output_string)

