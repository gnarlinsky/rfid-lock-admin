from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from rfid_lock_management.models import *
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
#from django.utils.timezone import utc
from test_helpers import t_info


class DoorModelTests(TestCase):

    def setUp(self):
        t_info("TestCase DoorModelTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)

    def test_unicode(self):
        """
        Test that custom __unicode__() method returns name of Door
        """
        door = Door.objects.create(name='Test door')
        self.assertEqual(unicode(door), 'Test door')

    def test_door_perm_creation(self):
        """
        When a new Door is added, create a corresponding Permission (i.e.
        checking Door's save() method)
        """
        door_name = "Test door"
        door = Door(name=door_name)
        # explicitly save()'ing rather than Door.objects.create()
        door.save()

        # now check that both door and associated permission exist
        d = Door.objects.filter(name=door_name)
        self.assertTrue(d)

        # note: door_name, not door.name
        p = Permission.objects.filter(codename='can_manage_door_%d' % door.pk,
            name='Can manage door to %s' % door_name,
            content_type=ContentType.objects.get(
                app_label='rfid_lock_management',
                model='door'))
        self.assertTrue(p)


class AccessTimeModelTests(TestCase):

    def setUp(self):
        t_info("TestCase AccessTimeModelTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)

    def test_unicode(self):
        """
        Test that custom __unicode__() returns the correctly formatted time
        """
        time = datetime.datetime(2013, 5, 16, 15, 30, 20)
        at = AccessTime.objects.create(access_time=time)
        self.assertEqual(unicode(at), 'May 16, 2013, 03:30 PM')

    def test_get_this_lockuser_html(self):
        """
        Create AccessTime with specific lockuser; make sure
        get_this_lockuser_html returns the correct html
        """
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        at = AccessTime.objects.create(lockuser=lu)
        self.assertEqual(at.get_this_lockuser_html(),
            "<a href='../lockuser/%d/'>%s</a>" % (lu.pk, lu))


class RFIDkeycardModelTests(TestCase):

    def setUp(self):
        t_info("TestCase RFIDkeycardModelTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 3)

    def test_unicode(self):
        """
        Test that custom __unicode__() method returns the rfid string.
        """
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(
            the_rfid='abcde12345', lockuser=lu, assigner=staff_only_user)
        self.assertEqual(unicode(rk), 'abcde12345')

    def test_get_allowed_doors(self):
        """
        Does get_allowed_doors() return the door(s), if any, that the
        associated lockuser is allowed to access
        """
        # create the LockUser and Doors
        door1 = Door.objects.create(name='Allowed door')
        door2 = Door.objects.create(name='Prohibited door')
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(
            the_rfid='abcde12345', lockuser=lu, assigner=staff_only_user)

        # only one door allowed
        lu.doors = [door1]
        self.assertEqual(list(rk.get_allowed_doors()), [door1])
        # todo:  here and elsewhere, consider using assertQuerysetEqual() --
        # see http://stackoverflow.com/a/14189017

        # no doors allowed
        lu.doors = []
        self.assertEqual(list(rk.get_allowed_doors()), [])

    def test_deactivate(self):
        """
        On deactivation, is RFIDkeycard object's date revoked and revoker set
        correctly?
        """
        # create keycard and associated lockuser
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(
            the_rfid='abcde12345', lockuser=lu, assigner=staff_only_user)

        # need logged in user so we can assign the revoker
        self.client = Client()
        self.client.login(username='johnny_staff', password='my_password')

        # Check that the time revoked is correct -- i.e. that it's now. But we
        # need to account for lag in time between setting the now variable and
        # executing deactivate (including the print statement). This can be
        # done with assertAlmostEqual(first, second, delta=None). This is my
        # approach to calculate the delta:
        #   - get the time at t1
        #   - RFIDkeycard.deactivate() at time t2=t1+x
        #   - assert for RFIDkeycard.date_revoked at time t3=t1+x+y
        #   - So deactivation happened AT MOST x+y microseconds ago,
        #     at time of assertion
        #   - So, setting delta to the time difference between t1 and t3,
        #     or x + y
        #   - i.e. now() minus t1
        t1 = datetime.datetime.now()
        t_info("Deactivating keycard......", 3)
        rk.deactivate(staff_only_user)

        t_info("Is the date revoked correct", 4)
        self.assertAlmostEqual(rk.date_revoked, 
            datetime.datetime.now(),
            delta=datetime.datetime.now() - t1)
        t_info("Is the revoker our user", 4)
        self.assertEqual(rk.revoker, staff_only_user)

    def test_is_active(self):
        """ """
        # create keycard and associated lockuser
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(
            the_rfid='abcde12345', lockuser=lu, assigner=staff_only_user)

        # should be active after just created
        self.assertTrue(rk.is_active())

        # set fake date revoked
        now = datetime.datetime.now()
        rk.date_revoked = now
        self.assertFalse(rk.is_active())


class LockUserModelTests(TestCase):

    def setUp(self):
        t_info("TestCase LockUserModelTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 3)

    def test_creating_new_obj_and_saving_it_to_db(self):
        """
        Create new LockUser, set attributes, save to database
        """
        t_info("Can we create new LockUser; set attributes; save it?", 4)
        lockuser = LockUser()
        lockuser.first_name = "Homer"
        lockuser.last_name = "Simpson"
        lockuser.email = "chunkylover53@aol.com"
        lockuser.address = "742 Evergreen Terrace, Springfield, USA"
        lockuser.phone_number = "(939) 555-5555"
        lockuser.save()  # i.e., INSERT

        t_info("Can we find it in the database again?", 4)
        all_lockusers_in_db = LockUser.objects.all()
        self.assertEqual(len(all_lockusers_in_db), 1)
        the_only_lockuser_in_db = all_lockusers_in_db[0]
        self.assertEqual(the_only_lockuser_in_db, lockuser)

        t_info("Were the attributes saved?", 4)
        self.assertEqual(the_only_lockuser_in_db.first_name, "Homer")
        self.assertEqual(the_only_lockuser_in_db.last_name, "Simpson")
        self.assertEqual(the_only_lockuser_in_db.email, 
            "chunkylover53@aol.com")
        self.assertEqual(the_only_lockuser_in_db.address,
             "742 Evergreen Terrace, Springfield, USA")
        self.assertEqual(the_only_lockuser_in_db.phone_number, "(939) 555-5555")

    def test_unicode(self):
        """
        Test that custom __unicode__() -- i.e. just obj_name -- returns first
        and last name of lockuser
        """
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        self.assertEqual(unicode(lu), 'Jane Doe')

    def test_is_active(self):
        """
        Check if is_active() reflects whether the user is assigned a keycard
        """
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        self.assertFalse(lu.is_active())

        # now assigning a keycard
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(
            the_rfid='abcde12345', lockuser=lu, assigner=staff_only_user)
        self.assertTrue(lu.is_active())

    def test_get_allowed_doors(self):
        """
        Does get_allowed_doors() return the door(s), if any, that the lockuser
        is allowed to access
        """
        # create the LockUser and Doors and associated/'supporting' objects
        door1 = Door.objects.create(name='Allowed door')
        door2 = Door.objects.create(name='Prohibited door')
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(
            the_rfid='abcde12345', lockuser=lu, assigner=staff_only_user)

        # only one door allowed
        lu.doors = [door1]
        self.assertEqual(list(lu.get_allowed_doors()), [door1])

        # no doors allowed
        lu.doors = []
        self.assertEqual(list(lu.get_allowed_doors()), [])

    def test_get_all_rfids(self):
        """
        Does get_all_rfids() returns all RFIDkeycards objects associated with
        Lockuser
        """
        lu1 = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        lu2 = LockUser.objects.create(
            first_name='John', last_name='Doe', email='jdoe2@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        # Of these four RFIDkeycards, three are assigned to the LockUser will
        # be testing this with, meaning that three should be in the returned
        # list
        rk1 = RFIDkeycard.objects.create(
            the_rfid='abcde11111', lockuser=lu1, assigner=staff_only_user)
        rk2 = RFIDkeycard.objects.create(
            the_rfid='abcde22222', lockuser=lu2, assigner=staff_only_user)
        rk3 = RFIDkeycard.objects.create(
            the_rfid='abcde33333', lockuser=lu2, assigner=staff_only_user,
            date_revoked=datetime.datetime.now())
        rk4 = RFIDkeycard.objects.create(
            the_rfid='abcde44444', lockuser=lu2, assigner=staff_only_user,
            date_revoked=datetime.datetime.now())

        # Note - below does not evaluate these as equivalent, must list()
        # self.assertEqual(lu2.get_all_rfids(),
        # RFIDkeycard.objects.filter(pk__in=[rk2.pk,rk3.pk,rk4.pk]))
        self.assertEqual(list(lu2.get_all_rfids()), [rk2, rk3, rk4])

    def test_get_all_rfids_html(self):
        """
        Check that method returns the correctly formatted html string of all
        rfids, NOT including the current one
        """
        lu1 = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        lu2 = LockUser.objects.create(
            first_name='John', last_name='Doe', email='jdoe2@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        # Of these four RFIDkeycards, three are assigned to the LockUser will
        # be testing this with, and one of those is the LockUser's current
        # keycard, meaning that there should only be two in the returned list
        rk1 = RFIDkeycard.objects.create(
            the_rfid='abcde11111', lockuser=lu1, assigner=staff_only_user)
        rk2 = RFIDkeycard.objects.create(
            the_rfid='abcde22222', lockuser=lu2, assigner=staff_only_user)
        rk3 = RFIDkeycard.objects.create(
            the_rfid='abcde33333', lockuser=lu2, assigner=staff_only_user,
            date_revoked=datetime.datetime.now())
        rk4 = RFIDkeycard.objects.create(
            the_rfid='abcde44444', lockuser=lu2, assigner=staff_only_user,
            date_revoked=datetime.datetime.now())

        # Issue #x
        first_rfid = "RFID: %s (activated on %s by %s; revoked on %s by %s)" % (
            rk3.the_rfid, rk3.date_created.strftime("%B %d, %Y, %I:%M %p"),
            rk3.assigner, rk3.date_revoked.strftime("%B %d, %Y, %I:%M %p"),
            rk3.revoker
        )
        second_rfid = "RFID: %s (activated on %s by %s; revoked on %s by %s)" % (
            rk4.the_rfid, rk4.date_created.strftime("%B %d, %Y, %I:%M %p"),
            rk4.assigner, rk4.date_revoked.strftime("%B %d, %Y, %I:%M %p"),
            rk4.revoker
        )
        correct_output_string = first_rfid + ",<br>" + second_rfid
        self.assertEqual(lu2.get_all_rfids_html(), correct_output_string)

    def test_get_current_rfid(self):
        """ """
        # Of these four RFIDkeycards, three are assigned to the LockUser will
        # be testing this with, and one of those is the LockUser's current
        # keycard
        lu1 = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        lu2 = LockUser.objects.create(
            first_name='John', last_name='Doe', email='jdoe2@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        rk1 = RFIDkeycard.objects.create(
            the_rfid='abcde11111', lockuser=lu1, assigner=staff_only_user)
        rk2 = RFIDkeycard.objects.create(
            the_rfid='abcde22222', lockuser=lu2, assigner=staff_only_user)
        rk3 = RFIDkeycard.objects.create(
            the_rfid='abcde33333', lockuser=lu2, assigner=staff_only_user,
            date_revoked=datetime.datetime.now())
        rk4 = RFIDkeycard.objects.create(
            the_rfid='abcde44444', lockuser=lu2, assigner=staff_only_user,
            date_revoked=datetime.datetime.now())
        self.assertEqual(lu2.get_current_rfid(), rk2)

    def test_prettify_get_current_rfid(self):
        """ """
        lu = LockUser.objects.create(
            first_name='John', last_name='Doe', email='jdoe2@gmail.com')
        self.assertEqual(lu.prettify_get_current_rfid(), None)

        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        curr_rfid = RFIDkeycard.objects.create(
            the_rfid='abcde22222', lockuser=lu, assigner=staff_only_user)
        correct_return_string = "RFID: %s (activated on %s by %s)" % (
            curr_rfid.the_rfid,
            curr_rfid.date_created.strftime("%B %d, %Y, %I:%M %p"),
            curr_rfid.assigner
        )
        self.assertEqual(lu.prettify_get_current_rfid(), correct_return_string)

    def test_prettify_get_allowed_doors_html_links(self):
        """ """
        door1 = Door.objects.create(name='Space 1')
        door2 = Door.objects.create(name='Space 2')
        door3 = Door.objects.create(name='Space 3')
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        lu.doors = [door1, door2]
        lu.save()

        correct_return_string = ("<a href='../door/%d/'>%s</a>, "
             "<a href='../door/%d/'>%s</a>") % (
             door1.pk, door1.name, door2.pk, door2.name)
        self.assertEqual(lu.get_allowed_doors_html_links(),
            correct_return_string)

    def test_prettify_get_allowed_doors(self):
        """ """
        door1 = Door.objects.create(name='Space 1')
        door2 = Door.objects.create(name='Space 2')
        door3 = Door.objects.create(name='Space 3')  # not assigned
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        lu.doors = [door1, door2]
        lu.save()
        correct_return_string = "%s, %s" % (door1.name, door2.name)

        self.assertEqual(lu.prettify_get_allowed_doors(),
            correct_return_string)

    def test_get_all_access_times(self):
        """
        Are the access times (access_time field for AccessTime object) for this
        LockUser the same as those returned by get_all_access_times (or None)
        """
        # create our lockusers
        lu1 = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        lu2 = LockUser.objects.create(
            first_name='John', last_name='Doe', email='jdoe2@gmail.com')

        # create several access times, including for different lockusers
        at1 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at2 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at3 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at4 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu2)

        # test the result for one lockuser
        self.assertEqual(lu1.get_all_access_times(), [
                         at1.access_time, at2.access_time, at3.access_time])

        # Testing the case when there are no access times: delete the access
        # times just created for this lock user
        at1.delete()
        at2.delete()
        at3.delete()

        # and test again
        self.assertEqual(lu1.get_all_access_times(), [])

    def test_get_last_access_time(self):
        """
        Is the last access time for this LockUser the same as that returned by
        get_last_access_time (or None) """
        # create our lockusers
        lu1 = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        lu2 = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe2@gmail.com')

        # create several access times, including for different lockusers
        at1 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at2 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at3 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at4 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu2)

        # test the result for one lockuser
        self.assertEqual(lu1.get_last_access_time(), at3.access_time)

        # Testing the case when there are no access times: delete the access
        # times just created for this lock user
        at1.delete()
        at2.delete()
        at3.delete()

        # and test again
        self.assertEqual(lu1.get_last_access_time(), None)

    def test_prettify_get_last_access_time(self):
        """ Check that this method formats the last access time correctly """
        # create our lockusers
        lu1 = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        lu2 = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe2@gmail.com')

        # create several access times, including for different lockusers
        at1 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at2 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at3 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu1)
        at4 = AccessTime.objects.create(
            access_time=datetime.datetime.now(), lockuser=lu2)

        # test the result for one lockuser
        self.assertEqual(lu1.prettify_get_last_access_time(),
             at3.access_time.strftime("%B %d, %Y, %I:%M %p"))

        # Testing the case when there are no access times: delete the access
        # times just created for this lock user
        at1.delete()
        at2.delete()
        at3.delete()

        # and test again
        self.assertEqual(lu1.prettify_get_last_access_time(), None)

    def test_custom_save_deactivate_keycard(self):
        """
        Check that custom save deactivates current keycard
        """
        #  create the objects and 'supporting' objects we need
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        rk = RFIDkeycard.objects.create(
            the_rfid='abcde12345', lockuser=lu, assigner=staff_only_user)
        lu.deactivate_current_keycard = True
        lu.current_keycard_revoker = staff_only_user
        lu.save()

        # Explicitly save() and check that deactivate_current_keycard is now
        # False; that current_keycard_revoker = None; and that the keycard is
        # no longer active
        self.assertFalse(lu.deactivate_current_keycard)
        self.assertEqual(lu.current_keycard_revoker, None)

        # refetch to get changes
        rk = RFIDkeycard.objects.get(
            the_rfid='abcde12345', lockuser=lu, assigner=staff_only_user)
        self.assertFalse(rk.is_active())

    def test_custom_save_assign_keycard(self):
        """
        Check that custom save assigns (creates and saves) new RFIDkeycard for
        this LockUser
        """
        # need LockUser, NewKeycardScan with ready_to_assign=True (and its
        # assigner User)
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')
        t_info("Creating staff user doing this......", 3)
        staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')
        new_nks_obj = NewKeycardScan.objects.create(
            rfid='abcdefghij', assigner_user=staff_only_user,
            ready_to_assign=True)
        num_rk_before = len(RFIDkeycard.objects.all())
        lu.save()

        # refetch the NewKeycardScan object
        new_nks_obj = NewKeycardScan.objects.get(pk=new_nks_obj.pk)

        # check that the NewKeycardScan object's ready_to_assign is now False
        self.assertFalse(new_nks_obj.ready_to_assign)

        # check that a new RFIDkeycard has been created:  make sure there is
        # one more RFIDkeycard object now
        self.assertEqual(num_rk_before + 1, len(RFIDkeycard.objects.all()))

        # check that the new keycard has the right attributes
        new_rk = RFIDkeycard.objects.latest("date_created")
        self.assertEqual(new_rk.lockuser, lu)
        self.assertEqual(new_rk.the_rfid, new_nks_obj.rfid)
        self.assertEqual(new_rk.assigner, new_nks_obj.assigner_user)

    def test_last_access_time_and_link_to_more(self):
        """
        Check that method returns the correctly formatted html string
        """
        # create our lockuser
        lu = LockUser.objects.create(
            first_name='Jane', last_name='Doe', email='jdoe@gmail.com')

        # no access times for this lock user
        self.assertEqual(lu.last_access_time_and_link_to_more(), None)

        # create several access times
        at1 = AccessTime.objects.create(
            access_time=datetime.datetime.now() + timedelta(days=1),
            lockuser=lu)
        at2 = AccessTime.objects.create(
            access_time=datetime.datetime.now() + timedelta(days=2),
            lockuser=lu)
        at3 = AccessTime.objects.create(
            access_time=datetime.datetime.now() + timedelta(days=3),
            lockuser=lu)

        link = ("<a href='../../accesstime/?lockuser__id__exact=%d'>"
            "View all access times</a>") % lu.id
        correct_output_string = "%s (%s)" % (
            at3.access_time.strftime("%B %d, %Y, %I:%M %p"), link)
        self.assertEqual(lu.last_access_time_and_link_to_more(),
            correct_output_string)
