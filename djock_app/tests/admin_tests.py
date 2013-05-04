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

# todo:  a number of tests


class LockUserFormTests(TestCase):

    def setUp(self):
        print colored("\nTestCase LockUserFormTests", "white","on_green")
        print colored(self._testMethodName + ": " + self._testMethodDoc, "green") 

    def tearDown(self):
        pass

    """
    def test__init__(self):
        """ """
        pass
    """

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

        def setUp(self):
            print colored("\nTestCase LockUserAdminTests", "white","on_green")
            print colored(self._testMethodName + ": " + self._testMethodDoc, "green") 

        def tearDown(self):
            pass

        def test_get_form(self):
            """ """
            pass

        def test_deactivate(self):
            """ """
            pass

        def test_email_selected(self):
            """ """
            pass

        def test__doors_heading(self):
            """ """
            pass

        def test__last_access_heading(self):
            """ """
            pass

        def test__current_rfid_heading(self):
            """ """
            pass

        def test_formfield_for_foreignkey(self):
            """ """
            pass

        def test_formfield_for_manytomany(self):
            """ """
            pass

        def test_get_doors_to_show(self):
            """ """
            pass

        def test_get_other_doors(self):
            """ """
            pass

        def test_change_view(self):
            """ """
            pass

        def test_save_model(self):
            """ """
            pass

class AccessTimeAdminTests(TestCase):

        def setUp(self):
            print colored("\nTestCase LockUserFormTests", "white","on_green")
            print colored(self._testMethodName + ": " + self._testMethodDoc, "green") 

        def tearDown(self):
            pass

        def test___init__(self):
            """ """
            pass

        def test_changelist_view(self):
            """ """
            pass

        def test__lockuser_html_heading(self):
            """ """
            pass

        def test_has_delete_permission(self):
            """ """
            pass

        def test_has_add_permission(self):
            """ """
            pass
