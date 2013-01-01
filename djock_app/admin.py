from django.contrib import admin
from djock_app.models import LockUser, AccessTime



class LockUserAdmin(admin.ModelAdmin):
    ####################################################
    # Page listing all LockUsers ("change list" page):
    ####################################################
    def make_active(self, request, queryset):
        """ Staff should not have the ability to delete LockUsers, only to DEACTIVATE them.  """
        queryset.update(is_active=True)
    make_active.short_description = "Activate selected lock users"

    def make_inactive(self, request, queryset):
        """ Staff should not have the ability to delete LockUsers, only to DEACTIVATE them. """
        queryset.update(is_active=False)
    make_inactive.short_description = "Deactivate selected lock users"

    def email_selected(self, request, queryset):
        """ Upon choosing this action, get new screen with field for entering body of email, etc. """
        pass
    email_selected.short_description =  "Email selected lock users"

    # Only the following actions will be shown in the dropdown
    actions = (make_active, make_inactive,email_selected)

    # fields (i.e. column headings)
    list_display = ('first_name','last_name','email','rfid','get_last_access_time','get_all_access_times','is_active')
    list_filter = ('rfid','is_active')  # show filters by RFID and active/inactive on the right
    #exclude = ("birthdate ", "middle_name")   # temp exclusion

    # Only the first name will appear as link to the individual LockUser page
    list_display_links = ['first_name']

    ####################################################
    # Individual LockUser page
    ####################################################
    # Which fields to show, and in what order
    # (parentheses group fields into a single line)
    fieldsets = (
            (None, {
                'fields': ( ('first_name', 'last_name'), 'email','phone_number','address', 'rfid', 'get_last_access_time', 'get_all_access_times','is_active'),
                'description': ('description.....  Create/modify new lock user and assign keycard')
            }),

        )
    readonly_fields = ("get_last_access_time","get_all_access_times")   # Obviously access times should not be editable

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
    list_display = ('access_time','rfid','get_this_user')
    actions=None  # don't provide the actions dropdown
    date_hierarchy = 'access_time' # Set date_hierarchy to the name of a DateField or DateTimeField in model, and the
        # change list page will include a date-based drilldown navigation by that field. (i.e. shows months or days or
        # years or whatever at the top)
    
    ####################################################################################################
    # Individual TimeAccess page
    # (Although there's no need link to an individual AccessTime object's page, it still exists.)
    ####################################################################################################
    readonly_fields = ('access_time','rfid')   # because obviously these shouldn't be editable.

    #Don't display save, etc. buttons on bottom (to do: the remaining "Save and continue editing" and "Save")
    def has_delete_permission(self, request, obj=None):
        """ Don't display "delete" button """
        return False
    def has_add_permission(self, request, obj=None):
        """Don't display Save And Add button """
        return False


# Globally disable deletion of selected objects (i.e this will not be an available action in the Actions dropdown of
# all ModelAdmins/change_list pages.
admin.site.disable_action('delete_selected')

# Run admin.site.register() for each model we wish to register
# (not defining a new AdminSite because the REAL Django admin just == all staff)
admin.site.register(LockUser,LockUserAdmin)
admin.site.register(AccessTime,AccessTimeAdmin)