from django.test import TestCase
from rfid_lock_management.templatetags import custom_filters
from django.contrib.contenttypes.models import ContentType
from rfid_lock_management.models import RFIDkeycard, LockUser, Door
from test_helpers import t_info

class TemplateTagsTests(TestCase):

    def setUp(self):
	    t_info("TestCase NewKeycardScanTests", 1)
	    t_info(self._testMethodName + ": " + self._testMethodDoc, 2)  

    def test_get_object_type(self):
        """
        Test that get_object_type custom filter returns the object.
        """
        t_info("Correct content types for models?", 4)
        lu_ct = ContentType.objects.get(model__iexact=LockUser.__name__)
        self.assertEqual(custom_filters.get_object_type(lu_ct.pk), 
            LockUser.__name__.lower())

        rf_ct = ContentType.objects.get(model__iexact=RFIDkeycard.__name__)
        self.assertEqual(custom_filters.get_object_type(rf_ct.pk),
            RFIDkeycard.__name__.lower())

        door_ct = ContentType.objects.get(model__iexact=Door.__name__)
        self.assertEqual(custom_filters.get_object_type(door_ct.pk),
            Door.__name__.lower())

        # Obj pk that is greater than count of objects: result will have to be
        # None
        fake_pk = len(ContentType.objects.all())
        self.assertEqual(custom_filters.get_object_type(fake_pk + 1), None)
