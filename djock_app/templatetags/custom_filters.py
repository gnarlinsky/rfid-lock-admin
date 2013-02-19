from django import template
from djock_app.models import LockUser

# All the tags and filters are registered in this variable
register = template.Library()

@register.filter
def is_lockuser_active(object_id):
    try:
        this_lockuser = LockUser.objects.filter(id=object_id)[0]
    except:
        this_lockuser = None
    if this_lockuser:
        return this_lockuser.is_active

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
    return the_object.__class__
    
