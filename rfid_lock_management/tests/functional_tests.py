from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.sites import AdminSite
from rfid_lock_management.admin import LockUserAdmin
from rfid_lock_management.models import LockUser
from test_helpers import t_info


class AccessTimeList(LiveServerTestCase):
    fixtures = ['initial.json']

    def setUp(self):
        """ Start up Selenium WebDriver browser instance """
        t_info("LiveServerTestCase GeneralFunctionalTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)

        # set up browser
        self.browser = webdriver.Firefox()
        # tells webdriver to use a max timeout of 3 seconds
        self.browser.implicitly_wait(3)

        # open browser and log in
        t_info("Opening browser to get to lockuser's change_form (login first)...", 3)
        self.browser.get(self.live_server_url + '/lockadmin')
        self.browser.maximize_window()

        t_info("But login first..........", 3)
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('moe')
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('moe')
        password_field.send_keys(Keys.RETURN)

    def tearDown(self):
        """ Shut down Selenium WebDriver browser instance """
        self.browser.quit()

    def test_access_time_change_list(self):
        """ """
        # Issue #y (client vs browser.get)
        t_info("Opening browser to get to room access log page......", 3)
        self.browser.get(self.live_server_url +
            '/lockadmin/rfid_lock_management/accesstime/')
        self.browser.maximize_window()

        t_info("logging in as staff user....", 3)
        client = Client()
        client.login(username='moe', password='moe')
        response = client.get("/lockadmin/rfid_lock_management/accesstime/")

        t_info("Are we on the change list for access times? Check "
               "template and title.", 4)
        self.assertTemplateUsed(response,
            'admin/rfid_lock_management/change_list.html')
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text,
            'Room access log | RFID Lock Administration')

        t_info("Does user see listed the doors they are allowed to manage in "
               "top navigation bar?", 4)
        # in pk order
        navbar_doors = "Doors you manage: Community Theater, Seminar Room"
        base_page_body = self.browser.find_element_by_tag_name('body')
        self.assertIn(navbar_doors, base_page_body.text)


class GeneralFunctionalTests(LiveServerTestCase):
    fixtures = ['initial.json']

    def setUp(self):
        """
        Start up Selenium WebDriver browser instance
        """
        t_info("LiveServerTestCase GeneralFunctionalTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)

        # set up browser
        self.browser = webdriver.Firefox()
        # tells webdriver to use a max timeout of 3 seconds
        self.browser.implicitly_wait(3)

        t_info("Opening browser to login first.......", 3)
        # user opens web browser; goes to main admin page
        self.browser.get(self.live_server_url + '/lockadmin')
        self.browser.maximize_window()
        t_info("But login first..........", 3)
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('moe')
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('moe')
        password_field.send_keys(Keys.RETURN)

    def tearDown(self):
        """
        Shut down Selenium WebDriver browser instance
        """
        self.browser.quit()

    def test_no_delete_button_lockuser_change_form(self):
        """
        Check that staff users do not see a 'delete' button/link on the form
        page for an individual Lock User. (This is for an existing LockUser --
        when *adding* a LockUser there would not be a 'delete' link/button in
        any case.)
        """
        object_id = 2
        self.browser.get(self.live_server_url +
            '/lockadmin/rfid_lock_management/lockuser/%d' % object_id)
        self.browser.maximize_window()

        # Now check whether the Delete link is there
        # Issue #z
        self.assertRaises(NoSuchElementException, 
            lambda: self.browser.find_element_by_class_name('deletelink-box'))
        # Note - lambda because something like
        #    self.assertRaises(NoSuchElementException,
        #       self.browser.find_element_by_class_name('deletelink-box'))
        # will not work, because gathers the statements at collection time and
        # will error then, not at testing time.

    def test_lockuser_change_form(self):
        """
        Is this the change_form for the right lock user?
        """
        # will be looking at change form for this lockuser
        object_id = 2
        lockuser = LockUser.objects.get(pk=object_id)

        t_info("Opening browser to get to lockuser's change_form.......", 3)
        # Issue #y
        self.browser.get(self.live_server_url +
            '/lockadmin/rfid_lock_management/lockuser/%d' % object_id)
        self.browser.maximize_window()

        # Non-form-field things
        t_info("check that in div with id='main_form', the first/only "
               "h2 tag text is: '<h2> Lock user/keycard assignment</h2>", 4)
        main_form_div = self.browser.find_element_by_id('main_form')
        first_h2 = main_form_div.find_element_by_tag_name('h2')
        self.assertEqual(first_h2.text, "Lock user / keycard assignment")

        # Check the form fields
        t_info("Check that various form fields that are filled in reflect "
               "the attributes for the LockUser whose pk is in the url.", 4)

        t_info("Is the staff user able to see - but not interact with - the "
               "doors that this lock user has access to, but the staff user "
               "does not?", 5)

        # create LockUserAdmin object so we can get other doors
        lua = LockUserAdmin(LockUser, AdminSite())

        client = Client()
        client.login(username='moe', password='moe')
        response = client.get(
            "/lockadmin/rfid_lock_management/lockuser/%d/" % object_id)
        request = response.context['request']
        actual_other_doors = lua.get_other_doors(request, object_id)
        door_names = [door.name for door in list(actual_other_doors)]
        # get the other doors as page displays them
        actual_other_doors_str = ", ".join(door_names)
        field = self.browser.find_element_by_id('other_doors')
        self.assertEqual(field.text, actual_other_doors_str)
        # test that we see the same thing the admin function would return
        # Issue #x
        #    (Here specifically: alternative -  hardcode actual_doors_str, i.e.
        #    actual_other_doors_str = "Space 1 Space 4"  )

        t_info("Comparing the value of the relevant text input field "
               "with the lockuser's actual email.", 4)

        field = self.browser.find_element_by_name('email')
        self.assertEqual(field.get_attribute('value'), lockuser.email)

        field = self.browser.find_element_by_name('first_name')
        self.assertEqual(field.get_attribute('value'), lockuser.first_name)

        field = self.browser.find_element_by_name('last_name')
        self.assertEqual(field.get_attribute('value'), lockuser.last_name)

        field = self.browser.find_element_by_name('address')
        self.assertEqual(field.get_attribute('value'), lockuser.address)

        field = self.browser.find_element_by_name('phone_number')
        self.assertEqual(field.get_attribute('value'), lockuser.phone_number)

        field = self.browser.find_element_by_name('phone_number')
        self.assertEqual(field.get_attribute('value'), lockuser.phone_number)

        doors_pk_tuples = lockuser.doors.values_list('pk')
        # make list of str, not list of tuples
        doors_pk_list = [t[0] for t in doors_pk_tuples]

        door_checkboxes = self.browser.find_elements_by_css_selector(
            "input[name='doors']")
        for door_checkbox in door_checkboxes:
            if door_checkbox.is_selected():
                self.assertIn(
                    int(door_checkbox.get_attribute('value')), doors_pk_list)

        deact_checkbox = self.browser.find_element_by_css_selector(
            "input[id='id_deactivate_current_keycard']")
        self.assertEqual(deact_checkbox.is_selected(),
            lockuser.deactivate_current_keycard)

        current_rfid_field = self.browser.find_element_by_css_selector(
            '.form-row.field-prettify_get_current_rfid')
        current_rfid_field = current_rfid_field.find_element_by_tag_name('p')
        self.assertEqual(current_rfid_field.text,
            lockuser.prettify_get_current_rfid())

        last_access_time_field = self.browser.find_element_by_css_selector(
            '.form-row.field-last_access_time_and_door_and_link_to_more')
        last_access_field = last_access_time_field.find_element_by_tag_name(
            'p')
        self.assertIn(lockuser.prettify_get_last_access_time(),
            last_access_time_field.text)

    def test_keycard_deactivation_but_some_doors_permitted(self):
        """ Tests is the situation where the lock user is permitted access to
        some door(s), but not the one(s) the staff user is allowed access to.
        That is, on the change form, there will be no checked Door(s), so
        checking 'Deactive keycard' should not deactivate the keycard.
        """
        t_info("Opening browser to get to lockuser's change_form.......", 3)
        lockuser_id = 1
        # in fixture, lock user 1  assigned a keycard and is permitted Space 1
        # and Space 4 access; the logged in staff user is not permitted access
        # to either of those.
        self.browser.get(self.live_server_url +
             '/lockadmin/rfid_lock_management/lockuser/%d' % lockuser_id)
        self.browser.maximize_window()

        # Issue #a
        # possibly redundant double checking.....
        t_info("Before any changes / saving, 'Current RFID' should be"
               "something (but not None and not nothing)", 4)
        # current_rfid_field = self.browser.find_element_by_class_name(
        #   'form-row field-prettify_get_current_rfid')
        # Note: above throws WebDriverException: Message: u'Compound class
        # names not permitted'
        current_rfid_field = self.browser.find_element_by_css_selector(
            '.form-row.field-prettify_get_current_rfid')
        current_rfid_field = current_rfid_field.find_element_by_tag_name('p')
        self.assertNotEqual(current_rfid_field.text, 'None')

        # strip out whitespace in case template formatting introduces extra
        # white space
        current_rfid_no_ws = ''.join(current_rfid_field.text.split())
        self.assertTrue(current_rfid_no_ws)

        # a key difference between this test and test_keycard_deactivation
        t_info("Check that no doors are selected", 4)
        door_checkboxes = self.browser.find_elements_by_css_selector(
            "input[name='doors']")
        door_checkbox_statuses = [door_checkbox.is_selected()
                                  for door_checkbox in door_checkboxes]
        self.assertFalse(any(door_checkbox_statuses))

        t_info("Find the 'Deactivate keycard' checkbox and verify it's "
               "not checked", 4)
        deact_checkbox = self.browser.find_element_by_css_selector(
            "input[id='id_deactivate_current_keycard']")
        self.assertFalse(deact_checkbox.is_selected())

        # a key difference between this test and test_keycard_deactivation
        t_info("Find the other doors text and verify there is at least "
               "one door listed", 4)

        other_doors_field = self.browser.find_element_by_id('other_doors')

        # Stripping out whitespace in case template formatting introduces extra
        # white space
        other_doors_text = other_doors_field.text
        other_doors_no_ws = ''.join(other_doors_text.split())
        self.assertTrue(other_doors_no_ws)

        t_info("Check the 'Deactivate keycard' checkbox", 3)
        deact_checkbox.click()

        t_info("Find and click 'Save'", 3)
        save_button = self.browser.find_element_by_css_selector(
            "input[value='Save']")
        save_button.click()

        t_info("Are we back on the change list?", 4)
        # check change list title
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text,
            'Manage lock users | RFID Lock Administration')

        t_info("Back on change list, change message(s) correct", 4)
        test_lockuser = LockUser.objects.get(pk=lockuser_id)
        message1 = 'The lock user "%s %s" was changed successfully.' % (
            test_lockuser.first_name, test_lockuser.last_name)

        # message 2: a key difference between this test and
        # test_keycard_deactivation
        # message2 = "%s % s's keycard was not deactivated because you do not
        #    have permission to manage % s.".format(test_lockuser.first_name,
        #    test_lockuser.last_name, other_doors_text)
        message2 = ("{} {}'s keycard was not deactivated because you do not "
                    "have permission to manage {}.").format(
                        test_lockuser.first_name,
                        test_lockuser.last_name,
                        other_doors_text
                    )

        # todo:  note that using earlier result from body of change
        # form to compare with messages on change list...
        info_messages_elements = self.browser.find_elements_by_class_name(
            'info')
        info_messages = [mess.text for mess in info_messages_elements]
        self.assertIn(message1, info_messages)
        self.assertIn(message2, info_messages)

        # a key difference between this test and test_keycard_deactivation
        t_info("Back on change list, lockuser should still have "
               "keycard(active: True).", 4)

        rows = self.browser.find_elements_by_tag_name('tr')
        rows_text = [row.text for row in rows]

        # implicitly joining long string
        burns_row = ('C. M. Burns mr.burns@springfieldnuclearpowerplant.com '
                    'True RFID: 1122135122 (activated on April 10, 2013, 12:52'
                    ' AM by superuser) Springfield Mafia Secret Meeting Room, '
                    'Junior Achievers Club April 10, 2013, 12:57 AM '
                    '(Springfield ' 'Mafia Secret Meeting Room)')
        self.assertIn(burns_row, rows_text)

        t_info("Hit back to go back to the change form", 3)
        self.browser.back()

        t_info("Are we back on the change form?", 4)
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text,
            'Change lock user | RFID Lock Administration')

        # a key difference between this test and test_keycard_deactivation
        t_info("Back on change form, 'Current RFID' should not be "
               "None, still have the RFID keycard info", 4)
        current_rfid_field = self.browser.find_element_by_css_selector(
            '.form-row.field-prettify_get_current_rfid')
        current_rfid = current_rfid_field.find_element_by_tag_name('p')
        current_rfid_no_ws = ''.join(current_rfid_field.text.split())
        self.assertTrue(current_rfid_no_ws)
        self.assertNotEqual(current_rfid_field.text, 'None')

        t_info("Back on change form, 'Deactivate current keycard' "
               "SHOULD be checked", 4)
        deact_checkbox = self.browser.find_element_by_css_selector(
            "input[id='id_deactivate_current_keycard']")
        self.assertTrue(deact_checkbox.is_selected())

    def test_keycard_deactivation(self):
        """
        Change form for an active (i.e. has assigned keycard) lock user: after
        checking 'Deactivate current keycard' and saving, does the change list
        show the deactivation/saved message? Does the change list show this
        lockuser as inactive? Back on the change form, there should not be an
        assigned keycard (Current RFID: None) and 'Deactivate current keycard'
        should be unchecked.
        """
        t_info("Opening browser to get to lockuser's change_form.......", 3)
        lockuser_id = 3
        self.browser.get(self.live_server_url +
             '/lockadmin/rfid_lock_management/lockuser/%d' % lockuser_id)
        self.browser.maximize_window()

        # Issue #a
        t_info("Before any changes / saving, 'Current RFID' should be "
               "something", 4)
        current_rfid_field = self.browser.find_element_by_css_selector(
            '.form-row.field-prettify_get_current_rfid')
        current_rfid_field = current_rfid_field.find_element_by_tag_name('p')
        self.assertNotEqual(current_rfid_field.text, 'None')

        # strip out whitespace in case template formatting introduces extra
        # white space
        current_rfid_no_ws = ''.join(current_rfid_field.text.split())
        self.assertTrue(current_rfid_no_ws)
        self.assertNotEqual(current_rfid_field.text, 'None')

        t_info("Find the 'Deactivate keycard' checkbox and verify it's "
               "not checked", 4)
        deact_checkbox = self.browser.find_element_by_css_selector(
            "input[id='id_deactivate_current_keycard']")
        self.assertFalse(deact_checkbox.is_selected())

        t_info("Check the 'Deactivate keycard' checkbox", 3)
        deact_checkbox.click()

        t_info("Find and click 'Save'", 3)
        save_button = self.browser.find_element_by_css_selector(
            "input[value='Save']")
        save_button.click()

        t_info("Are we back on the change form? Check title.", 4)
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text,
            'Manage lock users | RFID Lock Administration')

        t_info("Back on change list, change message(s) correct", 4)
        test_lockuser = LockUser.objects.get(pk=lockuser_id)
        message1 = 'The lock user "%s %s" was changed successfully.' % (
            test_lockuser.first_name, test_lockuser.last_name)
        message2 = "%s %s's keycard was deactivated successfully." % (
            test_lockuser.first_name, test_lockuser.last_name)
        info_messages_elements = self.browser.find_elements_by_class_name(
            'info')
        info_messages = [mess.text for mess in info_messages_elements]
        self.assertIn(message1, info_messages)
        self.assertIn(message2, info_messages)

        t_info("Back on change list, lockuser should no longer have "
               "keycard and active status is now False", 4)
        rows = self.browser.find_elements_by_tag_name('tr')
        rows_text = [row.text for row in rows]

        self.assertIn(
            'Lisa Simpson smartgirl63@yahoo.com False None Community Theater (None)',
            rows_text)

        t_info("Hit back to go back to the change form........", 3)
        self.browser.back()

        t_info("Are we back on the change form? Check title.", 4)
        title = self.browser.find_element_by_tag_name('title')
        self.assertEqual(title.text,
            'Change lock user | RFID Lock Administration')

        t_info("Back on change form, 'Current RFID' should now be None", 4)
        current_rfid_field = self.browser.find_element_by_css_selector(
            '.form-row.field-prettify_get_current_rfid')
        current_rfid = current_rfid_field.find_element_by_tag_name('p')
        self.assertEqual(current_rfid.text, 'None')

        t_info("Back on change form, 'Deactivate current keycard' "
               "SHOULD be checked", 4)
        deact_checkbox = self.browser.find_element_by_css_selector(
            "input[id='id_deactivate_current_keycard']")
        self.assertTrue(deact_checkbox.is_selected())


class LogIn(LiveServerTestCase):
    fixtures = ['initial.json']

    def setUp(self):
        """ Start up Selenium WebDriver browser instance """
        t_info("LiveServerTestCase LogIn", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)

        # set up browser
        self.browser = webdriver.Firefox()
        # tells webdriver to use a max timeout of 3 seconds
        self.browser.implicitly_wait(3)

    def tearDown(self):
        """ Shut down Selenium WebDriver browser instance """
        self.browser.quit()

    def test_can_do_stuff_in_browser(self):
        """ Logging in; making sure correct user and other info displayed """
        t_info("Does user see the login screen when going to /lockadmin; "
               "able to log in; see the right stuff on the following screen?", 4)

        t_info(
            "Opening browser to get to the log in screen at /lockadmin....", 3)
        # user opens web browser; goes to main admin page
        self.browser.get(self.live_server_url + '/lockadmin')
        self.browser.maximize_window()

        t_info("Does it say RFID Lock Administration?", 4)
        # returns WebElement object
        login_page_body = self.browser.find_element_by_tag_name('body')
        # .text strips out the HTML markup
        self.assertIn("RFID Lock Administration", login_page_body.text)

        t_info("Can user actually log in via website?", 4)
        # User types in username and password and hits return
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('moe')
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('moe')
        password_field.send_keys(Keys.RETURN)

        t_info("After username and password accepted, is the user "
               "taken to the main page", 4)
        base_page_body = self.browser.find_element_by_tag_name('body')
        self.assertIn("Logged in as moe", base_page_body.text)

        # todo: Issue #q
        t_info("Does user see main links in the body?", 4)
        base_page_body = self.browser.find_element_by_tag_name('body')
        navbar_links = "Lock users\nRoom access log\nCreate user and assign new keycard"
        self.assertIn(navbar_links, base_page_body.text)

        t_info("Does user see listed the doors they are allowed to "
               "manage in top navigation bar?", 4)
        # in pk order
        navbar_doors = "Doors you manage: Community Theater, Seminar Room"
        self.assertIn(navbar_doors, base_page_body.text)
