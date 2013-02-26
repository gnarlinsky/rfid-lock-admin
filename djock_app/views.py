from django.http import HttpResponse
from django.shortcuts import render_to_response, render, redirect
from djock_app.models import Door, LockUser, RFIDkeycard, AccessTime
import random
from datetime import datetime


# pseudocoding how to  handle the incoming request to verify rfid
# I think we discussed two ways of verifying: id 
#   - primary: /door/<door_id>/check/<rfid_id>
#   - secondary (if stuff is down): cached version on arduino -- but obv no code here for that


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
        response = ",".join(doors[0].get_allowed_rfids())
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


def deactivate_keycard(request,object_id):
    """ object_id was in the url -- it contains the id of the lockuser that needs its
    current keycard deactivated. 
        I.e. - get this lockuser's current keycard
             - deactivate it (set this keycard's date_revoked to now)
    """

    # to do: exceptions
    try:
        lu = LockUser.objects.filter(id=object_id)[0]
        rfk = lu.get_current_rfid()[0]
    except:
        # raise exception?
        return render(request,'basic.html')
    print "********* object_id is ", object_id
    print "\ti.e. the lockuser is ", lu
    print "\t and their keycard: ", rfk
    print "\t keycard is active? ", rfk.is_active()
    print "\t keycard's date revoked ", rfk.date_revoked

    #if rfk.is_active():
        #rfk.date_revoked = datetime.now()
        #rfk.save()
    rfk.deactivate()
    print "\t AFTER - keycard's date revoked ", rfk.date_revoked
    print "\t AFTER - is_active(): ", rfk.is_active()
    rfk.save()   # save RFIDkeycard object

    #return render(request, 'basic.html')
    #return HttpResponse(request,

    # back to the lockuser's (the one who we deactivated the card for) change_form
    back_to_lockuser = "/lockadmin/djock_app/lockuser/%s/" % lu.id
    return redirect(back_to_lockuser)
    #return redirect(lu)
    

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
"""
