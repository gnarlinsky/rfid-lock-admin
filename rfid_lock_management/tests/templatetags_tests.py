from django.test import TestCase
from rfid_lock_management.models import RFIDkeycard, LockUser, Door, AccessTime, NewKeycardScan
from termcolor import colored
from rfid_lock_management.templatetags import custom_filters
from django.contrib.contenttypes.models import ContentType 


     
class TemplateTagsTests(TestCase):
    def setUp(self):
        print colored("\nTestCase NewKeycardScanTests", "white", "on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") # or you could just set verbosity=2 with maa nage.py...
        
    def test_get_object_type(self):
        """ Test that get_object_type custom filter returns the object """
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
