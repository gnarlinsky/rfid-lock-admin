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
# update: moved to other files
#######################################################################################
