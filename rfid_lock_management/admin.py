from django.contrib import admin
from django.forms import CheckboxSelectMultiple, ModelForm
from django.db import models
from rfid_lock_management.models import LockUser, AccessTime, RFIDkeycard, Door
from termcolor import colored
from django import forms
from django.contrib import messages
#from chartit import DataPool, Chart
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect




class LockUserForm(ModelForm):
    class Meta:
        model = LockUser

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request',None)
        self.obj = kwargs.pop('obj',None)
        self.doors_not_permitted_to_this_staff_user_but_for_lockuser = kwargs.pop('doors_not_permitted_to_this_staff_user_but_for_lockuser',None)

        super(LockUserForm, self).__init__(*args, **kwargs) 

    # todo:  clean_fieldname? (https://docs.djangoproject.com/en/1.1/ref/forms/validation/#ref-forms-validation)
    def clean(self):
        """ If no Doors were selected -- if user is not permitted to access any door 
            -- deactivate associated keycard. 
            If the user is permitted access to doors that the staff user is not permitted access, make sure lockuser still has access to door staff user is not permitted to manage, since those wouldn't be on the form. Also, if 'deactivate current keycard' was checked in this situation, the keycard should NOT actually be revoked, because of those other doors. 
                    (todo)
            """
        super(forms.ModelForm, self).clean()
        # grab the cleaned fields we need
        cleaned_doors = self.cleaned_data.get("doors")
        # .get():  if data not there, returns nothing - vs exception for [] 
        cleaned_deactivate_current_keycard = self.cleaned_data.get("deactivate_current_keycard")

        # If the user is not permitted to access any door, set deactivate_current_keycard to True. Note that
        # we're changing cleaned_data here, not calling deactivate() on the associated RFIDkeycard.
        #if not cleaned_doors and not cleaned_deactivate_current_keycard:
        if not cleaned_doors:
            """
            self.cleaned_data['deactivate_current_keycard'] = True
            """
            if not self.doors_not_permitted_to_this_staff_user_but_for_lockuser:
                self.cleaned_data['deactivate_current_keycard'] = True
            else:  # don't deactivate keycard if no doors checked, because there are still doors lock user can access
                self.cleaned_data['deactivate_current_keycard'] = False

                msg = 'will not deactivate'
                #messages.add_message(self.request, messages.INFO, msg)
                self.cleaned_data['special_message'] = msg

        if self.doors_not_permitted_to_this_staff_user_but_for_lockuser: 
            for item in self.doors_not_permitted_to_this_staff_user_but_for_lockuser:
                if self.cleaned_data['doors']:
                    self.cleaned_data['doors'] = self.cleaned_data['doors'] | Door.objects.filter(pk=item.pk)
                else: 
                    self.cleaned_data['doors'] = Door.objects.filter(pk=item.pk)

        return self.cleaned_data


class LockUserAdmin(admin.ModelAdmin):
    form = LockUserForm
    # display options as checkboxes, not default as selection list
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
        }

    fieldsets = (
            (None, {
                'fields': ( \
                            ('first_name', 'last_name'), \
                            'email',\
                            'phone_number','address', \
                            'prettify_get_current_rfid',\
                            'last_access_time_and_door_and_link_to_more',  \
                            'doors',
                            'deactivate_current_keycard',
                            ),
            }),
        )

    readonly_fields = ("prettify_get_current_rfid", "last_access_time_and_door_and_link_to_more","prettify_get_last_access_time",)  

    list_display_links = ['first_name','last_name']
    list_display = ('first_name','last_name','email',\
                    'is_active',\
                    '_current_rfid_heading',\
                    '_doors_heading',
                    '_last_access_heading',
    )
    list_filter = ('doors',)

    def get_form(self, request, obj=None, **kwargs):
        ModelForm = super(LockUserAdmin, self).get_form(request, obj, **kwargs)
        class ModelFormMetaClass(ModelForm):
            def __new__(cls, *args, **kwargs):
                #kwargs['request'] = request
                # get doors this lockuser can access but staff user cannot, unless creating a new user
                if obj:
                    kwargs['doors_not_permitted_to_this_staff_user_but_for_lockuser'] = self.get_other_doors(request,obj.id)
                return ModelForm(*args, **kwargs)
        return ModelFormMetaClass

    def deactivate(self, request, queryset):
        """ Staff should not have the ability to delete LockUsers, only to 
        DEACTIVATE them. 

        Before deactivating, this checks if the LockUser is permitted doors 
        that the staff user is not.  This would mean that the staff user is 
        not allowed to revoke the keycard, and the lock user would remain active.
        """
        for obj in queryset:
            doors_not_permitted_to_this_staff_user_but_for_lockuser = self.get_other_doors(request,obj.id)
            if not doors_not_permitted_to_this_staff_user_but_for_lockuser:
                obj.deactivate_current_keycard = True
                obj.current_keycard_revoker = request.user
                obj.save()    #otherwise associated keycard won't become deactivated
    deactivate.short_description = "Deactivate selected lock users/keycards"

    # currently disabled -- not until production
    #def email_selected(self, request, queryset):
    #    """ Upon choosing this action, get new screen with field for entering body of email, etc. """
    #   pass
    #email_selected.short_description =  "Email selected lock users (not implemented until production)"

    actions = (deactivate,)

    def _doors_heading(self, obj):
        return obj.prettify_get_allowed_doors()
    _doors_heading.short_description = 'Allowed doors'

    def _last_access_heading(self, obj):
        #return obj.prettify_get_last_access_time()
        return obj.prettify_get_last_access_time_and_door()
    _last_access_heading.short_description = 'Last access'

    def _current_rfid_heading(self, obj):
        return obj.prettify_get_current_rfid()
    _current_rfid_heading.short_description = 'Current RFID'

    # TO DO: refactor these func....
    def get_doors_to_show(self,request):
        #(todo/temp) object_id is currently only used for debugging
        # superuser will always see all doors (doors_to_show)
        if request.user.is_superuser: # pragma: no cover (exclude from coverage report - superuser distinction is a development-only feature)
            return Door.objects.all()
        # otherwise filter on permissions
        doors_to_show = Door.objects.none()  # creates an EmptyQuerySet
        for door in Door.objects.all():
            perm = "rfid_lock_management.can_manage_door_%d" % door.pk   # put in proper format for has_perm
            if request.user.has_perm(perm):
                doors_to_show = doors_to_show | Door.objects.filter(pk=door.pk)  # concatenating QuerySets
        return doors_to_show

    # todo: refactor in terms of this template/admin divide? 
    def get_other_doors(self, request,object_id):
        """ Doors that the staff User is not allowed to administer. In
        change_form template, will get a set of these Door objects from context,
        then check the lockuser_set of each to see if the current lockuser has
        access to it.  
        
        (todo/temp) object_id is currently only used for debugging

        todo: do the check for whether lockuser actually has perms for the non-permitted door here
        """
        if request.user.is_superuser: # pragma: no cover (exclude from coverage report - superuser distinction is a development-only feature)
            # superuser will always see all doors (doors_to_show)
            return None 
        # otherwise filter on permissions
        doors_not_permitted_to_this_staff_user = Door.objects.none()  # creates an EmptyQuerySet
        for door in Door.objects.all():
            perm = "rfid_lock_management.can_manage_door_%d" % door.pk   # put in proper format for has_perm
            if not request.user.has_perm(perm):
                doors_not_permitted_to_this_staff_user = doors_not_permitted_to_this_staff_user | Door.objects.filter(pk=door.pk)  # concatenating QuerySets

        # all elem that are in this set but not the other. i.e. all doors 
        # todo:  no sets please
        # todo:  get/exception or filter or ... 
        this_lu = LockUser.objects.get(pk=object_id)
        ok_for_user_set = set(this_lu.get_allowed_doors())
        not_for_staff_set = set(doors_not_permitted_to_this_staff_user)
        doors_not_permitted_to_this_staff_user_but_for_lockuser = not_for_staff_set.intersection(ok_for_user_set)
        #doors_not_permitted_to_this_staff_user_but_for_lockuser = set(this_lu.get_allowed_doors()).intersection(set(doors_not_permitted_to_this_staff_user))
        return doors_not_permitted_to_this_staff_user_but_for_lockuser

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """  The queryset() method in DoorAdmin restricts a staff user's ability to view/change Doors that they do not have permission for (individual objects and change list).  But on the listdisplay and changeform for LockUsers, staff users can still see Doors  -- and assign them -- that they don't have permission for.  So here, we need to limit the ManyToMany Door field output for the LockUser.  
        """
        if db_field.name == "doors":
            kwargs["queryset"] = self.get_doors_to_show(request)
        return super(LockUserAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
      
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """  LockUser may have access to Doors that the staff user cannot admin;
        this must be accounted for when determining (Javascript) whether to
        disable "Assign keycard" button or select "Deactivate keycard" because
        all Doors have been unchecked.  In change_form template, will get a set
        of these Door objects from context, then check the lockuser_set of each
        to see if the current lockuser has access to it.  """
        extra_context={"doors_not_permitted_to_this_staff_user":self.get_other_doors(request, object_id)}   # todo:  ugh rename var
        return super(LockUserAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def has_delete_permission(self, request, obj=None):
        """ Don't display "delete" button """
        return False

    def save_model(self,request,obj,form,change):
        """ If deactivate current keycard was checked (which may have actually happened in clean, if  no Doors were selected) 
        need to deactivate current keycard.  Doing this
        here rather than models.py because need to attach request.user to the RFIDkeycard object being
        deactivated, to record revoker
        """
        ## todo:  a better way to do this?

       # if obj.deactivate_current_keycard or not obj.doors.exists():  # although deactivate_current_keycard should have been set to true in clean, if no doors
        if obj.deactivate_current_keycard: 
            obj.current_keycard_revoker = request.user
            msg = "%s's keycard was deactivated successfully." % obj
            messages.add_message(request, messages.INFO, msg)
        else:
            obj.current_keycard_revoker = None
            try:
                if form.cleaned_data['special_message'] == 'will not deactivate':
                    # nicer way to print the doors, not "set([<Door: Space 1>])"
                    doors_not_permit = ", ".join(door.name for door in list(form.doors_not_permitted_to_this_staff_user_but_for_lockuser))
                    msg = "%s's keycard was not deactivated because you do not have permission to manage %s." % (obj, doors_not_permit)
                    messages.add_message(request, messages.INFO, msg)
            except KeyError:
                pass
        super(LockUserAdmin, self).save_model(request, obj, form, change)


class AccessTimeAdmin(admin.ModelAdmin):
    list_display = ('access_time','lockuser_html_heading','door')   # if just 'lockuser', won't get html for link... todo: but I think there's an easier way to do this
    actions=None  # don't provide the actions dropdown
    date_hierarchy = 'access_time' # Set date_hierarchy to the name of a DateField or DateTimeField in model, and the
        # change list page will include a date-based drilldown navigation by that field. (i.e. shows months or days or
        # years or whatever at the top)
    list_filter = ('lockuser','door')  # show filters by RFID and active/inactive on the right

    def __init__(self, *args, **kwargs):
        """ Only defining here because simply including
                list_display_links = []
            above does not work; it defaults to linking from items in AccessTime col
        """
        super(AccessTimeAdmin, self).__init__(*args, **kwargs) # todo: is this appropriate here? 

    def changelist_view(self, request, extra_context=None):
        """ Don't show links for any item  """
        # No need to show the link to  page for an individual AccessTime, so no field should link to it.
        self.list_display_links = (None, )
        return super(AccessTimeAdmin, self).changelist_view(request, extra_context=extra_context)

    def change_view(self, request, extra_context=None):
        """ Don't allow access to individual AccessTime objects  """
        # No need to show the link to  page for an individual AccessTime, so no field should link to it...
        # .... but the page can still be accessed, so redirect to change list 
        return HttpResponseRedirect(reverse('admin:rfid_lock_management_accesstime_changelist'))

    def has_delete_permission(self, request, obj=None):
        """ Don't display "delete" button """
        return False

    def has_add_permission(self, request, obj=None):
        """Don't display Save And Add button """
        return False

    def lockuser_html_heading(self, obj):
        """ Returns the HTML with link to lock user's change_form to display on
            the Access Times change list page """
        return "<a href='../lockuser/%d/'>%s</a>" %  (obj.lockuser.id, obj.lockuser)
    lockuser_html_heading.short_description = 'User'
    lockuser_html_heading.allow_tags = True

# Register models
admin.site.register(LockUser,LockUserAdmin)
admin.site.register(AccessTime,AccessTimeAdmin)

# Globally disable deletion of selected objects (i.e this will not be an available action in the Actions dropdown of
# all ModelAdmins/change_list pages.
admin.site.disable_action('delete_selected')
