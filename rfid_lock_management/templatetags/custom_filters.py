from django import template
from rfid_lock_management.models import LockUser
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import stringfilter, safe, cut
#from django.contrib.auth.models import User
from rfid_lock_management.admin import LockUserAdmin
from django.contrib.admin.sites import AdminSite

# All the tags and filters are registered in this variable
register = template.Library()


@register.filter
def get_doors_you_manage(request):
    """ Give template the list of door names that the staff user can manage, or 'None' """
    lua = LockUserAdmin(LockUser, AdminSite())
    doors_to_show_qs = lua.get_doors_to_show(request)
    return_val = 'None'  # avoiding a test for 'None'...
    if doors_to_show_qs: 
        return_val = ', '.join([door.name for door in doors_to_show_qs])
    return return_val



@register.filter
def fix_json_string(string):
    """ Marks a string as not requiring further HTML escaping prior to output. """
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
        return False # No lockuser, so no keycard (so can still get the behavior we want on add, when there is no lockuser yet) 
    if this_lockuser:
        if this_lockuser.get_current_rfid():
            return True
        else:
            return False

@register.filter
#def get_object_type(the_object):
def get_object_type(content_type_id):
    """ get class of object, based on the content type id """
    #return the_object.__class__.__name__
    try:
        ct = ContentType.objects.get(id=content_type_id)
        return ct.model
    except:
        return None
   

"""
@register.filter
def get_original_id(referrer_path):
   #  given the HTTP_REFERER, get the last part of the URL, 
   #     which should be the object id. No checking of any kind here, 
   #     but the expected referer url is something like '...lockuser/3/' 
    split_path = referrer_path.split("/")
    if len(split_path)>1: # more than just "/"
        return split_path[-2]
    else: 
        return None
"""



""" 
This is unnecessary, since the new concept is: 
    lockuser is not active IFF no current keycard
@register.filter
def is_lockuser_active(object_id):
    try:
        this_lockuser = LockUser.objects.filter(id=object_id)[0]
    except:
        this_lockuser = None
    if this_lockuser:
        # return this_lockuser.activate 
        return not this_lockuser.deactivated  # so if deactivated, will return False 
"""

