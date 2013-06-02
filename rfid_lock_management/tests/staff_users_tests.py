from django.contrib.auth.models import User
from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from test_helpers import t_info


class StaffUserTests(TestCase):

    def setUp(self):
        t_info("TestCase StaffUserTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)
        # Note: can also get additional information by setting  verbosity=2
        # with manage.py. 

        t_info("Creating staff user......", 3)
        self.staff_only_user = User.objects.create_user(
            'johnny_staff', 'js@jmail.com', 'my_password')

        t_info("logging in as staff user....", 3)
        self.client = Client()
        self.client.login(username='johnny_staff', password='my_password')

    def tearDown(self):
        self.staff_only_user.delete()

    # When active staff users add/update a lock user they should only see doors
    # for which they themselves have permissions.
    def test_staff_only_user_can_only_see_doors_they_have_permission_for(self):
        """
        Check that staff users can only see the doors they are permitted to
        manage.
        """
        t_info("Assign permissions (only superuser should be able to)...", 3)
        perm_codename = "some_permission_x"
        perm_name = "Permission Number X"

        # Create the permission object
        content_type = ContentType.objects.get(
            app_label='rfid_lock_management', model='lockuser')
        perm = Permission.objects.create(
            codename=perm_codename, name=perm_name, content_type=content_type)

        t_info("Testing whether user has permission already (should not)", 4)
        self.assertFalse(self.staff_only_user.has_perm(perm_codename))

        # Now add the permission
        self.staff_only_user.user_permissions.add(perm)
        # Django does cache user permissions, so refetch user from the database
        # (http://stackoverflow.com/a/10103291)
        # should now have the assigned permission
        self.staff_only_user = User.objects.get(
            pk=self.staff_only_user.pk)  

        t_info("Testing whether user has the permission now", 4)
        # self.assertTrue(self.staff_only_user.has_perm(perm_codename),
        # self.staff_only_user.profile)
        self.assertTrue(self.staff_only_user.has_perm(
            'rfid_lock_management.' + perm_codename))
