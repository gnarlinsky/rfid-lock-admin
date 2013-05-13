from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from termcolor import colored
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rfid_lock_management.models import RFIDkeycard, LockUser, Door, AccessTime

class StaffUserTests(TestCase):
    def setUp(self):
        print colored("\nTestCase StaffUserTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") 
        # Note: can also get additional information by setting  verbosity=2 with manage.py

        print colored("Creating staff user......","cyan")
        self.staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')

        print colored("logging in as staff user....","cyan")
        self.client = Client()
        self.client.login(username='johnny_staff',password='my_password')

    def tearDown(self):
        self.staff_only_user.delete()

    # - when active staff users add/update a lock user they should only see doors
    #   for which they themselves have permissions
    def test_staff_only_user_can_only_see_doors_they_have_permission_for(self):
        """ 
        Check that staff users can only see the doors they have permission to see. 
        """
        print colored("\tAssign permissions (only superuser should be able to).......", "cyan") # todo: doing this as superuser? 
        perm_codename = "some_permission_x"
        perm_name = "Permission Number X"
      
        # Create the permission object:
        content_type = ContentType.objects.get(app_label='rfid_lock_management', model='lockuser')
        perm = Permission.objects.create(codename=perm_codename, name=perm_name, content_type=content_type)

        print colored("\tTesting whether user has the permission already (should not)", "blue")
        self.assertFalse(self.staff_only_user.has_perm(perm_codename))

        # now add the permission
        self.staff_only_user.user_permissions.add(perm)
        # Django does cache user permissions, so refetch user from the database (http://stackoverflow.com/a/10103291)
        self.staff_only_user = User.objects.get(pk=self.staff_only_user.pk)  # should now have the assigned permission

        print colored("\tTesting whether user has the permission now", "blue")
        #self.assertTrue(self.staff_only_user.has_perm(perm_codename), self.staff_only_user.profile)  
        self.assertTrue(self.staff_only_user.has_perm('rfid_lock_management.'+perm_codename))  
