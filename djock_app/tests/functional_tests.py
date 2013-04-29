from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from termcolor import colored
from djock_app.models import RFIDkeycard, LockUser, Door, AccessTime


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

# todo:  class LoginStuff........ to separate from stuff where ... already logged in? so can just setUp logging in? If required..............

# LiveServerTestCase starts up a test web server in a separate thread
class RenameLaterFunctionalTests(LiveServerTestCase):
    #fixtures = ['test_staff_superuser.json']  # to save the test user so can succeed on login tests
                                            # (everything should be same for a non-staff superuser as
                                            # well, though... Test for that? )
    # (make sure the only staff user is the superuser in the db currently, then 
    #   ./manage.py dumpdata auth.User --indent=2 > test_staff_superuser.json )
    
    # todo - finalize fixture, bye bye above
    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

    def setUp(self):
        """ Start up Selenium WebDriver browser instance """
        print colored("\nTestCase RenameLaterFunctionalTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green")

        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)  # tells webdriver to use a max timeout of 3 seconds

    def tearDown(self):
        """ Shut down Selenium WebDriver browser instance """
        print colored("\n(tearing down - quit browser after every test)", "green")
        self.browser.quit()

    def test_no_delete_button_lockuser_change_form(self):
        """ Check that staff users do not see a 'delete' button/link on the form page for an individual Lock User. (This is for an existing LockUser -- when *adding* a LockUser there would not be a 'delete' link/button in any case.) """
        

        """ 
        staff_user_1 = User.objects.get(username="staff_user_1")
        print colored("our user: ","white","on_red")
        print staff_user_1.__dict__

        client = Client()
        print colored("\tLogging in as staff user via client.login....","cyan")
        return_val = client.login(username=staff_user_1.username, password='staff_user_1')
        print colored("return val ===========>", "white", "on_red")
        print return_val
        """

        #################################################################
        # open browser and log in
        #################################################################
        print colored("\tOpening browser to get to lockuser's change_form.......", "cyan")
        self.browser.get(self.live_server_url + '/lockadmin/djock_app/lockuser/1')
        print colored("\tBut login first..........", "cyan")
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('staff_user_1')
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('staff_user_1')
        password_field.send_keys(Keys.RETURN)

        #################################################################
        # Now check whether the Delete link is there
        #################################################################


        """
        # yes, could get rid of the else clause and simply set 
        #  no_element_exception = False 
        # *before* the try clause -- but this is just a bit more clear...
        print colored("\tNow TRY to get our element to check for delete link presence.", "cyan")
        # Since this throws an exception if element is not found, I'm doing a 
        #   try/except here instead of a just asserting.... 
        # todo:  is this kosher?
        try:
            self.browser.find_element_by_class_name('deletelink-box')
        except NoSuchElementException:    
            # if we are in this except -- the above element was NOT found -- 
            # meaning that the test should pass
            no_element_exception = True
        else: 
            # we're in the else clause, meaning that the code in the try clause 
            # did NOT raise an exception -- the above element WAS found -- 
            # meaning that the test fails.
            no_element_exception = False

        self.assertTrue(no_element_exception)
        """

        # todo: a better/more intuitive way than the above? 
        self.assertRaises(NoSuchElementException, lambda: self.browser.find_element_by_class_name('deletelink-box'))
        # Note - lambda because something like 
        #    self.assertRaises(NoSuchElementException, self.browser.find_element_by_class_name('deletelink-box'))
        # will not work, because gathers the statements at collection time and will error then, not at testing time.

        





# todo: just putting into temp class for now to avoid running these as well
class Temp(TestCase):

    #fixtures = ['test_staff_superuser.json']  # to save the test user so can succeed on login tests
                                            # (everything should be same for a non-staff superuser as
                                            # well, though... Test for that? )
    # (make sure the only staff user is the superuser in the db currently, then 
    #   ./manage.py dumpdata auth.User --indent=2 > test_staff_superuser.json )
    
    # todo - finalize fixture, bye bye above
    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

    def setUp(self):
        """ Start up Selenium WebDriver browser instance """
        print colored("\nTestCase RenameLaterFunctionalTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green")

        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)  # tells webdriver to use a max timeout of 3 seconds

    def tearDown(self):
        """ Shut down Selenium WebDriver browser instance """
        print colored("\n(tearing down - quit browser after every test)", "green")
        self.browser.quit()


   # def test_can_get_to_login_screen_and_log_in(self):
    def test_can_do_stuff_in_browser(self):
        """ """
        print colored("\tDoes user see the login screen when going to /lockadmin; able to log in; see the right stuff on the following screen; <........> ?", "blue")

        print colored("\tOpening browser to get to the log in screen at /lockadmin.......", "cyan")
        # todo:  learn more about live_server_url
        self.browser.get(self.live_server_url + '/lockadmin') # user opens web browser; goes to main admin page

        print colored("\tDoes it say RFID Lock Administration?", "blue")
        login_page_body = self.browser.find_element_by_tag_name('body') # returns WebElement object
        self.assertIn("RFID Lock Administration", login_page_body.text)  # .text strips out the HTML markup

        print colored("\tCan user actually log in via website?", "blue")
        # The user "test" was created when we loaded the fixture test_staff_user.json
        # User types in username and password and hits return
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('test')
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('test')
        password_field.send_keys(Keys.RETURN)

        # todo:  the welcome text has changed (top nav bar); also, don't hardcode in the user name
        #  see docstring below 
        print colored("\tAfter username and password accepted, is the user taken to the admin page", "blue")
        base_page_body = self.browser.find_element_by_tag_name('body')
        # todo: change
        #  see docstring below 
        self.assertIn("Welcome, test. Change password / Log out", base_page_body.text)
        # now we can check if top header nav contains "Logged in as staff_user_1" if that's the staff user's login
        # base below on this... note the two imp lines
        """
        <div id="navbarRow" class="row"> 
            <!--  LINE BELOW IMPORTANT!!!! -->
            <a class="brand" href="/lock/">RFID Lock Administration</a>
            <form class="navbar-search pull-right" action="">
                <ul class="nav">
                <!--  LINE BELOW IMPORTANT!!!! -->
                <li><p class="navbar-text pull-right">Logged in as staff_user_1 </p> </li>
                <li><a href="/lockadmin/password_change/">Change password</a> </li>
                <li><a href="/lockadmin/logout/">Log out</a></li>
                </ul>
            </form>
        </div>
                                                                                                       
        """
        # todo: change
        print colored("\tDoes user see the links in the top navigation bar?","blue")
        base_page_body = self.browser.find_element_by_tag_name('body')
        self.assertIn("main | lock users | door locks | access logs | staff users", base_page_body.text)

        
        # To do -- does user see the other links...
        # print colored("Does user see the links in the top navigation bar?","magenta")
        # base_page_links = self.browser.find_elements_by_link_text('blah blah blah')
        # self.assertEqual(blah blah blah)


    def test_lockuser_change_form(self):
        """ """
        # make sure this staff user exists? 
        #
        # # and what about logging in !!!!!
        # make sure the lockuser with pk 1 exists  (?)

        print colored("\tOpening browser to get to lockuser's change_form.......", "cyan")
        self.browser.get(self.live_server_url + '/lockadmin/djock_app/lockuser/1')

        print colored("\tThis is a change form, and for the right user?", "blue")
        # so to test this: check that in div with id="main-form",
        #   - the first thing is: '<h2> Lock user / keycard assignment </h2>'
        #   - the various form fields that are filled in reflect the attributes for the LockUser whose pk is in the url
       
        self.assertFalse('still to do!')



    # to do 
    def test_can_create_new_lockuser_via_admin_site(self):
        """ """
        print colored("\tCan user create a new LockUser using the site?", "blue")
        # to do:  now create a LockUser, using the site, not like the unit tests below
        self.fail("not done yet...")

    # to do 
    def test_can_create_new_door_via_admin_site(self):
        """ """
        print colored("\tCan user create a new Door using the site?", "blue")
        # to do:  now create a LockUser, using the site, not like the unit tests below
        self.fail("not done yet...  same thing for the other Models")



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

    """
    def SetUp(self):
        print colored("\nTestCase RenameLaterFunctionalTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green")

    def TearDown(self):
        pass

