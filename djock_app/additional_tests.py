from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from djock_app.models import RFIDkeycard, LockUser, Door, AccessTime
from termcolor import colored
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


"""
# to run only some tests: 
#   $ ./manage.py test djock_app.LockUserModelTest

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



#######################################################################################
#  Functional tests 
#######################################################################################
#  "We start by writing some browser tests - functional tests, which
#  simulate what an actual user would see and do. We'll use Selenium, a test tool which
#  actually opens up a real web browser, and then drives it like a real user, clicking
#  on links and buttons, and checking what is shown on the screen. These are the tests
#  that will tell us whether or not our application behaves the way we want it to, from
#  the user's point of view."  (http://www.tdd-django-tutorial.com/tutorial/1/)
#  Selenium: in-browser framework to test rendered HTML and the behavior of Web pages,
#   e.g. JavaScript
#######################################################################################
"""

# The most atomic bits for functional tests are magenta; unit tests cyan

# LiveServerTestCase starts up a test web server in a separate thread
class RenameLaterTests(LiveServerTestCase):
    fixtures = ['test_staff_superuser.json']  # to save the test user so can succeed on login tests
                                            # (everything should be same for a non-staff superuser as
                                            # well, though... Test for that? )
    # (make sure the only staff user is the superuser in the db currently, then 
    #   ./manage.py dumpdata auth.User --indent=2 > test_staff_superuser.json )
    def setUp(self):
        """ Start up Selenium WebDriver browser instance """
        print colored("\nSETTING UP / LiveServerTestCase RenameLaterTests - test doing stuff in the *browser*", "white","on_green")
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)  # tells webdriver to use a max timeout of 3 seconds

    def tearDown(self):
        """ Shut down Selenium WebDriver browser instance """
        print colored("\nTEARING DOWN", "green")
        self.browser.quit()

   # def test_can_get_to_login_screen_and_log_in(self):
    def test_can_do_stuff_in_browser(self):
        print colored("\nTEST: does user see the login screen when going to /lockadmin; able to log in; see the right stuff on the following screen; <........> ?", "blue")

        print colored("\tChecking if we can open browser and get to the log in screen at /lockadmin", "magenta")
        self.browser.get(self.live_server_url + '/lockadmin') # user opens web browser; goes to admin page

        print colored("\tDoes it say RFID Lock Administration?", "magenta")
        login_page_body = self.browser.find_element_by_tag_name('body') # returns WebElement object
        self.assertIn("RFID Lock Administration", login_page_body.text)  # .text strips out the HTML markup

        print colored("\tCan user actually log in via website?", "magenta")
        # The user "test" was created when we loaded the fixture test_staff_user.json
        # User types in username and password and hits return
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('test')
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('test')
        password_field.send_keys(Keys.RETURN)

        print colored("\tAfter username and password accepted, is the user taken to the admin page", "magenta")
        base_page_body = self.browser.find_element_by_tag_name('body')
        self.assertIn("Welcome, test. Change password / Log out", base_page_body.text)

        print colored("\tDoes user see the links in the top navigation bar?","magenta")
        base_page_body = self.browser.find_element_by_tag_name('body')
        self.assertIn("main | lock users | door locks | access logs | staff users", base_page_body.text)

        
        # To do -- does user see the other links...
        # print colored("Does user see the links in the top navigation bar?","magenta")
        # base_page_links = self.browser.find_elements_by_link_text('blah blah blah')
        # self.assertEquals(blah blah blah)

    def test_can_create_new_lockuser_via_admin_site(self):
        print colored("\nTEST: can user create a new LockUser using the site?", "blue")
        # to do:  now create a LockUser, using the site, not like the unit tests below
        self.fail("not done yet...")

    def test_can_create_new_door_via_admin_site(self):
        print colored("\nTEST: can user create a new Door using the site?", "blue")
        # to do:  now create a LockUser, using the site, not like the unit tests below
        self.fail("not done yet...  same thing for the other Models")


#######################################################################################
#  Unit tests
#######################################################################################
class RFIDkeycardAssignmentTest(TestCase):
    """
    USE CASES CONCERNING SPECIFICALLY ASSIGNING A NEW KEYCARD TO A LOCK USER THROUGH THE WEB INTERFACE.(so these parallel functional tests)

    * staff user or super user wants to assign a new keycard to a lockuser with an active keycard already.
        (lockuser is active, since have active keycard).
    - What should happen: The staff user should not be able to do that.  This is what the staff user should see:
        * The thing link/img for "assign new keycard" should be grayed out/non-functional;
        * but right nearby there should also be a button/link "Deactivate current keycard."
        (or just have one control, but switch between these two)

    * staff user/superuser wants to assign a new keycard to an active lockuser, but no keycard already:
        - Deactivate current keycard" should not be functional
        - "Assign new keycard" should be functional

    * staff user/superuser wants to assign a new keycard to a lockuser, but lockuser is inactive :
        - Deactivate current keycard" should not be functional
        - text for "assign new keycard" should actually be "activate lockuser and assign new keycard" (or
          just have one control, but switch between these two)

    fixture rename_back_initial_data.json: only lisa and ralph don't have a current rfid; only lisa is inactive
    """
    def SetUp(self):
        pass

    def TearDown(self):
        pass

class LockUserModelTest(TestCase):
    # here won't be using Selenium; interacting with application at a lower level
    def test_creating_new_lockuser_and_saving_it_to_db(self):
        print colored("\nTEST: create new LockUser, set attributes, save to database","blue")

        print colored("\tCan we create new LockUser; set attributes; save it?","cyan")
        lockuser = LockUser()
        lockuser.first_name = "Homer"
        lockuser.last_name = "Simpson"
        lockuser.email =  "chunkylover53@aol.com"
        lockuser.address = "742 Evergreen Terrace, Springfield, USA"
        lockuser.phone_number = 9395555555   # to do: actually change phone_number to char field in the code
        """
        lockuser.birthdate = 
        lockuser.middle_name  = 
        doors, rfids
        is active
        get_all_access_times, prettify
        get_last_access_time, prettify
        get_all_rfids, prettify
        get_current_rfid, prettify
        get_allowed_doors, prettify
        """
        lockuser.save()  # i.e., INSERT

        print colored("\tCan we find it in the database again?","cyan")
        # Note that this will fail if some other fixture is loaded already!!!!!!!!!!!!!!!!!!!!!!!
        all_lockusers_in_db = LockUser.objects.all()
        self.assertEquals(len(all_lockusers_in_db),1)
        the_only_lockuser_in_db = all_lockusers_in_db[0]
        self.assertEquals(the_only_lockuser_in_db, lockuser)

        print colored("\tWere the attributes saved?","cyan")
        self.assertEquals(the_only_lockuser_in_db.first_name,"Homer")
        self.assertEquals(the_only_lockuser_in_db.last_name,"Simpson")
        self.assertEquals(the_only_lockuser_in_db.email,"chunkylover53@aol.com")
        self.assertEquals(the_only_lockuser_in_db.address,"742 Evergreen Terrace, Springfield, USA")
        self.assertEquals(the_only_lockuser_in_db.phone_number,9395555555)
# TO DO: same as above for the other models

class DoorModelTests(TestCase):
    def setUp(self):
        print colored("\nSETTING UP / TestCase DoorModelTests", "white", "on_green")
        fixtures = ['just_doors.json'] 

class UserTests(TestCase):
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
                #    [<Permission: djock_app | door | Can add door>]               (pk = 2)
                #    [<Permission: djock_app | lock user | Can add lock user>] (pk = 6) 
                #    [<Permission: djock_app | lock user | Can change lock user>]  (pk=10)
                #    [<Permission: djock_app | rfi dkeycard | Can add rfi dkeycard>]  (pk = 12)
                #    [<Permission: djock_app | rfi dkeycard | Can change rfi dkeycard>] (pk=8)
                        (others:
                        #    [<Permission: djock_app | lock user | Can manage door to Bike Project>] (pk=39)
                        #    [<Permission: djock_app | lock user | Can manage door to Makerspace>] (pk = 38)
                        #    [<Permission: djock_app | lock user | Can manage door to Door X>] (pk=35)
                        )
            * and check that these permissions actually control what the user can and can't do/view
    """

    def setUp(self):
        print colored("\nSETTING UP / TestCase UserTests", "white", "on_green")
        #       This?  get diff types of users  from a fixture or create here.
        #       Explicitly set its
        #       - staff to false and
        #       - superuser to false for a staff-only user;
        #       - then set superuser to true (staff status doesn't matter) to test the other side of the coin.


        self.staff_only_user = User.objects.create_user('Chevy Chase', 'chevy@chase.com', 'chevyspassword')
        #self.staff_only_user = User.objects.get(username="staff_only_test_user")

        # c = client, etc.; make sure both types users above can login first? 

    def tearDown(self):
        # Clean up after each test
        self.staff_only_user.delete()

    # - when active staff users add/update a lock user they should only see doors
    #   for which they themselves have permissions
    def test_staff_only_user_can_only_see_doors_they_have_permission_for(self):
        """ or.... right now it's just test_can_add_and_check_for_random_permission(self): """
        print colored("\nTEST: staff-only user can only see the doors they have permission to see?", "blue")

        print colored("\nAssign permissions (only superuser should be able to)", "cyan") # am I doing this as superuser? 
        perm_codename = "some_permission_x"
        perm_name = "Permission Number X"
      
        # Create the permission object:
        content_type = ContentType.objects.get(app_label='djock_app', model='lockuser')
        perm = Permission.objects.create(codename=perm_codename, name=perm_name, content_type=content_type)

        # Testing whether user has the permission already (should not)
        self.assertFalse(self.staff_only_user.has_perm(perm_codename))

        # now add the permission
        #self.staff_only_user.user_permissions.add(perm, self.staff_only_user.profile)
        self.staff_only_user.user_permissions.add(perm)

        # Django does cache user permissions, which screws with things. So 
        # refetch user from the database (http://stackoverflow.com/a/10103291)
        self.staff_only_user = User.objects.get(pk=self.staff_only_user.pk)  # should now have the assigned permission

        # Testing whether user has the permission already (should not)
        #self.assertTrue(self.staff_only_user.has_perm(perm_codename), self.staff_only_user.profile)  
        self.assertTrue(self.staff_only_user.has_perm('djock_app.'+perm_codename))  
        #print self.staff_only_user.get_all_permissions() # should now include new permission
        #print colored("\t(doors)"+str(Door.objects.all()), "cyan")

        # staff-only users can only see/assign Doors that they themselves have access to. 
        # So whatever is in the list that user.doors returns (pk's), those are the only ones that this
        # user has the permission to add to lockuser.doors.   i.e. create/verify the existence of a
        # lockuser with certain door permissions

        # self.user.user_permissions.add(Permission.objects.get(codename='change_user'))
        #self.fail("getting to this.....")

    # Actually, staff-only users should not be able to delete anything, only deactivate
    def _test_deleting_lockuser(self):
        # Do I have to create and save a lockuser again like above?
        # Only the superuser should be able to actually delete a user object; regular, staff users
        #   should only have the power to deactivate, not delete. (Right?)
        
        #   How to specify the permissions of the user that would be doing this stuff, 
        #   deleting, creating, etc? 
        #       This?  get a user from a fixture or create one. Explicitly set its staff to false and
        #       superuser to false for a staff-only user;  then set superuser to true (staff status
        #       doesn't matter) to test the other side of the coin.
        print colored("\nTEST: delete LockUser","blue")

        print colored("\tOnly superuser can delete?","cyan")
        # if user has superuser status (but can also have staff status): 
        #   lockuser.delete()
        #   (note also that this is a permission can set for users... So when creating a new staff user,
        #   various permissions specific to my app should be set, e.g. permission to delete *certain*
        #   objects, etc. ? Then test here for each one..... 
        #  Currently, the only permissions explicitly/automatically adding to staff-only users: 
        #       - add LockUser
        #       - change LockUser
        #       - add RFIDkeycard
        #       - change RFIDkeycard
        #       (pk's 3, 7 4, 8)
        # 
        #   now test that cannot find in the db
        print colored("\tSuperuser, so we can't find the LockUser in database?","cyan")
        #   all_lockusers_in_db = LockUser.objects.all()
        #   self.assertEquals(len(all_lockusers_in_db),0)
        # else: 
        #   test that can still find in db
        print colored("\tStaff user, so can we still find the LockUser in database?","cyan")
        #all_lockusers_in_db = LockUser.objects.all()
        #self.assertEquals(len(all_lockusers_in_db),1)
        self.fail("(to do)")

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


#  LockCommunicationTests(TestCase) -- in tests.py 
