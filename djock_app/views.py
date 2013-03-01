from django.http import HttpResponse
from django.shortcuts import render_to_response, render, redirect
from djock_app.models import Door, LockUser, RFIDkeycard, AccessTime, NewKeycardScan
import random
from datetime import datetime
from django.utils import simplejson
from termcolor import colored   # temp
#from django.contrib import messages


def test_jquery(request):
    response_data = {'success':True, 'rfid':"1111111111"}
    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")




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
    """ In addition to checking whether the given rfid is valid for the given door, 
    also check whether we're actually trying to assign a new keycard rather than 
    authenticating. """
    response = 0
    # if door id not valid or rfid not valid, return ""

    # Is the request actually for new keycard assignment? 
    new_scan_queryset = NewKeycardScan.objects.all()
    if new_scan_queryset:
        print colored("here we are .................", "green")
        new_scan = new_scan_queryset.latest("time_initiated")  # get the latest NewKeycardScan object, ordered by the field time_initiated (i.e. time the object was created) 
        if new_scan.waiting_for_scan == True:
            new_scan.doorid = doorid  # record the door the new scan request came from (not necessary so far) 
            new_scan.rfid = rfid
            #messages.success(request,new_scan.rfid)
            #print colored("messages.success "+ str(messages.success),"magenta")
            print colored("the rfid? : "+ str(new_scan.rfid),"magenta")
            new_scan.save()   #?????????
    
    # or is the request actually for authenticating an existing keycard for this door? 
    else: 
        rfidkeycard_list =  RFIDkeycard.objects.all()
        for rfidkeycard in rfidkeycard_list:
            allowed_doors = rfidkeycard.get_allowed_doors()
            if allowed_doors:
                for door in rfidkeycard.get_allowed_doors():
                    if rfidkeycard.is_active():
                        if rfidkeycard.the_rfid == rfid:
                            if int(door.id) == int(doorid):
                                response = 1

    return HttpResponse(response)

def initiate_new_keycard_scan(request,lockuser_object_id):
    n = NewKeycardScan()
    n.waiting_for_scan = True
    print colored("n.waiting_for_scan: "+str(n.waiting_for_scan), "red")
    n.save()   

    # back to the lockuser's (the one who we deactivated the card for) change_form
    back_to_lockuser = "/lockadmin/djock_app/lockuser/%s/" % lockuser_object_id
    return redirect(back_to_lockuser)
    # todo: No refreshing, pls!   AJAX
    
def finished_new_keycard_scan(request, lockuser_object_id):


    # todo: Does it make more sense to put this in RFIDkeycardForm, in admin.py? 
    new_scan_queryset = NewKeycardScan.objects.all()
    if new_scan_queryset:
        new_scan = new_scan_queryset.latest("time_initiated")  # get the latest NewKeycardScan object, ordered by the field time_initiated (i.e. time the object was created) 
        print colored("waiting? "+ str(new_scan.waiting_for_scan),"blue")
        print colored("time_initiated? "+ str(new_scan.time_initiated),"blue")
        print colored("timed_out?, 2 min default: "+ str(new_scan.timed_out()),"blue")
        print colored("the doorid? : "+ str(new_scan.doorid),"blue")
        print colored("the rfid? : "+ str(new_scan.rfid),"blue")
        # if waiting for new keycard to be scanned, but timed out
        if new_scan.timed_out(minutes=2):
            pass

        # set waiting status to False and save NewKeycardScan object
        new_scan.waiting_for_scan = False
        new_scan.save()
        # todo: or should I delete the NewKeycardScan object when done with it?

    # Return message indicating whether we're good to go (so staff user can go ahead and hit "save" for
    # this lockuser), or whether we timed out. 
    #######################################
    # Also can send back extra stuff in the redirect url, e.g. /blah/?var=5 -- You would then parse that
    # variable with request.GET in the view code and show the appropriate text
    #######################################
    #print colored("here's messages.info: "+str(messages.success), "red")

    # back to the lockuser's (the one who we deactivated the card for) change_form
    back_to_lockuser = "/lockadmin/djock_app/lockuser/%s/" % lockuser_object_id
    return redirect(back_to_lockuser)
    # todo: No refreshing, pls!   AJAX








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
