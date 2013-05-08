from django.test import TestCase
from django.contrib.auth.models import User
from termcolor import colored
from django.test.client import Client
from django.contrib import admin 
from django.forms import CheckboxSelectMultiple, ModelForm 
from django.db import models 
from djock_app.models import LockUser, AccessTime, RFIDkeycard, Door 
from djock_app.admin import LockUserForm, LockUserAdmin, AccessTimeAdmin
from termcolor import colored 
from django import forms 
from django.contrib.admin.sites import AdminSite
from django.http import HttpResponsePermanentRedirect



# todo:  a number of tests


class LockUserFormTests(TestCase):

    def setUp(self):
        print colored("\nTestCase LockUserFormTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") 

    def tearDown(self):
        pass

    # todo: make sure comprehensive
    def test_clean(self):
        """ """
        door1 = Door.objects.create(name='Space 1') 
        door2 = Door.objects.create(name='Space 2')

        print colored("\tNo doors permitted to lockuser, so deactivate keycard", "blue")
        lu_form = LockUserForm() 
        lu_form.cleaned_data = {'doors':[]}
        lu_form.save()
        lu_form.clean()
        # .get():  if data not there, returns nothing - vs exception for [] 
        self.assertTrue(lu_form.cleaned_data.get('deactivate_current_keycard'))

        print colored("\tSome doors permitted to lockuser, same ones as for staff user, so return all of them", "blue")
        lu_form.cleaned_data = {'doors':[door1, door2]}
        lu_form.doors_not_permitted_to_this_staff_user_but_for_lockuser = None
        lu_form.save()
        lu_form.clean()
        self.assertTrue(lu_form.cleaned_data.get('doors'), {'doors':[door1,door2]})

        
        print colored("\tSome doors permitted to lockuser, but one of them not permitted to staff user - make sure same doors permitted to lockuser after save", "blue")
        lu_doors_qs = Door.objects.filter(pk=door1.pk) | Door.objects.filter(pk=door2.pk)
        lu_form.cleaned_data = {'doors': lu_doors_qs } 
        lu_form.doors_not_permitted_to_this_staff_user_but_for_lockuser = Door.objects.filter(pk=door1.pk)
        lu_form.save()

        #################  to do  ###############3#######################
        #super(ModelForm, lu_form).clean()
        #print lu_form.cleaned_data.get('doors')
        #
        #   so the above should NOT be same as below after custom clean()..........
        #   have to create perms and the staff user???
        # 
        ##################################################################
        lu_form.clean()
        self.assertTrue(lu_form.cleaned_data.get('doors'), {'doors':[door1,door2]})


class LockUserAdminTests(TestCase):
    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

    def setUp(self):
        print colored("\nTestCase LockUserAdminTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") 
        self.client = Client()
        self.client.login(username='staff_user_1',password='staff_user_1')

    def tearDown(self):
        pass

    def test_deactivate(self):
        """ Deactiving selected lock users (admin action) """
        response = self.client.get("/lockadmin/djock_app/lockuser/")
        request = response.context['request']

        # deactivate all LockUsers
        lua = LockUserAdmin(LockUser, AdminSite())
        queryset = LockUser.objects.all()
        lua.deactivate(request, queryset)

        # In the fixture, only one LockUser (id 3) is not permitted the same 
        # doors that the staff user is not permitted, so only LockUser 3 would
        # be deactivated if all are selected. 
        self.assertTrue(LockUser.objects.get(pk=1).is_active())
        self.assertTrue(LockUser.objects.get(pk=2).is_active())
        self.assertFalse(LockUser.objects.get(pk=3).is_active())
        # todo:  questions again about how (hard) to code the correct values


class AccessTimeAdminTests(TestCase):
    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

    def setUp(self):
        print colored("\nTestCase AccessTimeAdminTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") 
        self.client = Client()
        self.client.login(username='staff_user_1',password='staff_user_1')

    def tearDown(self):
        pass

    def test_change_form_redirection(self):
        """ Check that if we try to go to an individual Access Time object's change form, we're redirected back to the change list. """

        # follow=False: prevent from following the redirect and actually loading the next url
        response = self.client.get("/lockadmin/djock_app/accesstime/1/", follow=False) 
        self.assertRedirects(response, '/lockadmin/djock_app/accesstime/')





        #client = Client()
        #response = client.get('/lockadmin/djock_app/accesstime/1/')
        response = self.client.get('/lockadmin/djock_app/accesstime/1/')
        #self.assertEqual(response.status_code, 302)
        #self.assertTrue(isinstance(response, HttpResponsePermanentRedirect))
        #self.assertEqual(response.META['HTTP_LOCATION'], '/lockadmin/djock_app/accesstime/')

    def test_lockuser_html_heading(self):
        """ Does the AccessTime change list page display LockUsers as links to their change pages? """
        #response = self.client.get("/lockadmin/djock_app/accesstime/")
        #request = response.context['request']

        ata = AccessTimeAdmin(AccessTime, AdminSite())   

        all_at = AccessTime.objects.all()
        some_at = all_at[0:10]

        # using the actual function
        for at in some_at: 
            compare_string = "<a href='../lockuser/%d/'>%s</a>" %  (at.lockuser.id, at.lockuser)
            self.assertEqual( ata.lockuser_html_heading(at),compare_string)

        # looking at the page, i.e. more functional
        response = self.client.get("/lockadmin/djock_app/accesstime/")
        for lu in LockUser.objects.all():
            if lu.get_last_access_time():
                link = "<a href='../lockuser/%d/'>%s</a>" %  (lu.id, lu)
                self.assertIn(link, response.content)
