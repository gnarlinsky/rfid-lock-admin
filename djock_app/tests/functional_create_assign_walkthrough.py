from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.sites import AdminSite

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

from termcolor import colored
from djock_app.models import RFIDkeycard, LockUser, Door, AccessTime
from djock_app.admin import LockUserAdmin

import time
import os
import shutil


# Take screenshot at certain points (and create dir to store images; also scrolls page to get elements into view)? 
# (Note - uses screencapture, which is OS X only [the results are higher quality than using selenium's save_screenshot])
SCREENSHOTS = True
# note:  -C option captures the cursor on the screen

# Indicate how many seconds to pause at key points to slow down walkthrough.
# Set to 0 to turn off 
# ~.5 for screenshots
SLOWER = .5

# LiveServerTestCase starts up a test web server in a separate thread
class CreateLockUserAssignKeycardWalkthrough(LiveServerTestCase):
    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']


    def setUp(self):
        #################################################################
        # print test info 
        #################################################################
        print colored("\nLiveServerTestCase CreateLockUserAssignKeycardWalkthrough", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green")

        #################################################################
        # Set up browser and mouse
        #################################################################
        self.browser = webdriver.Firefox()
        #self.mouse = ActionChains(self.browser)
        self.browser.implicitly_wait(3)  # tells webdriver to use a max timeout of 3 seconds

        #################################################################
        # Create dir for screenshots (archive existing)
        #################################################################
        if SCREENSHOTS: 
            self.screenshots_dir = self._testMethodName + '___screenshots'
            # just create new directories in os x (note)
            if os.path.exists(self.screenshots_dir):
            #os.rename(self.screenshots_dir, "archive___"+self.screenshots_dir)
                try:
                    if os.path.isdir(self.screenshots_dir):
                        # delete folder
                        shutil.rmtree(self.screenshots_dir)
                    else:
                        # delete file
                        os.remove(self.screenshots_dir)
                except:
                   print "Exception: ",str(sys.exc_info())
            else:
               print "not found: ", self.screenshots_dir
            os.makedirs(self.screenshots_dir)
            

    def tearDown(self):
        """ Shut down Selenium WebDriver browser instance """
        print colored("\n(tearing down)", "green")
        self.browser.quit()


    def test_create_new_lockuser_and_assign_keycard_walkthrough(self):
        """ This is a walkthrough for: adding a lockuser to the system, and assigning a keycard. 
        The sequence of events: 

        Staff user...
        - logs in 
        - (main page loads (currently /lockadmin/djock_app/))
        - clicks 'New user' button
        - (add form loads (/lockadmin/djock_app/lockuser/add/) )
        - fills out all fields 
        - selects a door checkbox 
        - clicks <input type="submit" value="Save and continue editing" name="_continue" class="btn">
        - clicks <input type="button" class="btn" id="add_keycard_button" value="Assign keycard">
        - <to do at this point -- will find_element_by_* find the element below if the enclosing div is not visible, since it itself is not explicitly set to not be visible? Depending on answer, might have to insert new events/checks in here............. >
        - clicks <input type="button" class="btn" id="start_button" value="Scan new card">
        - opens new browser window and goes to address e.g. http://192.168.x.x:port_num/checkdoor//checkrfid (obv use liveserver variable)
        - back to previous window
        - clicks <input type="button" class="btn" id="done_button" value="Done">
        - clicks <input type="submit" value="Save" class="btn" name="_save">
        - (change list loads)
        - * change list table should have the correct line with the lock user's information, status, RFID, etc. *
        """
        # start counter for screenshot file names, which will be numbered sequentially
        if SCREENSHOTS: sc_counter = 0
        
        """
        - logs in 
        """
        self.browser.get(self.live_server_url + '/lockadmin') # user opens web browser; goes to main admin page

        if SCREENSHOTS: sc_counter += 1; time.sleep(SLOWER); os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters

        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys('staff_user_1')
        time.sleep(SLOWER)  
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys('staff_user_1')
        time.sleep(SLOWER)  

        if SCREENSHOTS: sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters

        password_field.send_keys(Keys.RETURN)


        """
        - (main page loads (currently /lockadmin/djock_app/))
        """
        if SCREENSHOTS: sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters


        """
        - clicks 'New user' button
        """
        add_lockuser_button = self.browser.find_element_by_id('new_user_button')
        if SCREENSHOTS: sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters
        add_lockuser_button.click()

        """
        - (lock user add form loads (/lockadmin/djock_app/lockuser/add/) )
        """
        if SCREENSHOTS: sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters
        

        """
        - fills out fields 
        """
        first_name = 'Marge'
        last_name = 'Simpson'
        email = 'marge@yahoo.com'
        phone_number =  2175553223  # todo: str
        address = '742 Evergreen Terrace, Springfield, IL'

        self.browser.find_element_by_name('first_name').send_keys(first_name)
        self.browser.find_element_by_name('last_name').send_keys(last_name)
        self.browser.find_element_by_name('email').send_keys(email)
        self.browser.find_element_by_name('phone_number').send_keys(phone_number)
        self.browser.find_element_by_name('address').send_keys(address)

        if SCREENSHOTS: time.sleep(SLOWER); sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters


        """
        - selects a door checkbox 
        """
        door_checkboxes = self.browser.find_elements_by_css_selector("input[name='doors']")
        door_checkboxes[0].click()
        # scroll to bottom of page (useful for screenshot)
        if SCREENSHOTS: self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")


        """
        - clicks 'Save and continue' 
        """
        save_and_continue_button = self.browser.find_element_by_css_selector("input[value='Save and continue editing']")
        save_and_continue_button.click()
        # scroll to bottom of page (useful for screenshot)
        if SCREENSHOTS: self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if SCREENSHOTS: sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters


        """
        - clicks 'Assign keycard' 
        """
        assign_keycard_button = self.browser.find_element_by_css_selector("input[value='Assign keycard']")
        assign_keycard_button.click()
        # scroll to bottom of page (useful for screenshot)
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if SCREENSHOTS: time.sleep(SLOWER); sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters


        """
        - clicks 'Scan new card'
        """
        scan_new_card_button = self.browser.find_element_by_css_selector("input[value='Scan new card']")
        scan_new_card_button.click()
        if SCREENSHOTS: time.sleep(SLOWER); sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters

        
        """
        - opens new browser window and goes to address e.g. http://192.168.x.x:port_num/checkdoor/<door id>/checkrfid/<rfid>
        """
        rfid = 'abcde12345'
        scan_keycard_url = self.live_server_url + '/checkdoor/1/checkrfid/' + rfid
        # ... Actually, opening another browser instance, because dealing with selenium windows is getting ridiculous
        browser2 =  webdriver.Firefox()
        browser2.get(scan_keycard_url)
        if SCREENSHOTS: time.sleep(SLOWER); sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters
        browser2.quit()

        
        """
        - back to previous window
        """
        if SCREENSHOTS: time.sleep(SLOWER); sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters


        """
        - clicks 'Done'
        """
        done_button = self.browser.find_element_by_css_selector("input[value='Done']")
        done_button.click()


        """
        - clicks 'Save'
        """
        save_button = self.browser.find_element_by_css_selector("input[value='Save']")
        save_button.click()

        """
        - (change list loads)
        """
        if SCREENSHOTS: time.sleep(SLOWER); sc_counter += 1; os.system('screencapture  %s/%02d.png' % (self.screenshots_dir, sc_counter)) # %02d pads to 2 characters

        """
        - * change list table should have the correct line with the lock user's information, status, RFID, etc. *
        """
        # After saving, one of the rows on the changelist table should now be: 
        rows = self.browser.find_elements_by_tag_name('tr')

        # checking cell by cell, using variables defined at the beginning
        th_cell = rows[1].find_element_by_tag_name('th')   # the second row -- the top row, following the header row -- holds the newly added lock user's information
        self.assertEqual(th_cell.text, first_name) 

        td_cells = rows[1].find_elements_by_tag_name('td')
        self.assertEqual(td_cells[1].text, last_name) 
        self.assertEqual(td_cells[2].text, email) 
        self.assertEqual(td_cells[3].text, 'True')  # is active
        # don't check the "activated on" date in the current RFID cell, but check other info
        self.assertIn('staff_user_1', td_cells[4].text)
        self.assertIn(rfid, td_cells[4].text)
        self.assertEqual(td_cells[5].text, 'Space 2') 
        self.assertEqual(td_cells[6].text, 'None')
