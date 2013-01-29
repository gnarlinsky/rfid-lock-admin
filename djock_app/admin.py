from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models
from djock_app.models import LockUser, AccessTime, RFIDkeycard, Door

# do I need this????
#class OpenershipAdmin(admin.ModelAdmin):
#    pass

# https://docs.djangoproject.com/en/dev/ref/contrib/admin/#working-with-many-to-many-intermediary-models
#class OpenershipInline(admin.TabularInline):
    #model = Openership
    #extra = 1



#########################  TO DO ########################################
# Get rid of "delete" action for all except superuser, 
# including not showing the button on change_list
########################################################################



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
    readonly_fields = ('get_allowed_lockusers',)   # because obviously these shouldn't be editable.   (but commenting out if want to create some objects from admin just for fun)

class RFIDkeycardAdmin(admin.ModelAdmin):
    #inlines = (OpenershipInline,)
    list_display = ["the_rfid","date_created","date_revoked","get_this_lockuser"]

class LockUserAdmin(admin.ModelAdmin):
    ####################################################
    # Page listing all LockUsers ("change list" page):
    ####################################################
    #inlines = (OpenershipInline,)

    ####  no!  creating views to activate/deactivate that are more complex now, so these should reference those
    # instead of just independent updates
    #       Update: Well.... maybe not.  I'm distinguishing (de)activating LockUsers from (de)activating RFIDkeycards now, so
    #       come back to this.......
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

    def activate_keycard(self,request,queryset): pass
    activate_keycard.short_description = "Activate keycard"
    def deactivate_keycard(self,request,queryset): pass
    deactivate_keycard.short_description = "Deactivate keycard"
    def reactivate_keycard(self,request,queryset): pass
    reactivate_keycard.short_description = "Reactivate keycard"

    # Only the following actions will be shown in the dropdown
    actions = (activate_keycard, deactivate_keycard, reactivate_keycard, make_active, make_inactive,email_selected)

    # fields (i.e. column headings)
    list_display = ('first_name','last_name','email','prettify_get_current_rfid','prettify_get_all_rfids','prettify_get_allowed_doors','prettify_get_last_access_time','prettify_get_all_access_times','is_active')

    #list_filter = ('rfid','is_active')  # show filters by RFID and active/inactive on the right
    #exclude = ("birthdate ", "middle_name")   # temp exclusion

    # Only the first and last names  will appear as link to the individual LockUser page
    list_display_links = ['first_name','last_name']

    ####################################################
    # Individual LockUser page
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
                            # !!!!!!!!!!!!!  What you want is to set allowed doors from here, right. So now you have to go into
                            # this territory:  how do i make these into like checkboxes or whatever.  form shit. like this:
                            # http://stackoverflow.com/questions/1760421/how-can-i-render-a-manytomanyfield-as-checkboxes
                            # update to that:  nope.   DO INLINE SHIT HERE... RIGHT? 
                            # https://docs.djangoproject.com/en/dev/ref/contrib/admin/#inlinemodeladmin-objects
                            #  goddamnit something is not fucking working, wtf.
                            #  https://docs.djangoproject.com/en/dev/ref/contrib/admin/#working-with-many-to-many-models leads me
                            #  to believe there should not be this fucking trouble with just fucking displaying fucking a
                            #  manytomany or fk field without any inline shenanigans. so wtf. 

                            # wait, you know what.......     the reason doors wasn't happening was because it's a fucking
                            # rfidkeycard field, not lockuser field.  So now that I think about it....   door access should be
                            # defined by the person, not by the keycard.  that is, it should be just a fucking manytomany in
                            # lockusers.   and then rfidkeycard can look at the fucking lockuser for its shit. 
                            'prettify_get_current_rfid','prettify_get_all_rfids',\
                            'prettify_get_last_access_time', 'prettify_get_all_access_times', \
                            'is_active',\
                            #'get_allowed_doors', \
                            # but this won't work either! even if you read-only it. 
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

