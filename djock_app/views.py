#from django.views.generic.simple import redirect_to, direct_to_template
from django.http import HttpResponse
from django.shortcuts import render_to_response
from djock_app.models import Door, LockUser, RFIDkeycard, AccessTime
import random


# pseudocoding how to  handle the incoming request to verify rfid
# I think we discussed two ways of verifying: id 
#   - primary: /door/<door_id>/check/<rfid_id>
#   - secondary (if stuff is down): cached version on arduino????
"""
def is_allowed(request, rfid, door):
    alloweds = door.get_allowed_rfids()

    if rfid in alloweds:
        return HttpResponse with 1
    else:
        0
"""

# TO DO: tests for get_all_allowed (across doors); e.g. all_allowed/
# tests for URLS with door id's as well, e.g. all_allowed/door/x

# return list of rfid's allowed for all doors, or a particular door,
#   as json list 
#   (Should just do one method, with door defaulting to None/one urlconf? 
#   Or just have an additional urlconf for get_allowed_one_door/doorid/ vs get_allowed_all_doors/
def get_allowed_rfids(request, doorid=None):
    """ Returns list of allowed rfid's for the specified door, or 0 if none """
    # check that door id is valid. 
    #   Int of a certain length: taken care of in the urlconf
    #   Check that there even is a such 
    # if door id not valid, return ""
    doors = Door.objects.filter(pk=doorid)    # doorid should not be pk; note, get returns an error if no such door; filter returns an empty list
    if doors:
        response = doors[0].get_allowed_rfids()
    if not response: 
        response = 0  # make sure not going to return empty set
    return HttpResponse(response)
    
     

    


# TO DO: refactor below.. to return more immediately; 
#           clean up the conditional logic
def check(request,doorid, rfid): 
    response = 0
    # if door id not valid or rfid not valid, return ""

    rfidkeycard_list =  RFIDkeycard.objects.all()

    for rfidkeycard in rfidkeycard_list:
        allowed_doors = rfidkeycard.get_allowed_doors()
        if allowed_doors:
            for door in rfidkeycard.get_allowed_doors():
                if rfidkeycard.is_active():
                    if rfidkeycard.the_rfid == rfid:
                        if int(door.id) == int(doorid):
                            response = 1

    # And in the case where we're actually assigning a new card, so need to get back to that template... 
    # ......   can the response actually be a status code? 
    return HttpResponse(response)

"""def check(request, doorid, rfid):

    return list_detail.object_list(
        request,
        queryset = RFIDkeycard.objects.all(), 
        template_name = "basic.html",
        #template_object_name = "rfidkeycard_list",  # So in template,  {% for rfidkeycard in rfidkeycard_list %} instead of   {% for rfidkeycard in object_list %} .....  although something isn't working.....
        extra_context = {"params" :{'doorid': doorid, 'rfid':rfid}, \
        "doors_list": Door.objects.all(), 
                     }   
                     )   

"""



    
    

#generate a random number to simulate an actual keycard being scanned in and the num retrieved """
"""
def fake_assign(request):
    fake_rfid = random.randint(1000000000,9999999999)
    # template is change_form.html?  really?
    return render_to_response('admin/djock_app/change_form.html', {'fake_rfid': fake_rfid} )
"""
# How about creating a custom template tag, like {{ fake_rfid }} ?


###############  TO DO/ TO NOTE #####################################
"""
ON ASSIGNING NEW KEYCARD: 
- When a card is scanned, the arduino will try to hit some url to 
  verify if a certain rfid is ok.   like is_it_ok/bike_proj_door/<some_num>/.
- The same view that is called by that urlconf ***should also check 
  whether we're expecting a bad (i.e. not approved) key right now,
  for the purposes of assigning it to some user.*** If yes, that's
  the one to assign, instead of checking if it's approved.   

  (See email thread 'The actual process of assigning a keycard?' for more infoz.

  For now, though, blackbox away some of this..... So, what happens when want to assign a new keycard, if one has not been assigned already:  on an individual lock user's page:   
-  there should be a button:  "Activate keycard."  
-  Clicking that should show prompt like "Go scan in new card."  
- But for now, right next to that: button, e.g. "OK, I fake-scanned it." 
- Clicking on that button should  result in the same thing that scanning in a new card should result in.  
-  For now, just generate some random long number. 
- Then create a new keycard with that number

If there is already a keycard assigned, but deactivated, show a REactivate button. 
        just set the is_active to True. 


So this was in admin.py.........
    def make_active(self, request, queryset):
        # check if REactivating
        queryset = blah blah
        queryset.update(is_active=True)

    def make_inactive(self, request, queryset):
        queryset = blah blah
        queryset.update(is_active=False)


ON CHECKING IF AN RFID/KEY IN THE URL IS APPROVED FOR THE SPECIFIED DOOR(S):
- Get the door object for the (slugified?) door name in the url
- Get the QuerySet of associated RFIDkeycards
- Filter those for RFIDkeycard's rfid_num = rfid num in url


LATER........
- When a user is modified or added (in terms of being active at all or more/fewer doors access), e-mail all the staff. 
"""


