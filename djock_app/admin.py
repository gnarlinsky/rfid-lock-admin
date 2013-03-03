from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.forms import CheckboxSelectMultiple, IntegerField, ModelForm
from django.db import models
from djock_app.models import LockUser, AccessTime, RFIDkeycard, Door, NewKeycardScan
import random  #temp
from termcolor import colored   #temp




#########################  TO DO ########################################################################
#  - Get rid of "delete" action for all except superuser, including not showing the button on change_list
# - (maybe?): When a user is modified or added (in terms of being active at all or more/fewer doors access), e-mail all the staff. 
# - search bar for lockusers/accesstimes/doors change lists
# -  # the field labeled "rfids" should not be required.  
####################################################################################################


class DoorAdmin(admin.ModelAdmin):
    ####################################################################################################
    # Page listing all Doors:
    ####################################################################################################
    # # field names to display, as columns
    list_display = ('name','id', 'get_allowed_lockusers_html_links','get_all_access_times','prettify_get_allowed_rfids')
    actions=None  # don't provide the actions dropdown
    
    ####################################################################################################
    # Individual Door page
    ####################################################################################################
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






        """ has_perm(perm, obj=None) / has_perms(perm_list, obj=None)
        Returns True if the user has the specified permission, where perm is in the format "<app label>.<permission codename>". (see documentation on permissions). If the user is inactive, this method will always return False.

        If obj is passed in, this method won't check for a permission for the model, but for this specific object.
        """


            # permission codenames are named can_manage_door_x, where x is the pk num
        # else... return nothing and/or exception? 

# playing with prepopulating stuff 
class RFIDkeycardForm(ModelForm):
    #the_rfid = IntegerField(help_text="help text")

    # override __init__ to prepopulate the_rfid field with a random number, just to 
    #   simulate assigning a new card
    """
    def __init__(self, *args, **kwargs):
        super(RFIDkeycardForm, self).__init__(*args, **kwargs)
        new_scan_queryset = NewKeycardScan.objects.all()
        if new_scan_queryset: 
            new_scan = new_scan_queryset.latest("time_initiated")  # get the latest NewKeycardScan object, ordered by the field time_initiated (i.e. time the object was created) 
            print colored("the rfid? : "+ str(new_scan.rfid),"white","on_green")
            print colored("is newKeycardScan obj available? " + str(new_scan),"white","on_green")
            self.fields['the_rfid'] = IntegerField(help_text = "(Not a random number -- from door/rfid check request)")
            self.fields['the_rfid'].initial = new_scan.rfid
        else: 
            print colored("is newKeycardScan obj available? NOPE " ,"white","on_green")
            self.fields['the_rfid'] = IntegerField(help_text = "(This is a random number to simulate getting a new keycard number after it's scanned in.<br>Only superuser can actually see the number.)")
            self.fields['the_rfid'].initial = str(random.randint(0000000000,9999999999)) # rfid's should be 10 char long... just str'ing ints, because I don't want to mess with random crap anymore.
        """

    class Meta:
        model = RFIDkeycard

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

class RFIDkeycardAdmin(admin.ModelAdmin):
    form = RFIDkeycardForm # prepopulating with random num

    list_display = ["the_rfid","id", "date_created","date_revoked","is_active", "lockuser",
                    "get_allowed_doors_html_links"]

    ####################################################################################################
    # Individual page (change form)
    ####################################################################################################
    #prepopulated_fields = { 'the_rfid': ('id',)} 
    #fields = ("the_rfid","date_revoked","date_created","id")
    fields = ("lockuser","date_created","date_revoked","is_active","get_allowed_doors")  # here showing fields wouldn't show to a staff user, since the real (not inline) RFIDkeycard change_form would only be visible to superuser.
    readonly_fields = ("date_created","is_active","get_allowed_doors")
    #   Should I check for that at other levels of the code
    # lockuser should be editable after creation....  But it should show only one lockuser in the
    # dropdown, so theoretically it's ok. 


    #readonly_fields = ("the_rfid",)   # I only see None when readonly. Maybe need to save first in RFIDkeycardForm's __init__?
                                        # But since regular staff users shouldn't see it at all... forget it. 


   # fieldsets = ( (None, { 'fields': ("date_revoked" ),
     #           'description': ('')
      #     }), )
      # WTF? It keeps saying field x doesn't exist, but "x" just picks up the first char of the field, like "field t doesn't
      # exist" if I have "the_rfid" ????!!!


#####################################################
# NO MORE INLINE RFIDKEYCARD FORM
#####################################################
# class RFIDkeycardInline(admin.TabularInline):
#     """ The inline form that staff users will see. """
#     form = RFIDkeycardForm
#     model = RFIDkeycard
#     extra = 1  # how many inline objects to add a time/how many blank inlines to show
# 
#     can_delete = False # Specifies whether or not inline objects can be deleted in the inline.
#     fields = ("lockuser","date_created","date_revoked","is_active")
#     readonly_fields = ("date_created","date_revoked","is_active")   # TO DO:  show date_created, date_revoked (along with some other fields?) only on existing keycards, not at creation time. 
#     #exclude = ("the_rfid",)
# 
#     # override __init__ to prepopulate the_rfid field with a random number, just to 
#     #   simulate assigning a new card
#     """
#     def __init__(self, *args, **kwargs):
#         super(RFIDkeycardInline, self).__init__(*args, **kwargs)
#         self.fields['the_rfid'] = IntegerField(help_text = "(This is a random number to simulate getting a new keycard number after it's scanned in.<br>Only superuser can actually see the number.)")
#         self.fields['the_rfid'].initial = str(random.randint(0000000000,9999999999)) # rfid's should be 10 char long... just str'ing ints, because I don't want to mess with random crap anymore.
#     """
#     #fields['the_rfid'] = IntegerField(help_text = "(This is a random number to simulate getting a new keycard number after it's scanned in.<br>Only superuser can actually see the number.)")
#     #fields['the_rfid'].initial = str(random.randint(0000000000,9999999999)) # rfid's should be 10 char long... just str'ing ints, because I don't want to mess with random crap anymore.
#     def queryset(self,request):
#         """
#         Limit the existing RFIDkeycard objects displayed inline on LockUser's change_form. Don't show any - 
#            only the "+" should be there.
#         """ 
#         # temporarily show some keycards there, for debugging
#         rfk_queryset = super(RFIDkeycardInline, self).queryset(request).none() # creates an EmptyQueryset  
#         return rfk_queryset
# 

class LockUserAdmin(admin.ModelAdmin):
    #inlines = [RFIDkeycardInline]



    ####################################################
    # Page listing all LockUsers ("change list" page):
    ####################################################


    #-------------------
    # Actions dropdown
    #------------------
    def make_active(self, request, queryset):
        """ Staff should not have the ability to delete LockUsers, only to DEACTIVATE them.  """
        queryset.update(activate=True)
        # Must save after update(), since update()  doesn't run any save() methods on your models, or emit the pre_save
        # or post_save signals (which are a consequence of calling save()).
        for obj in queryset:
            obj.save()    
    make_active.short_description = "Activate selected lock users"

    def make_inactive(self, request, queryset):
        """ Staff should not have the ability to delete LockUsers, only to DEACTIVATE them. """
        queryset.update(activate=False)
        for obj in queryset:
            obj.save()    #otherwise associated keycard won't become deactivated
    make_inactive.short_description = "Deactivate selected lock users"

    def deactivate_keycard(self, request, queryset):
        """ Deactivate associated keycard """
        queryset.update(deactivate_current_keycard=True)
        for obj in queryset:
            obj.save()    
    deactivate_keycard.short_description = "Deactivate selected lock users' keycards"

    def email_selected(self, request, queryset):
        """ Upon choosing this action, get new screen with field for entering body of email, etc. """
        pass
    email_selected.short_description =  "Email selected lock users"

    # Only the following actions will be shown in the dropdown
    #actions = (activate_keycard, deactivate_keycard, reactivate_keycard, make_active, make_inactive,email_selected)
    actions = (make_active, make_inactive, deactivate_keycard, email_selected)


    
    #-------------------------
    # Which fields to display
    #-------------------------
    # fields (i.e. column headings)
    list_display = ('first_name','last_name','email',\
                    'prettify_get_current_rfid','prettify_get_all_rfids',\
                    'get_allowed_doors_html_links',\
                    'prettify_get_last_access_time',
                 #  'is_active',
                    'activate',
    )

    #list_filter = ('rfid','is_active')  # show filters by RFID and active/inactive on the right
    #exclude = ("birthdate ", "middle_name")   # temp exclusion

    # Only the first and last names  will appear as link to the individual LockUser page
    list_display_links = ['first_name','last_name']

    ####################################################
    # Individual LockUser page  (change form)
    ####################################################
    # Which fields to show, and in what order
    # (parentheses group fields into a single line)
    fieldsets = (
            (None, {
                'fields': ( \
                            ('first_name', 'last_name'), \
                            #'email',\
                            'phone_number','address', \
                            # will error if the below are not set as read_only...  which makes sense; these are methods and
                            # things I can't edit from the form.. right?
                            'prettify_get_current_rfid','prettify_get_all_rfids',\
                            'prettify_get_last_access_time', 'prettify_get_all_access_times', \
                            #'is_active', \
                            'activate', \
                            'doors',
                            'deactivate_current_keycard',
                          #  'rfids',
                            ),

                'description': ('description.....  Create/modify new lock user and assign keycard')
            }),
        )


    readonly_fields = ("prettify_get_current_rfid", "prettify_get_all_rfids","prettify_get_last_access_time","prettify_get_all_access_times")   # Obviously access times should not be editable


    # display options as checkboxes, not default as selection list
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
        }


    ####################################################################
    # Switching to Foreign Key relationship for RFIDkeycard/LockUser,
    #   so need a change in the interface (which makes more sense
    #   anyways):
    #       - "Assign new keycard" is a primary action, accessible from main
    #       - Goes to rfidkeycard/add -- same "go scan in, I'm waiting" deal as before
    #       - Can't create an RFIDkeycard without ****assigning it a LockUser -- which
    #           can be done from the RFIDkeycard change_form****
    #       - But can create a LockUser without assigning a keycard, same as before
    #       - Eliminating: create a new RFIDkeycard from LockUser page as a popup/inline
    #       - But "assign new keycard"/"deactivate keycard" (fieldset.html) should
    #           still behave the same way for the user.
    ####################################################################


     
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """ 'Like the formfield_for_foreignkey method, the formfield_for_manytomany method can be overridden to change the default formfield for a many to many field. '  - django docs;
        Here, need specific behavior for rfid keycards and Doors"""

        ################
        #  rfids
        ################
        # if the field name is rfids, don't show any -- only the "+" should be there,
        #   i.e. "assign new keycard"
        if db_field.name == "rfids":
            # No existing rfid keycard/number should be shown on the LockUser's change form, 
            # at least not to non-superusers
            #kwargs["queryset"] = RFIDkeycard.objects.none()  # creates an EmptyQueryset  
            # temporarily show some keycards there, for debugging
            kwargs["queryset"] = RFIDkeycard.objects.all()  
        

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        ################
        #  doors
        ################
        # The queryset() method in DoorAdmin restricts a staff user's ability to 
        #   view/change Doors that they do not have permission for (individual objects and change list).
        # But on the listdisplay and changeform for LockUsers, staff users can still see Doors 
        #   -- and assign them -- that they don't have permission for.  So here, we need to limit the 
        #   ManyToMany Door field output for the LockUser.  
        #
        # TO DO: maybe it makes more sense for non-permitted doors to be viewable 
        # (Door changelist, LockUser displaylist, LockUser changeform), but be grayed out/readonly
        if db_field.name == "doors":
            doors_to_show = Door.objects.none()  # creates an EmptyQuerySet
            for door in Door.objects.all():
                perm = "djock_app.can_manage_door_%d" % door.pk   # put in proper format for has_perm
                #if request.user.has_perm(perm):
                # if staff user has permission for a certain door, or if user is superuser,  put door on the list
                if request.user.is_superuser or request.user.has_perm(perm):
                    doors_to_show = doors_to_show | Door.objects.filter(pk=door.pk)  # concatenating QuerySets
                    # Doing door instead of the filter, as below, results in Error: 'Door' object has no attribute '_clone'...???
                    #doors_to_show = doors_to_show | door   # concatenating QuerySets
            kwargs["queryset"] = doors_to_show

        return super(LockUserAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    #Don't display save, etc. buttons on bottom (to do: the remaining "Save and continue editing" and "Save")
    def has_delete_permission(self, request, obj=None):
        """ Don't display "delete" button """
        return False



class AccessTimeAdmin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        """ Only defining here because simply including
                list_display_links = []
            above does not work; it defaults to linking from items in AccessTime col
        """
        super(AccessTimeAdmin, self).__init__(*args, **kwargs)
        # There's no need to show the page for an individual AccessTime, so no field should link to it.
        self.list_display_links = (None, )

    ####################################################################################################
    # Page listing all AccessTimes ("change list" page):
    ####################################################################################################
    # # field names to display, as columns
    list_display = ('access_time','the_rfid','get_this_lockuser')
    actions=None  # don't provide the actions dropdown
    date_hierarchy = 'access_time' # Set date_hierarchy to the name of a DateField or DateTimeField in model, and the
        # change list page will include a date-based drilldown navigation by that field. (i.e. shows months or days or
        # years or whatever at the top)
    
    ####################################################################################################
    # Individual TimeAccess page
    # (Although there's no need link to an individual AccessTime object's page, it still exists.)
    ####################################################################################################
   # readonly_fields = ('access_time','rfid')   # because obviously these shouldn't be editable.   (but commenting out if want to create some objects from admin just for fun)

    #Don't display save, etc. buttons on bottom (to do: the remaining "Save and continue editing" and "Save")
    def has_delete_permission(self, request, obj=None):
        """ Don't display "delete" button """
        return False
    def has_add_permission(self, request, obj=None):
        """Don't display Save And Add button """
        return False



#####################################################################
# Customize User list display, change form fields
#####################################################################
"""
class StaffUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')
    #fields = ('additional_attribute',)
    #fields += ('email','first_name',)
    fieldsets = (
            (None, {
                'fields': ( \
                            ('first_name', 'last_name'), 'email', 'additional_attribute',\
                            ),

            }),
        )
    #add_fieldsets = (
    #fieldsets = (
    #        (None, {
                #'classes': ('wide',),
                #'fields': ('additional_attribute') }
   #             'fields': ('username', 'first_name','additional_attribute') 
   #             } ),
   #     )

    #readonly_fields = ('additional_attributes',)   
    #fields = ('username', )
"""









#####################################################################
# Custom user permissions
#####################################################################

#  should this stuff go in __init__.py? 
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


# Django's athentication framework uses the contenttypes framework (INSTALLED_APPS)
# to tie user permissions to specific models.
content_type = ContentType.objects.get(app_label='djock_app', model='lockuser')

"""
permission = Permission.objects.get_or_create(codename='can_manage_door_1',  \
               name='Can Manage Door 1',\
              #content_type=content_type)
              content_type=content_type)
"""

# Making door permissions based on how many door there are right now, not hardcoding it in
door_objects = Door.objects.all()
for door in door_objects:
# or just get(.../create?   ??  vs get_or_create ??
    perms, created = Permission.objects.get_or_create(\
                    codename='can_manage_door_%d' % door.pk, \

                    # TO DO: make sure door names are unique!
                    name = 'Can manage door to %s' % door.name,\

                    content_type = content_type)   
                                                

#####################################################################
# Customize User list display, change form fields
#####################################################################
UserAdmin.list_display = ('username','first_name', 'last_name', 'email', 'is_superuser','is_active', 'is_staff','get_all_permissions')
#UserAdmin.fields = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')
#UserAdmin.fieldsets = (
    #fieldsets = (
#            (None, {
                #'classes': ('wide',),
                #'fields': ('username','password1','password2','email', 'first_name', 'last_name', 'is_active', 'is_staff','user_permissions')
 #               'fields': ( \
 #                           ('username'),\
 #                           ('first_name', 'last_name'), \
 #                           'username','email','is_active', 'is_staff','user_permissions',\
 #                           'email',\
 #                           ),
 #               } ),
 #       )
    #readonly_fields = ('additional_attributes',)   

#####################################################################
# Register models
#####################################################################
admin.site.register(LockUser,LockUserAdmin)
admin.site.register(RFIDkeycard, RFIDkeycardAdmin)
admin.site.register(AccessTime,AccessTimeAdmin)
admin.site.register(Door, DoorAdmin)

# Register User with UserAdmin. Note that in settings.py, in INSTALLED_APPS,
#   make sure that 'django.contrib.auth' appears on the list before the app
#   - this app - that is replacing the default admin.  This means that things
#   happen in the right order: first Django registers the User model, then
#   we un-register it here, then we re-register with our own ModelAdmin -
#   User Admin. (If the ordering is wrong, will get error like "The model
#   User is already registered.")
#admin.site.register(User, StaffUserAdmin)
#admin.site.register(User)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)



# Globally disable deletion of selected objects (i.e this will not be an available action in the Actions dropdown of
# all ModelAdmins/change_list pages.
admin.site.disable_action('delete_selected')
# Although might want to be able to delete Doors

