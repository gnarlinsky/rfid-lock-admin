from django.contrib import admin
from django.forms import CheckboxSelectMultiple, ModelForm
from django.db import models
from djock_app.models import LockUser, AccessTime, RFIDkeycard, Door
from termcolor import colored
from django import forms
from django.contrib import messages
#from chartit import DataPool, Chart
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


#########################  TO DO ##########################################
#  - Get rid of "delete" action for all except superuser, including not showing the button on change_list
# - (maybe?): When a user is modified or added (in terms of being active at all or more/fewer doors access), e-mail all the staff. 
# - search bar for lockusers/accesstimes/doors change lists
# -  # the field labeled "rfids" should not be required.  
###########################################################################



""" Staff user door management is not a current use case
class DoorAdmin(admin.ModelAdmin):
    ###########################################################################
    # Page listing all Doors:
    ###########################################################################
    # # field names to display, as columns
    list_display = ('name','id', 'description', 'get_allowed_lockusers_html_links','get_all_access_times',\
        #'prettify_get_allowed_rfids' \
        )
    actions=None  # don't provide the actions dropdown
    
    ###########################################################################
    # Individual Door page
    ###########################################################################
    readonly_fields = ('get_allowed_lockusers','get_all_access_times')   # because obviously these shouldn't be editable.  
    #(but commenting out if want to create some objects from admin vs shell just for fun)


    # Staff users should only be able to manage doors that they have permissions for

    # This works when the user is looking at the list of Doors (the change list page), 
    # but not when they're displayed on the lock user's change_form, and the user is 
    # able to add/remove any of those. I can restrict stuff template-level here,
    # but that still seems wrong.... ???
    def queryset(self, request):
        if request.user.is_superuser:
            return Door.objects.all()
        # but else if not superuser, is staff, is active: 
        
        doors_to_return = Door.objects.none()  # creates an EmptyQuerySet
        for door in Door.objects.all():
            perm = "djock_app.can_manage_door_%d" % door.pk   # put in proper format for has_perm
            if request.user.has_perm(perm):
                doors_to_return = doors_to_return | Door.objects.filter(pk=door.pk)  # concatenating QuerySets
                # Doing door instead of the filter results in Error: 'Door' object has no attribute '_clone'
                #doors_to_return = doors_to_return | door   # concatenating QuerySets
                
        return doors_to_return


    def has_delete_permission(self, request, obj=None):
        #Don't display "delete" button
        return False

#    def has_add_permission(self, request, obj=None):
#        # Don't display Save And Add button
#        return False


"""


""" has_perm(perm, obj=None) / has_perms(perm_list, obj=None)
        Returns True if the user has the specified permission, where perm is in the format "<app label>.<permission codename>". (see documentation on permissions). If the user is inactive, this method will always return False.

        If obj is passed in, this method won't check for a permission for the model, but for this specific object.
        """
            # permission codenames are named can_manage_door_x, where x is the pk num
        # else... return nothing and/or exception? 

"""
class RFIDkeycardForm(ModelForm):
    #the_rfid = IntegerField(help_text="help text")

    # override __init__ to prepopulate the_rfid field with a random number, just to 
    #   simulate assigning a new card
    def __init__(self, *args, **kwargs):
        super(RFIDkeycardForm, self).__init__(*args, **kwargs)
        new_scan_queryset = NewKeycardScan.objects.all()
        if new_scan_queryset: 
            new_scan = new_scan_queryset.latest("time_initiated")  # get the latest NewKeycardScan object, ordered by the field time_initiated (i.e. time the object was created) 
            self.fields['the_rfid'] = IntegerField(help_text = "(Not a random number -- from door/rfid check request)")
            self.fields['the_rfid'].initial = new_scan.rfid
        else: 
            self.fields['the_rfid'] = IntegerField(help_text = "(This is a random number to simulate getting a new keycard number after it's scanned in.<br>Only superuser can actually see the number.)")
            self.fields['the_rfid'].initial = str(random.randint(0000000000,9999999999)) # rfid's should be 10 char long... just str'ing ints, because I don't want to mess with random crap anymore.
    class Meta:
        model = RFIDkeycard


        
    def save(self,*args,**kwargs):
        try:
            super(RFIDkeycardForm,self).save(*args,**kwargs)
        except IntegrityError:
            # form passed validation, so didn't error there 
            errors = forms.util.ErrorList()
            errors = forms._errors.setdefault(django.forms.forms.NON_FIELD_ERRORS, errors)
            errors.append('Sorry, this RFID already exists.')


    # playing with# trying to override save
#    def save(self, commit=True, force_insert=False, force_update=False, *args, **kwargs):
        # If anything overrides your form, or wants to modify what it's saving,
        # it will do save(commit=False), modify the output, and then save it itself.
#        rfcard = super(RFIDkeycardForm, self).save(commit=False, *args, **kwargs)
        #################################################
        # do my custom stuff - 
        # (rfidkeycard actually will be saved same as always.  But before it does so, I want to actually change the associated lockuser -- just to
        # associate it with this keycard, so that after a page refresh of the original change_form, we
        # should be able to see this change. /save

#        if commit: 
#            rfcard.save()
#        return rfcard
#

"""

# Only superuser/developers can access RFIDkeycard objects from outside LockUser
""" Staff user door management is not a current use case
class RFIDkeycardAdmin(admin.ModelAdmin):
    #form = RFIDkeycardForm # prepopulating with random num

    list_display = ["the_rfid","id", "date_created","date_revoked","is_active", "lockuser",
                    "get_allowed_doors_html_links"]

    ####################################################################################################
    # Individual page (change form)
    ####################################################################################################
    #prepopulated_fields = { 'the_rfid': ('id',)} 
    #fields = ("the_rfid","date_revoked","date_created","id")
    fields = ("the_rfid","lockuser","date_created","date_revoked","get_allowed_doors","is_active")  # here showing fields wouldn't show to a staff user, since the real (not inline) RFIDkeycard change_form would only be visible to superuser.
    readonly_fields = ("the_rfid","deactivate","lockuser","date_created","date_revoked","is_active","get_allowed_doors")

"""

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
        """ If no Door were selected -- if user is not permitted to access any door 
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

                # todo:  eek!  just adding to cleaned_data!
                #msg = "%s's keycard was not deactivated because you do not have permission to manage %s." % (self.obj, self.doors_not_permitted_to_this_staff_user_but_for_lockuser)
                msg = 'will not deactivate'
                #messages.add_message(self.request, messages.INFO, msg)
                self.cleaned_data['special_message'] = msg

        if self.doors_not_permitted_to_this_staff_user_but_for_lockuser: 
            for item in self.doors_not_permitted_to_this_staff_user_but_for_lockuser:
                if self.cleaned_data['doors']:
                    self.cleaned_data['doors'] = self.cleaned_data['doors'] | Door.objects.filter(pk=item.pk)
                else: 
                    self.cleaned_data['doors'] = Door.objects.filter(pk=item.pk)

        # get the id of this door; add to QS
        return self.cleaned_data
        # temp/todo: 
        # testing faking it: 
        #form = form + '<li><label for="id_doors_2"><input checked="checked" type="checkbox" name="doors" value="2" id="id_doors_2" /> Space 1</label></li>'


class LockUserAdmin(admin.ModelAdmin):
    #inlines = [RFIDkeycardInline]
    #form = LockUserForm(request.POST, request=request)
    form = LockUserForm
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


    #def save_form(self,request,form,change):
        #super(LockUserAdmin, self).save_form(request, form, change)
    ####################################################
    # Page listing all LockUsers ("change list" page):
    ####################################################
    #-------------------
    # Actions dropdown
    #------------------
    def deactivate(self, request, queryset):
        """ Staff should not have the ability to delete LockUsers, only to DEACTIVATE them. """
        for obj in queryset:
            doors_not_permitted_to_this_staff_user_but_for_lockuser = self.get_other_doors(request,obj.id)
            if not doors_not_permitted_to_this_staff_user_but_for_lockuser:
                obj.deactivate_current_keycard = True
                obj.current_keycard_revoker = request.user
                obj.save()    #otherwise associated keycard won't become deactivated
    deactivate.short_description = "Deactivate selected lock users/keycards"



    ########  todo:  before doing the pragma thing actually, see :  can i just leave off the 'pass'.... ########    
    # so later insert after the def, if have to: 

    # currently disabled -- not until production
    def email_selected(self, request, queryset):
        """ Upon choosing this action, get new screen with field for entering body of email, etc. """
        #pass
    email_selected.short_description =  "Email selected lock users (not implemented until production)"


    # Only the following actions will be shown in the dropdown
    actions = (deactivate, email_selected)


    #-------------------------
    # Which fields to display
    #-------------------------
    # fields (i.e. column headings)
    # to do:  show deactivated (i.e. no current keycard) in gray, or de-emphasize another way
    list_display = ('first_name','last_name','email',\
                    'is_active',\
                    #'prettify_get_current_rfid',\
                    '_current_rfid_heading',\
                    #'prettify_get_allowed_doors',\
                    '_doors_heading',
                    #'prettify_get_last_access_time',
                    '_last_access_heading',
    )
    readonly_fields = ("prettify_get_current_rfid", "get_all_rfids_html","last_access_time_and_link_to_more","prettify_get_last_access_time",)  

    list_filter = ('doors',)

   #list_display = ('_my_field',)
   #readonly_fields = ('_my_field', )     


    #-------------------------
    # nicer column labels
    #------------------------
    # todo: DRYer? (all of these)

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




    # Only the first and last names  will appear as link to the individual LockUser page
    list_display_links = ['first_name','last_name']

    ####################################################
    # Individual LockUser page  (change form)
    ####################################################

    # Which fields to show, and in what order
    # (parentheses group fields into a single line)
    # to do:  show deactivated (i.e. no current keycard) in gray, or de-emphasize another way
    fieldsets = (
            (None, {
                'fields': ( \
                            ('first_name', 'last_name'), \
                            'email',\
                            'phone_number','address', \
                            # will error if the below are not set as read_only...  which makes sense; these are methods and
                            # things I can't edit from the form.. 
                            'prettify_get_current_rfid',\
                            'last_access_time_and_link_to_more',  \
                            #'is_active', \
                            'doors',
                            'deactivate_current_keycard',
                          #  'rfids',
                            ),

               # 'description': ('description.....  Create/modify new lock user and assign keycard')
            }),
        )


    # display options as checkboxes, not default as selection list
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
        }


    # TO DO: refactor these func....
    def get_doors_to_show(self,request):
        #(todo/temp) object_id is currently only used for debugging
        # superuser will always see all doors (doors_to_show)
        if request.user.is_superuser: # pragma: no cover (exclude from coverage report - superuser distinction is a development-only feature)
            return Door.objects.all()
        # otherwise filter on permissions
        doors_to_show = Door.objects.none()  # creates an EmptyQuerySet
        for door in Door.objects.all():
            perm = "djock_app.can_manage_door_%d" % door.pk   # put in proper format for has_perm
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
        this_lu = LockUser.objects.filter(id=object_id)[0]


        # superuser will always see all doors (doors_to_show)
        if request.user.is_superuser: # pragma: no cover (exclude from coverage report - superuser distinction is a development-only feature)
            return None 
        # otherwise filter on permissions
        doors_not_permitted_to_this_staff_user = Door.objects.none()  # creates an EmptyQuerySet
        for door in Door.objects.all():
            perm = "djock_app.can_manage_door_%d" % door.pk   # put in proper format for has_perm

            if not request.user.has_perm(perm):
                doors_not_permitted_to_this_staff_user = doors_not_permitted_to_this_staff_user | Door.objects.filter(pk=door.pk)  # concatenating QuerySets
        # todo:  no sets please
        doors_not_permitted_to_this_staff_user_but_for_lockuser = set(this_lu.get_allowed_doors()).intersection(set(doors_not_permitted_to_this_staff_user))
        # all elem that are in this set but not the other. i.e. all doors 
        #return doors_not_permitted_to_this_staff_user

        return doors_not_permitted_to_this_staff_user_but_for_lockuser
        # todo: umm... rename these...

    # The queryset() method in DoorAdmin restricts a staff user's ability to 
    #   view/change Doors that they do not have permission for (individual objects and change list).
    # But on the listdisplay and changeform for LockUsers, staff users can still see Doors 
    #   -- and assign them -- that they don't have permission for.  So here, we need to limit the 
    #   ManyToMany Door field output for the LockUser.  
    #
    # TO DO: maybe it makes more sense for non-permitted doors to be viewable 
    # (Door changelist, LockUser displaylist, LockUser changeform), but be grayed out/readonly
    #
    # TO DO: refactor!
    def formfield_for_manytomany(self, db_field, request, **kwargs):
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
        #return True  
        # todo/temp commenting out 
        # so back to False later

        

    def save_model(self,request,obj,form,change):
        # if deactivate current keycard was checked (which may have actually happened in clean, if  no Doors were selected) 
        # need to deactivate current keycard.  Doing this
        # here rather than models.py because need to attach request.user to the RFIDkeycard object being
        # deactivated, to record revoker
        ## todo:  a better way to do this?

       # if obj.deactivate_current_keycard or not obj.doors.exists():  # although deactivate_current_keycard should have been set to true in clean, if no doors
        if obj.deactivate_current_keycard: 
            obj.current_keycard_revoker = request.user
            msg = "%s's keycard was deactivated successfully." % obj
            messages.add_message(request, messages.INFO, msg)

            #current_keycard = obj.get_current_rfid() 
            #if current_keycard:
            #    current_keycard.deactivate(request.user)
            #    current_keycard.save()
            # there may be no current keycard, so a new one should be prevented from being assigned
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
                
            #msg = form.cleaned_data["special_message"]

        # todo --  ugh this better not be totally before save. 



        # temp/todo: 
        # testing faking it: 
        #form = form + '<li><label for="id_doors_2"><input checked="checked" type="checkbox" name="doors" value="2" id="id_doors_2" /> Space 1</label></li>'
        super(LockUserAdmin, self).save_model(request, obj, form, change)




class AccessTimeAdmin(admin.ModelAdmin):
    # todo: 
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
        return HttpResponseRedirect(reverse('admin:djock_app_accesstime_changelist'))

    #########################################################################
    # Page listing all AccessTimes ("change list" page):
    #########################################################################
    # max num of entries per page
    #list_per_page = 100
    # # field names to display, as columns
    #list_display = ('access_time','get_this_lockuser_html','get_this_door')
    list_display = ('access_time','lockuser_html_heading','door')   # if just 'lockuser', won't get html for link... todo: but I think there's an easier way to do this

    # todo: method names 
    def lockuser_html_heading(self, obj):
        """ Returns the HTML with link to lock user's change_form to display on
            the Access Times change list page """
        #return obj.get_this_lockuser_html()
        return "<a href='../lockuser/%d/'>%s</a>" %  (obj.lockuser.id, obj.lockuser)
    lockuser_html_heading.short_description = 'User'
    # Django will HTML-escape the output by default. If you'd rather not escape the output of the method, give the method an allow_tags attribute whose value is True.
    lockuser_html_heading.allow_tags = True

    actions=None  # don't provide the actions dropdown
    date_hierarchy = 'access_time' # Set date_hierarchy to the name of a DateField or DateTimeField in model, and the
        # change list page will include a date-based drilldown navigation by that field. (i.e. shows months or days or
        # years or whatever at the top)
    list_filter = ('lockuser','door')  # show filters by RFID and active/inactive on the right
    
    #########################################################################
    # Individual TimeAccess page
    # (Although there's no need link to an individual AccessTime object's page, it still exists.)
    #########################################################################
   # readonly_fields = ('access_time','rfid')   # because obviously these shouldn't be editable.   (but commenting out if want to create some objects from admin just for fun)

    def has_delete_permission(self, request, obj=None):
        """ Don't display "delete" button """
        return False
    def has_add_permission(self, request, obj=None):
        """Don't display Save And Add button """
        return False


# To do, if staff users are able to manage other staff users (not a current use case)
"""
#####################################################################
# Customize User list display, change form fields
#####################################################################
class StaffUserAdmin(UserAdmin):
    list_display = ('username','first_name', 'last_name', 'email', 'is_superuser','is_active', 'is_staff', 'date_joined','last_login','get_all_permissions')
    fieldsets = ( 
        (None           { 'fields': (('username', 'email'), 'password') }),
        (None,          { 'fields': (('first_name', 'last_name'))       }),
        (None,          { 'fields': ('last_login', 'date_joined')       }),
        ('Permissions', { 'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'user_permissions') }),
    )   
    add_fieldsets = ( 
        (None, { 'classes': ('wide',),
                 'fields': ('username', 'password1', 'password2')}),  
    )   
    readonly_fields = ('date_joined','last_login')   

    # Limit permissions shown to *staff* users to: 
    # The min perms a non-superuser staff user should have:
    # - lockuser: add, change
    # - manage zero doors
    # - *staff* users: only change own info
    # - access times: *view* only (i.e. change, but can't *edit* anything on change form... right?)
    # 
    # The max perms a non-superuser staff user can have, in addition to above:
    # - doors: add
    # - *staff* users: add, change others
    def get_form(self, request, obj=None, **kwargs):
        form = super(StaffUserAdmin,self).get_form(request, obj, **kwargs)

        # only on change, not add (todo)
        permissions = form.base_fields['user_permissions']

        # maximum permissions
        staff_permissions = permissions.queryset.filter(codename__regex=r'add_lockuser|change_lockuser|add_user|change_user|add_door|change_door')
        staff_permissions = staff_permissions | permissions.queryset.filter(codename__regex = 'can_manage_door')
        # All door management permissions, except deletion (using reqex because door permissions are created dynamically)
        permissions.queryset = staff_permissions
        return form
"""


#####################################################################
# Register models
#####################################################################
#admin.site.register(Door, DoorAdmin)
#admin.site.register(RFIDkeycard, RFIDkeycardAdmin)
admin.site.register(LockUser,LockUserAdmin)
admin.site.register(AccessTime,AccessTimeAdmin)

# Register User with UserAdmin. Note that in settings.py, in INSTALLED_APPS,
#   make sure that 'django.contrib.auth' appears on the list before the app
#   - this app - that is replacing the default admin.  This means that things
#   happen in the right order: first Django registers the User model, then
#   we un-register it here, then we re-register with our own ModelAdmin -
#   User Admin. (If the ordering is wrong, will get error like "The model
#   User is already registered.")
#admin.site.register(User, UserAdmin)
#admin.site.unregister(User)
#admin.site.register(User, StaffUserAdmin)

# Globally disable deletion of selected objects (i.e this will not be an available action in the Actions dropdown of
# all ModelAdmins/change_list pages.
admin.site.disable_action('delete_selected')
# Although might want to be able to delete Doors
