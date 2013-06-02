from django import template
from django.contrib.admin.sites import AdminSite
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import stringfilter, safe, cut
from rfid_lock_management.models import LockUser
from rfid_lock_management.admin import LockUserAdmin

register = template.Library()

@register.filter
def get_doors_you_manage(request):
    """
    Give template the list of door names that the staff user can manage,
    or 'None'
    """
    lua = LockUserAdmin(LockUser, AdminSite())
    doors_to_show_qs = lua.get_doors_to_show(request)
    return_val = 'None'  # avoiding a test for 'None'...
    if doors_to_show_qs:
        return_val = ', '.join([door.name for door in doors_to_show_qs])
    return return_val

@register.filter
def fix_json_string(string):
    """
    Marks a string as not requiring further HTML escaping prior to output.
    """
    string = safe(string)
    string = string.replace('"\\"',"'").replace('\\"\"', "'") # fix quotes
    string = cut(string,"\"") # keep fixing
    string = safe(string)  # keep fixing
    return string

@register.filter
def does_lockuser_have_active_keycard(object_id):
    try:
        this_lockuser = LockUser.objects.filter(id=object_id)[0]
    except:
        # No lockuser, so no keycard (i.e. can still get behavior we want
        # on add, when there is no lockuser yet).
        return False
    if this_lockuser:
        if this_lockuser.get_current_rfid():
            return True
        else:
            return False

@register.filter
#def get_object_type(the_object):
def get_object_type(content_type_id):
    """
    Get class of object, based on the content type id
    """
    try:
        ct = ContentType.objects.get(id=content_type_id)
        return ct.model
    except:
        return None
