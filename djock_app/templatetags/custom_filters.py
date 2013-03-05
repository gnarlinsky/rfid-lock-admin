from django import template
from djock_app.models import LockUser

# All the tags and filters are registered in this variable
register = template.Library()


""" This is unnecessary, since the new concept is: 
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

@register.filter
def does_lockuser_have_active_keycard(object_id):
    try:
        this_lockuser = LockUser.objects.filter(id=object_id)[0]
    except:
        this_lockuser = None
    if this_lockuser:
        if this_lockuser.get_current_rfid():
            return True
        else:
            return False

@register.filter
def get_object_type(the_object):
    """ get class of object """
    return the_object.__class__.__name__
    
@register.filter
def get_original_id(referrer_path):
    """ given the HTTP_REFERER, get the last part of the URL, 
        which should be the object id. No checking of any kind here, 
        but the expected referer url is something like '...lockuser/3/' 
    """
    split_path = referrer_path.split("/")
    if len(split_path)>1: # more than just "/"
        return split_path[-2]
    else: 
        return None
