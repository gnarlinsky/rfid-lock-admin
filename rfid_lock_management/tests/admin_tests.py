from django import forms


from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.contrib import admin
from django.forms import CheckboxSelectMultiple, ModelForm
from django.db import models
from rfid_lock_management.models import LockUser, AccessTime
from rfid_lock_management.admin import LockUserAdmin, AccessTimeAdmin
from django.contrib.admin.sites import AdminSite
from django.http import HttpResponsePermanentRedirect
from test_helpers import t_info


class LockUserAdminActionsTests(TestCase):
    fixtures = ['initial.json']

    def setUp(self):
        t_info("TestCase LockUserAdminActionsTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)
        self.client = Client()
        self.client.login(username='moe', password='moe')

    def tearDown(self):
        pass

    def test_deactivate(self):
        """
        Deactivating selected lock users (admin action)
        """
        response = self.client.get("/lockadmin/rfid_lock_management/lockuser/")
        request = response.context['request']

        # deactivate all LockUsers
        lua = LockUserAdmin(LockUser, AdminSite())
        queryset = LockUser.objects.all()
        lua.deactivate(request, queryset)

        # Issue #x
        self.assertTrue(LockUser.objects.get(pk=1).is_active())
        self.assertTrue(LockUser.objects.get(pk=2).is_active())
        # In the fixture, only one LockUser (id 3) is not permitted the same
        # doors that the staff user is not permitted, so only LockUser 3 would
        # be deactivated if all are selected.
        self.assertFalse(LockUser.objects.get(pk=3).is_active())


class AccessTimeAdminTests(TestCase):
    fixtures = ['initial.json']

    def setUp(self):
        t_info("TestCase AccessTimeAdminTests", 1)
        t_info(self._testMethodName + ": " + self._testMethodDoc, 2)
        self.client = Client()
        self.client.login(username='moe', password='moe')

    def tearDown(self):
        pass

    def test_change_form_redirection(self):
        """
        Check that if we try to go to an individual Access Time object's change
        form, we're redirected back to the change list.
        """
        # follow=False: prevent from following the redirect and actually
        # loading the next url
        response = self.client.get(
            "/lockadmin/rfid_lock_management/accesstime/1/", follow=False)
        self.assertRedirects(response,
            '/lockadmin/rfid_lock_management/accesstime/')

    def test_lockuser_html_heading(self):
        """
        Does the AccessTime change list page display LockUsers as links to
        their change pages?
        """
        ata = AccessTimeAdmin(AccessTime, AdminSite())
        all_at = AccessTime.objects.all()
        some_at = all_at[0:10]

        # using the actual method
        for at in some_at:
            compare_string = "<a href='../lockuser/%d/'>%s</a>" % (
                at.lockuser.id, at.lockuser)
            self.assertEqual(ata.lockuser_html_heading(at), compare_string)

        # looking at the page, i.e. more functional
        response = self.client.get(
            "/lockadmin/rfid_lock_management/accesstime/")
        for lu in LockUser.objects.all():
            if lu.get_last_access_time():
                link = "<a href='../lockuser/%d/'>%s</a>" % (lu.id, lu)
                self.assertIn(link, response.content)
