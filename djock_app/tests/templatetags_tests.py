from django.test import TestCase
from djock_app.models import RFIDkeycard, LockUser, Door, AccessTime, NewKeycardScan
from termcolor import colored
from djock_app.templatetags import custom_filters
from django.contrib.contenttypes.models import ContentType 


"""
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test.client import Client
import simplejson
from datetime import datetime, timedelta
from django.utils.timezone import utc
from djock_app.misc import get_arg_default
"""

#        print colored("\nTestCase ChartifyTests", "white", "on_green")
     
class TemplateTagsTests(TestCase):
    def setUp(self):
        print colored("\nTestCase NewKeycardScanTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") # or you could just set verbosity=2 with maa nage.py...
        """
        self.client = Client()

        print colored("Creating staff user doing this......","cyan")
        self.staff_only_user = User.objects.create_user('johnny_staff', 'js@jmail.com', 'my_password')
        # todo:   user tests

        print colored("logging in as staff user....","cyan")
        self.client.login(username='johnny_staff',password='my_password')
        """
        
    def test_get_object_type(self):
        """ """
        # todo....
        # umm testing the test.......

        print colored("\tCorrect content types for models?", "blue")
        lu_ct = ContentType.objects.get(model__iexact=LockUser.__name__)
        self.assertEqual(custom_filters.get_object_type(lu_ct.pk), LockUser.__name__.lower())

        rf_ct = ContentType.objects.get(model__iexact=RFIDkeycard.__name__)
        self.assertEqual(custom_filters.get_object_type(rf_ct.pk), RFIDkeycard.__name__.lower())

        door_ct = ContentType.objects.get(model__iexact=Door.__name__)
        self.assertEqual(custom_filters.get_object_type(door_ct.pk), Door.__name__.lower())

        # obj pk that is greater than count of obj: result will have to be None
        fake_pk = len(ContentType.objects.all())
        print fake_pk
        self.assertEqual(custom_filters.get_object_type(fake_pk+1), None)
