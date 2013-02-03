from django.contrib import admin
from django.forms import CheckboxSelectMultiple, IntegerField, ModelForm
from django.db import models
from djock_app.models import LockUser, AccessTime, RFIDkeycard, Door
import random

#########################  TO DO ########################################################################
#  - Get rid of "delete" action for all except superuser, including not showing the button on change_list
# - (maybe?): When a user is modified or added (in terms of being active at all or more/fewer doors access), e-mail all the staff. 
# - search bar for lockusers/accesstimes/doors change lists
####################################################################################################


class DoorAdmin(admin.ModelAdmin):
    ####################################################################################################
    # Page listing all Doors:
    ####################################################################################################
    # # field names to display, as columns
    list_display = ('name','get_allowed_lockusers','prettify_get_allowed_rfids')
    actions=None  # don't provide the actions dropdown
    
    ####################################################################################################
    # Individual Door page
    ####################################################################################################
    readonly_fields = ('get_allowed_lockusers',)   # because obviously these shouldn't be editable.  
    #(but commenting out if want to create some objects from admin vs shell just for fun)


# playing with prepopulating stuff 
class RFIDkeycardForm(ModelForm):
    #the_rfid = IntegerField(help_text="help text")

    # override __init__ to prepopulate the_rfid field with a random number, just to 
    #   simulate assigning a new card
    def __init__(self, *args, **kwargs):
        super(RFIDkeycardForm, self).__init__(*args, **kwargs)
        self.fields['the_rfid'] = IntegerField(help_text = "(this is a random number to simulate getting a new keycard number after it's scanned in)")
        self.fields['the_rfid'].initial = random.randint(100000,999999)

    class Meta:
        model = RFIDkeycard


class RFIDkeycardAdmin(admin.ModelAdmin):

    # playing with prepopulating stuff 
    form = RFIDkeycardForm

    #inlines = (OpenershipInline,)
    list_display = ["the_rfid","date_created","date_revoked","get_this_lockuser","id"]

    ####################################################################################################
    # Individual page (change form)
    ####################################################################################################
    #prepopulated_fields = { 'the_rfid': ('id',)} 
    fields = ("the_rfid","date_revoked","date_created","id")
    readonly_fields = ("date_revoked","date_created","id")
   # fieldsets = ( (None, { 'fields': ("date_revoked" ),
     #           'description': ('')
      #     }), )
      # WTF? It keeps saying field x doesn't exist, but "x" just picks up the first char of the field, like "field t doesn't
      # exist" if I have "the_rfid" ????!!!



class LockUserAdmin(admin.ModelAdmin):
    ####################################################
    # Page listing all LockUsers ("change list" page):
    ####################################################
    #inlines = (OpenershipInline,)

    ####  no!  creating views to activate/deactivate that are more complex now, so these may
    # reference those instead of just independent updates
    def make_active(self, request, queryset):
        """ Staff should not have the ability to delete LockUsers, only to DEACTIVATE them.  """
 #       queryset.update(is_active=True)
        pass
    make_active.short_description = "Activate selected lock users"

    def make_inactive(self, request, queryset):
        """ Staff should not have the ability to delete LockUsers, only to DEACTIVATE them. """
        #queryset.update(is_active=False)
        pass
    make_inactive.short_description = "Deactivate selected lock users"

    def email_selected(self, request, queryset):
        """ Upon choosing this action, get new screen with field for entering body of email, etc. """
        pass
    email_selected.short_description =  "Email selected lock users"

    # Only the following actions will be shown in the dropdown
    #actions = (activate_keycard, deactivate_keycard, reactivate_keycard, make_active, make_inactive,email_selected)
    actions = (make_active, make_inactive,email_selected)

    # fields (i.e. column headings)
    list_display = ('first_name','last_name','email',\
                    'prettify_get_current_rfid','prettify_get_all_rfids','prettify_get_allowed_doors', \
                    'prettify_get_last_access_time','prettify_get_all_access_times',\
                    'is_active')

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
                            ('first_name', 'last_name'), 'email',\
                            'phone_number','address', \
                            # will error if the below are not set as read_only...  which makes sense; these are methods and
                            # things I can't edit from the form.. right?
                            'prettify_get_current_rfid','prettify_get_all_rfids',\
                            'prettify_get_last_access_time', 'prettify_get_all_access_times', \
                            'is_active',\
                            'doors',
                            'rfids',
                            ),

                'description': ('description.....  Create/modify new lock user and assign keycard')
            }),
        )


    readonly_fields = ("is_active","prettify_get_current_rfid", "prettify_get_all_rfids","prettify_get_last_access_time","prettify_get_all_access_times")   # Obviously access times should not be editable


    # display options as checkboxes, not default as selection list
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
        }
    #inlines = [ DoorInline, ] 

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """ 'Like the formfield_for_foreignkey method, the formfield_for_manytomany method can be overridden to change the default formfield for a many to many field. '  - django docs """
        if db_field.name == "rfids":
            #kwargs["queryset"] = RFIDkeycard.objects.filter(id=None)  # quick and gross way to just have nothing but the plus show up there!
            # but actually that field is required (although I guess it should not be), so limiting to rfid cards assigned to no one... Upon adding new one have to
            # refresh but this is interim behavior anyways. :
            kwargs["queryset"] = RFIDkeycard.objects.filter(lockuser=None)  
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


# Run admin.site.register() for each model we wish to register
# (not defining a new AdminSite because the REAL Django admin just == all staff)
admin.site.register(RFIDkeycard, RFIDkeycardAdmin)
admin.site.register(LockUser,LockUserAdmin)
admin.site.register(AccessTime,AccessTimeAdmin)
admin.site.register(Door, DoorAdmin)

# Globally disable deletion of selected objects (i.e this will not be an available action in the Actions dropdown of
# all ModelAdmins/change_list pages.
admin.site.disable_action('delete_selected')
# Although might want to be able to delete Doors

