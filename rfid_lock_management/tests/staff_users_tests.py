from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from rfid_lock_management.models import RFIDkeycard, LockUser, Door, AccessTime
from termcolor import colored
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


#######################################################################################
# TO DO: 
#######################################################################################
#  Note - update relevant to various test to-do's: getting rid of the concept of lockuser deactivation
#######################################################################################
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



class StaffUserTests(TestCase):
    """
    TO DO: 
    In the list of accesstimes, 
    - staff can only see the doors they have permission to. 
    - staff users should not be able to the actual RFID's,  
    - and they should be able to see only the doors they have permissions for
    - should only be able to see buttons + top menu options for: 
        (1) add new lock user
        (2) lock users
        (3) Locks
        (4) Room access log and graphs

        # TO DO:
        # Staff vs superusers:
        # Only superusers see the RFID numbers and certain other fields 
        # # both on change forms and display lists.  To regular staff users, 
        # # these fields are meaningless. 
        # #            (Here's a short list just to get started, there are others)
        # #     - prettify get current rfid, get current rfid
        # #     - prettify get all rfid's, get all rfid's


    No regular staff user should able to *add* Doors, for now. 

    Staff users with can-add/del/change-Doors should be able to:
        * See ALL Doors
        * be able to add/del/change Doors

    NOBODY (other than developers), not even special super staff users, should be able to edit RFIDkeycards directly. 


    New keycard scan:  test timing, e.g.  
     * someone else initiates a new keycard scan after you -- will you use your newKeycardScan object, or the one created later? 
        


    ----------------- More on permissions ----------------------------------
    (these are not to check whether perms are created for doors, but to check whether they're obeyed) 
    Custom user permissions for door management are dynamically created, based on the doors that are present in the
        system -- so load the door fixture as well as the staff user fixture if using fixtures, using natural keys
        (https://docs.djangoproject.com/en/1.4/ref/django-admin/#django-admin-option---natural).
        (More on natural keys:  see #1 in expanded_comments)

        TO DO: (a) Check that custom user permissions exist for all  doors in the system...
               (b) which is a separate test from: does user have certain custom permissions!  (so probably that test
               should not  be in UserTests suite? It just concerns Permissions and Doors.....)
               (c) which is a separate test from just assigning regular permissions to staff users!

            (a) 
            * Note: if you load door *fixtures*, permissions won't be created programmatically -- so create Door objects here 
            * check that there are now custom permissions with the right door names, codenames, etc. 
            
            (b) 
            * Now should be able to reference those permissions (know what the codenames are), and try to assign, unassign them
              for staff user. 
            * check that they actually control what the staff user can/can't do/view

            (c) 
            * Assign/unassign these
                #    [<Permission: rfid_lock_management | door | Can add door>]               (pk = 2)
                #    [<Permission: rfid_lock_management | lock user | Can add lock user>] (pk = 6) 
                #    [<Permission: rfid_lock_management | lock user | Can change lock user>]  (pk=10)
                #    [<Permission: rfid_lock_management | rfi dkeycard | Can add rfi dkeycard>]  (pk = 12)
                #    [<Permission: rfid_lock_management | rfi dkeycard | Can change rfi dkeycard>] (pk=8)
                        (others:
                        #    [<Permission: rfid_lock_management | lock user | Can manage door to Bike Project>] (pk=39)
                        #    [<Permission: rfid_lock_management | lock user | Can manage door to Makerspace>] (pk = 38)
                        #    [<Permission: rfid_lock_management | lock user | Can manage door to Door X>] (pk=35)
                        )
            * and check that these permissions actually control what the user can and can't do/view
    """

    def setUp(self):
        print colored("\nTestCase StaffUserTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") # or you could just set verbosity=2 with manage.py...
        #       This?  get diff types of users  from a fixture or create here.
        #       Explicitly set its
        #       - staff to false and
        #       - superuser to false for a staff-only user;
        #       - then set superuser to true (staff status doesn't matter) to test the other side of the coin.
        #self.staff_only_user = User.objects.create_user('Chevy Chase', 'chevy@chase.com', 'chevyspassword')
        #self.staff_only_user = User.objects.get(username="staff_only_test_user")


        self.client = Client()

        print colored("Creating staff user......","cyan")
        self.staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')

        print colored("logging in as staff user....","cyan")
        self.client.login(username='johnny_staff',password='my_password')


    def tearDown(self):
        # Clean up after each test
        self.staff_only_user.delete()

    # - when active staff users add/update a lock user they should only see doors
    #   for which they themselves have permissions
    def test_staff_only_user_can_only_see_doors_they_have_permission_for(self):
        # todo: .... right now it's just test_can_add_and_check_for_random_permission(self): """
        """ staff-only user can only see the doors they have permission to see? """

        print colored("\tAssign permissions (only superuser should be able to).......", "cyan") # todo: doing this as superuser? 
        perm_codename = "some_permission_x"
        perm_name = "Permission Number X"
      
        # Create the permission object:
        content_type = ContentType.objects.get(app_label='rfid_lock_management', model='lockuser')
        perm = Permission.objects.create(codename=perm_codename, name=perm_name, content_type=content_type)

        print colored("\tTesting whether user has the permission already (should not)", "blue")
        self.assertFalse(self.staff_only_user.has_perm(perm_codename))

        # now add the permission
        #self.staff_only_user.user_permissions.add(perm, self.staff_only_user.profile)
        self.staff_only_user.user_permissions.add(perm)

        # Django does cache user permissions, which screws with things. So 
        # refetch user from the database (http://stackoverflow.com/a/10103291)
        self.staff_only_user = User.objects.get(pk=self.staff_only_user.pk)  # should now have the assigned permission

        # Testing whether user has the permission now
        print colored("\tTesting whether user has the permission now", "blue")
        #self.assertTrue(self.staff_only_user.has_perm(perm_codename), self.staff_only_user.profile)  
        self.assertTrue(self.staff_only_user.has_perm('rfid_lock_management.'+perm_codename))  
        #print self.staff_only_user.get_all_permissions() # should now include new permission
        #print colored("\t(doors)"+str(Door.objects.all()), "cyan")

        # staff-only users can only see/assign Doors that they themselves have access to. 
        # So whatever is in the list that user.doors returns (pk's), those are the only ones that this
        # user has the permission to add to lockuser.doors.   i.e. create/verify the existence of a
        # lockuser with certain door permissions

        # self.user.user_permissions.add(Permission.objects.get(codename='change_user'))
        #self.fail("getting to this.....")


    #def test_can_change_non_staff_users(self):
    #    self.assertFalse(self.user.has_perm('logical_change_user', self.non_staff.profile)) # can't change non staff users without permission
    #
    #    # now add the permission and test it again
    #    self.user.user_permissions.add(Permission.objects.get(codename='change_user'))
    #
    #    # refetch user from the database
    #    self.user = User.objects.get(pk=self.user.pk)
    #    print self.user.get_all_permissions() # should now include new permission
    #    self.assertTrue(self.user.has_perm('logical_change_user', self.non_staff.profile))
