from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.sites import AdminSite

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from termcolor import colored
from djock_app.models import RFIDkeycard, LockUser, Door, AccessTime
from djock_app.admin import LockUserAdmin



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
        print colored("\nLiveServerTestCase RenameLaterFunctionalTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green")

        #################################################################
        # set up browser
        #################################################################
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)  # tells webdriver to use a max timeout of 3 seconds

        #################################################################
        # open browser and log in
        #################################################################
        print colored("\tOpening browser to get to lockuser's change_form.......", "cyan")
        self.browser.get(self.live_server_url + '/lockadmin') # user opens web browser; goes to main admin page
        print colored("\tBut login first..........", "cyan")
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('staff_user_1')
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('staff_user_1')
        password_field.send_keys(Keys.RETURN)

    def tearDown(self):
        """ Shut down Selenium WebDriver browser instance """
        print colored("\n(tearing down - quit browser after every test)", "green")
        self.browser.quit()

    # todo:  get that _ out of there....
    def test_no_delete_button_lockuser_change_form(self):
        """ Check that staff users do not see a 'delete' button/link on the form page for an individual Lock User. (This is for an existing LockUser -- when *adding* a LockUser there would not be a 'delete' link/button in any case.) """
        

        """ 
        staff_user_1 = User.objects.get(username="staff_user_1")
        print colored("our user: ","white","on_red")
        print staff_user_1.__dict__

        # todo:   this?  or... put browser login code below into setup.....
        client = Client()
        print colored("\tLogging in as staff user via client.login....","cyan")
        return_val = client.login(username=staff_user_1.username, password='staff_user_1')
        print colored("return val ===========>", "white", "on_red")
        print return_val
        """

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
        # todo: is this a better/more intuitive way than the above? 
        self.assertRaises(NoSuchElementException, lambda: self.browser.find_element_by_class_name('deletelink-box'))
        # Note - lambda because something like 
        #    self.assertRaises(NoSuchElementException, self.browser.find_element_by_class_name('deletelink-box'))
        # will not work, because gathers the statements at collection time and will error then, not at testing time.


    def test_lockuser_change_form(self):
        """  Is this the change_form for the right lock user? """
        # make sure this staff user exists? 
        #
        # # and what about logging in !!!!!
        # make sure the lockuser with pk 2 exists  (?)

        fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json',]

        # will be looking at change form for this lockuser 
        object_id = 2
        lockuser = LockUser.objects.get(pk=object_id)

        print colored("\tOpening browser to get to lockuser's change_form.......", "cyan")
        self.browser.get(self.live_server_url + '/lockadmin/djock_app/lockuser/%d' % object_id)


        print colored("logging in as staff user....","cyan")
        client = Client()
        self.client.login(username='staff_user_1',password='staff_user_1')
        response = self.client.get("/lockadmin/djock_app/lockuser/%d/" % object_id)
        request = response.context['request']


        #######################################################################
        # todo: using client here as well as browser.. so logging in two 
        # different ways..but need request, with user.  Better way to do that?
        #######################################################################

        # Login the same user 
        #staff_only_user = User.objects.get(username="staff_user_1")
        #client.login(username='staff_user_1',password='staff_user_1')

        
        #############################################################
        # Non-form-field things
        #############################################################
        # todo:  non-form-field things in separate test?
        print colored("\tcheck that in div with id='main_form', the first/only h2 tag text is: '<h2> Lock user / keycard assignment </h2>", "blue")
        main_form_div = self.browser.find_element_by_id('main_form')
        first_h2 = main_form_div.find_element_by_tag_name('h2')
        self.assertEqual(first_h2.text, "Lock user / keycard assignment")

        #############################################################
        # Check the form fields
        #############################################################
        print colored("\tCheck that various form fields that are filled in reflect the attributes for the LockUser whose pk is in the url:", "blue")

        print colored("\t\tIs the staff user able to see -- but not interact with (not radio button!) -- the doors that this lock user has access to that the staff user doesn't?", "magenta")
        # create LockUserAdmin object so we can get other doors 
        lua = LockUserAdmin(LockUser, AdminSite())

        # now get the other doors as page displays them 
        field = self.browser.find_element_by_id('other_doors')
        actual_other_doors = lua.get_other_doors(request, object_id)
        door_names = [door.name for door in list(actual_other_doors)]
        actual_other_doors_str = ", ".join(door_names)
        self.assertEqual(field.text, actual_other_doors_str) # test that we see the same thing the admin function would return
        # todo:  or hardcode actual_doors_str, i.e. 
        #       actual_other_doors_str = "Space 1 Space 4"
        # ? 
        # (and same questions for other assertions in this test) 
        

        print colored("\t\tComparing the value of the relevant text input field with the lockuser's actual email.", "magenta")
        field = self.browser.find_element_by_name('email')  # yes, find_element_by_name is really useful for form input fields
        self.assertEqual(field.get_attribute('value'), lockuser.email)
        self.fail()   # todo:  same as above for the rest of the fields
        

    def test_keycard_deactivation_but_some_doors_permitted(self):
        """ This is the situation where the lock user is permitted access to some door(s), but not the one(s) the staff user is allowed access to. That is, on the change form, there will be no checked Door(s), so checking 'Deactive keycard' should not deactivate the keycard."""

        print colored("\tOpening browser to get to lockuser's change_form.......", "cyan")
        lockuser_id = 1  
        self.browser.get(self.live_server_url + '/lockadmin/djock_app/lockuser/%d' % lockuser_id)   # in fixture, lock user 1  assigned a keycard and is permitted Space 1 and Space 4 access; the logged in staff user is not permitted access to either of those

        # todo: is it appropriate to have these double-checking things (so checking state BEFORE making the changes that testing)? As in, I don't trust the fixture? Answer applies to other tests as well.......
        print colored("\tBefore any changes/saving, 'Current RFID' should be something (but not None and not nothing)", "blue") # probably pointless double checking.....
        #current_rfid_field = self.browser.find_element_by_class_name('form-row field-prettify_get_current_rfid')
        # above throws WebDriverException: Message: u'Compound class names not permitted' 
        #print colored("************************************"*10, "white", "on_blue")
        #print self.browser.find_element_by_tag_name('body').text
        #print colored("************************************"*10, "white", "on_blue")
        current_rfid_field = self.browser.find_element_by_css_selector('.form-row.field-prettify_get_current_rfid')
        current_rfid_field = current_rfid_field.find_element_by_tag_name('p')
        self.assertNotEqual(current_rfid_field.text, 'None')
        # strip out whitespace in case template formatting introduces extra white space
        current_rfid_no_ws = ''.join(current_rfid_field.text.split())
        self.assertTrue(current_rfid_no_ws)

        # a key difference between this test and _test_keycard_deactivation
        print colored("\tCheck that no doors are selected","blue")
        door_checkboxes = self.browser.find_elements_by_css_selector("input[name='doors']")
        print colored("************************************"*10, "green", "on_white")
        print [ door_checkbox.is_selected() for door_checkbox in door_checkboxes] 
        door_checkbox_statuses = [ door_checkbox.is_selected() for door_checkbox in door_checkboxes]
        self.assertFalse(any(door_checkbox_statuses))
            
        print colored("\tFind the 'Deactivate keycard' checkbox and verify it's not checked", "blue")
        deact_checkbox = self.browser.find_element_by_css_selector("input[id='id_deactivate_current_keycard']")
        self.assertFalse(deact_checkbox.is_selected())


        # >>>>>> not done below here either;..>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        # a key difference between this test and _test_keycard_deactivation
        print colored("\tFind the other doors text and verify there is at least one door listed", "blue")

        # to test that we see the same thing the admin function would return
        # no - just verify that there's something in that field
        #lua = LockUserAdmin(LockUser, AdminSite())
        #actual_other_doors = lua.get_other_doors(request, object_id)
        #door_names = [door.name for door in list(actual_other_doors)]
        #actual_other_doors_str = " ".join(door_names) 

        #other_doors_field = self.browser.find_element_by_id('other_doors')
        #self.assertEqual(other_doors_field.text, actual_other_doors_str) 

        other_doors_field = self.browser.find_element_by_id('other_doors')
        print colored("*"*20, "white", "on_red")
        print colored("  wtf ?????  "*20, "white", "on_red")
        print other_doors_field.text
        print colored("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", "white", "on_red")
        print colored("*"*20, "white", "on_red")

        # note - strip out whitespace in case template formatting introduces extra white space
        other_doors_text = other_doors_field.text
        other_doors_no_ws = ''.join(other_doors_text.split())
        self.assertTrue(other_doors_no_ws)

        print colored("\tCheck the 'Deactivate keycard' checkbox", "cyan")
        deact_checkbox.click()

        print colored("\tFind and click 'Save'", "cyan")
        save_button = self.browser.find_element_by_css_selector("input[value='Save']")
        save_button.click()


        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # stuff below here -- until the '#<<<<<<<<<<<<<<<<<<<<<<<# line --  is just copied from below, so yet to do........ 
        print colored("\tAre we back on the change list?", "blue")
        # todo: template check, rather than looking at elements on the page - meh, no client please
        #self.assertTemplateUsed(response, 'change_list.html')
        # determine change list title
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text, 'Select lock user to change | RFID Lock Administration')

        print colored("\tBack on change list, change message(s) correct", "blue")
        test_lockuser = LockUser.objects.get(pk=lockuser_id)
        # todo: consistent quotes pls
        message1 = 'The lock user "%s %s" was changed successfully.' % (test_lockuser.first_name, test_lockuser.last_name)

        print colored("*"*10+"     locals   " + "*"*10, "white", "on_red")
        print locals()
        print colored("*"*20, "white", "on_red")
        # message 2: a key difference between this test and _test_keycard_deactivation
        print colored("*"*10+"    doors not permit   " + "*"*10, "white", "on_red")
    
        print colored("*"*20, "white", "on_red")
        #print doors_not_permit
        #doors_not_permit = ', '.join(other_doors_text.split(" "))
        #message2 = "%s %s's keycard was not deactivated because you do not have permission to manage %s."\
        #            % (test_lockuser.first_name, test_lockuser.last_name, doors_not_permit)
        message2 = "%s %s's keycard was not deactivated because you do not have permission to manage %s."\
                    % (test_lockuser.first_name, test_lockuser.last_name, other_doors_text)  
                    # todo:  note that using earlier result from body of change form to compare with messages on change list... 

        print colored("*"*10+"     message 2   " + "*"*10, "white", "on_red")

        print message2
        print colored("*"*20, "white", "on_red")

        info_messages_elements = self.browser.find_elements_by_class_name('info')
        info_messages = [mess.text for mess in info_messages_elements]
        self.assertIn(message1, info_messages)
        self.assertIn(message2, info_messages)



        # a key difference between this test and _test_keycard_deactivation
        print colored("\tBack on change list, lockuser should still have keycard (active: True).", "blue")
        rows = self.browser.find_elements_by_tag_name('tr')
        rows_text = [row.text for row in rows]
        self.assertIn('C. M. Burns mr.burns@springfieldnuclearpowerplant.com True RFID: 1122135122 (activated on Wed Apr 10 00:52:00 2013 by superuser) Space 1, Space 4 April 10, 2013, 12:57 AM', rows_text) # todo:  note hardcoded.....  

        print colored("\tHit back to go back to the change form", "cyan")
        self.browser.back()
        # do that

        print colored("\tAre we back on the change form?", "blue")
        # todo: template check, rather than looking at elements on the page - meh, no client please
        #self.assertTemplateUsed(response, 'change_list.html')
        # determine change list title
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text, 'Change lock user | RFID Lock Administration')


        # a key difference between this test and _test_keycard_deactivation
        print colored("\tBack on change form, 'Current RFID' should not be None, still have the RFID keycard info", "blue")
        current_rfid_field = self.browser.find_element_by_css_selector('.form-row.field-prettify_get_current_rfid')
        current_rfid = current_rfid_field.find_element_by_tag_name('p')
        current_rfid_no_ws = ''.join(current_rfid_field.text.split())
        self.assertTrue(current_rfid_no_ws)
        self.assertNotEqual(current_rfid_field.text, 'None')

        print colored("\tBack on change form, 'Deactivate current keycard' SHOULD be checked", "blue")
        deact_checkbox = self.browser.find_element_by_css_selector("input[id='id_deactivate_current_keycard']")
        self.assertTrue(deact_checkbox.is_selected())



    def test_keycard_deactivation(self):
        """  Change form for an active (i.e. has assigned keycard) lock user: 
        after checking 'Deactivate current keycard' and saving, does the change
        list show the deactivation/saved message? Does the change list show this
        lockuser as inactive? Back on the change form, there should not be an 
        assigned keycard (Current RFID: None) and 'Deactivate current keycard'
        should be unchecked.  """


        print colored("\tOpening browser to get to lockuser's change_form.......", "cyan")
        lockuser_id = 3
        self.browser.get(self.live_server_url + '/lockadmin/djock_app/lockuser/%d' % lockuser_id)   # in fixture, lock user 2  assigned a keycard

        # todo: is it appropriate to have these double-checking things (so checking state BEFORE making the changes that testing)? As in, I don't trust the fixture? Answer applies to other tests as well.......
        print colored("\tBefore any changes/saving, 'Current RFID' should be something", "blue") # probably pointless double checking.....
        #current_rfid_field = self.browser.find_element_by_class_name('form-row field-prettify_get_current_rfid')
        # above throws WebDriverException: Message: u'Compound class names not permitted' 
        current_rfid_field = self.browser.find_element_by_css_selector('.form-row.field-prettify_get_current_rfid')
        current_rfid_field = current_rfid_field.find_element_by_tag_name('p')
        self.assertNotEqual(current_rfid_field.text, 'None')

        # strip out whitespace in case template formatting introduces extra white space
        current_rfid_no_ws = ''.join(current_rfid_field.text.split())
        self.assertTrue(current_rfid_no_ws)
        self.assertNotEqual(current_rfid_field.text, 'None')


        print colored("\tFind the 'Deactivate keycard' checkbox and verify it's not checked", "blue")
        deact_checkbox = self.browser.find_element_by_css_selector("input[id='id_deactivate_current_keycard']")
        self.assertFalse(deact_checkbox.is_selected())

        print colored("\tCheck the 'Deactivate keycard' checkbox", "cyan")
        deact_checkbox.click()

        print colored("\tFind and click 'Save'", "cyan")
        save_button = self.browser.find_element_by_css_selector("input[value='Save']")
        save_button.click()

        print colored("\tAre we back on the change list?", "blue")
        # todo: template check, rather than looking at elements on the page - meh, no client please
        #self.assertTemplateUsed(response, 'change_list.html')
        # determine change list title
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text, 'Select lock user to change | RFID Lock Administration')

        print colored("\tBack on change list, change message(s) correct", "blue")
        test_lockuser = LockUser.objects.get(pk=lockuser_id)
        # todo: consistent quotes pls
        message1 = 'The lock user "%s %s" was changed successfully.' % (test_lockuser.first_name, test_lockuser.last_name)
        message2 = "%s %s's keycard was deactivated successfully."  % (test_lockuser.first_name, test_lockuser.last_name)
        info_messages_elements = self.browser.find_elements_by_class_name('info')
        info_messages = [mess.text for mess in info_messages_elements]
        self.assertIn(message1, info_messages)
        self.assertIn(message2, info_messages)



        print colored("\tBack on change list, lockuser should no longer have keycard and active status is now False", "blue")
        rows = self.browser.find_elements_by_tag_name('tr')
        rows_text = [row.text for row in rows]
        print rows_text

        self.assertIn( 'Lisa Simpson smartgirl63@yahoo.com False None Space 2 None', rows_text) # todo:  note hardcoded.....  


        print colored("\tHit back to go back to the change form", "cyan")
        self.browser.back()
        # do that

        print colored("\tAre we back on the change form?", "blue")
        # todo: template check, rather than looking at elements on the page - meh, no client please
        #self.assertTemplateUsed(response, 'change_list.html')
        # determine change list title
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text, 'Change lock user | RFID Lock Administration')

        print colored("\tBack on change form, 'Current RFID' should now be None", "blue")
        current_rfid_field = self.browser.find_element_by_css_selector('.form-row.field-prettify_get_current_rfid')
        current_rfid = current_rfid_field.find_element_by_tag_name('p')
        self.assertEqual(current_rfid.text, 'None')

        print colored("\tBack on change form, 'Deactivate current keycard' SHOULD be checked", "blue")
        deact_checkbox = self.browser.find_element_by_css_selector("input[id='id_deactivate_current_keycard']")
        self.assertTrue(deact_checkbox.is_selected())


    """ Not currently a use case
    def test_can_create_new_door(self):
        """ """
        print colored("\tCan user create a new Door using the site?", "blue")
        # to do:  now create a LockUser, using the site, not like the unit tests below
        self.assertFalse("not done yet...  same thing for the other Models")
    """





class LogIn(LiveServerTestCase):
    # Temp2 --  do NOT login in setUp

    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']
    def setUp(self):
        """ Start up Selenium WebDriver browser instance """
        print colored("\nLiveServerTestCase Temp2", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green")

        #################################################################
        # set up browser
        #################################################################
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
        # The user "test" was created when we loaded the fixture 
        # User types in username and password and hits return
        #################################################################
        print colored("\tOpening browser to get to lockuser's change_form.......", "cyan")
        self.browser.get(self.live_server_url + '/lockadmin/djock_app/lockuser/1')
        print colored("\tBut login first..........", "cyan")
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('staff_user_1')
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('staff_user_1')
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





class RFIDkeycardAssignmentTests(TestCase):
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
        print colored("\nTestCase RFIDkeycardAssignmentTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green")

    def TearDown(self):
        pass

