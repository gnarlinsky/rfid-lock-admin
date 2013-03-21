from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render, redirect
from djock_app.models import Door, LockUser, RFIDkeycard, AccessTime, NewKeycardScan
import random
from datetime import datetime
from django.utils import simplejson
from termcolor import colored   # temp
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.contrib.auth.models import User
from django.utils.timezone import utc

def generate_random_access_times(request):
    """ just for dev - generate random access times in a specified range """
    min_num_times = int(request.POST.get('min_num_times'))
    max_num_times = int(request.POST.get('max_num_times'))

    # for each keycard in the system, generate a random number of access times, in the range specified in the form
    for keycard in RFIDkeycard.objects.all():
        for i in range(random.randint(min_num_times,max_num_times)):
            #AccessTime(the_rfid=keycard.the_rfid, access_time=get_random_time()).save()
            # todo:  also get keycard's lockuser and pass it
            AccessTime(the_rfid=keycard.the_rfid, access_time=get_random_time(), lockuser=keycard.lockuser).save()
    return HttpResponseRedirect("/lockadmin/")


from random import randrange
from datetime import timedelta, datetime
def get_random_time():
    """ This function will return a random datetime between two datetime objects.  """
    # between now and a year ago
    end = datetime.utcnow().replace(tzinfo=utc)
    start = end - timedelta(days=365)   # one year
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds

    random_second = randrange(int_delta)
    return (start + timedelta(seconds=random_second))




    


# return list of rfid's allowed for all doors, or a particular door,
#   as json list 
def get_allowed_rfids(request, doorid=None):
    """ Returns list of allowed rfid's for the specified door, or 0 if none """
    # check that door id is valid. 
    #   Int of a certain length: taken care of in the urlconf
    #   Check that there even is a such 
    # if door id not valid, return ""
    # todo:  return JSON
    door = Door.objects.filter(pk=doorid)    # doorid should not be pk; note, get returns an rror if no such door; filter returns an empty list
    if door:
        allowed_rfids = door[0].get_allowed_rfids()  # list of Keycard objects
        #alloweds = ",".join([keycard_obj.the_rfid for keycard_obj in allowed_rfids])
        alloweds = [int(keycard_obj.the_rfid) for keycard_obj in allowed_rfids]
    to_json = {"doorid": int(doorid), "allowed_rfids": alloweds}
    return HttpResponse(simplejson.dumps(to_json), content_type="application/json")

# TO DO: refactor below.. to return more immediately; 
#           clean up the conditional logic
def check(request,doorid, rfid): 
    """ In addition to checking whether the given rfid is valid for the given door, 
    also check whether we're actually trying to assign a new keycard rather than 
    authenticating. If not doing a new keycard scan, create and save an AccessTime """
    response = 0
    # if door id not valid or rfid not valid, return ""

    # Is the request actually for new keycard assignment? 
    new_scan_queryset = NewKeycardScan.objects.all()
    if new_scan_queryset:
        new_scan = new_scan_queryset.latest("time_initiated")  # get the latest NewKeycardScan object, ordered by the field time_initiated (i.e. time the object was created) 
        # TODO: Things might go awry if someone else initiated a scan later... Currently verifying pk's later,  in
        # finished_keycard_scan, but do earlier. And pass pk info in a smarter way.

        if new_scan.waiting_for_scan == True:
            new_scan.doorid = doorid  # record the door the new scan request came from (not necessary so far) 
            new_scan.rfid = rfid
            new_scan.save()  
    
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
                                    print colored("**** creating and saving accesstime *****","red","on_white")
                                    at = AccessTime(the_rfid=rfid,access_time=datetime.utcnow().replace(tzinfo=utc), lockuser=rfidkeycard.lockuser)  # todo: access time is going to be a bit later...
                                    at.save()
                                    # TODO: If we reuse keycards/keycard nums, AccessTime objects'
                                    # lockusers -- as seen on AccessTimes change_list, for ex -- will be
                                    # incorrect, since lockuser is the CURRENT owner, so this would not 
                                    # be valid for access times of the PREVIOUS owner. It's probably best to
                                    # associate AccessTimes with lockusers at creation time. I.e. determine
                                    # the current lockuser in *views.py* (check() ) and assign there.

    return HttpResponse(response)


    
def initiate_new_keycard_scan(request,lockuser_object_id):
#def initiate_new_keycard_scan(request):

    # If this lockuser already has a current keycard, don't proceed
    # (This should have been prevented at template level also)
    try: 
        lu = LockUser.objects.filter(id=lockuser_object_id)
    except:
        response_data = {'success':False, "error_mess":"WTF? There's no lock user?"}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    if lu[0].get_current_rfid():
        response_data = {'success':False, 'error_mess':"This lock user is already assigned a keycard! You shouldn't have even gotten this far!"} # Todo: So when stuff like this happens in production...  Should it sent some kind of automated error report to whomever is developing/maintaining the site? 
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        n = NewKeycardScan()
        n.waiting_for_scan = True
        n.assigner_user = request.user
        n.save()   
        response_data = {'success':True, 'new_scan_pk':n.pk}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    
#def finished_new_keycard_scan(request, lockuser_object_id):
def finished_new_keycard_scan(request,new_scan_pk):
    """  Verify this is the NewKeycardScan object we initiated, that the rfid
        is not the same as that of a currently active keycard, and that we 
        haven't timed out. Then get the rfid from the newly-scanned card. 

        Also verifying __, ____, .........
    """
    # TODO:  raise exceptions.   
    # TODO:  Error codes to aid developers. So Staff user sees "ERROR (code 2). Try again," not "ERROR (scary message  about the exact error). Try again." 
    new_scan_queryset = NewKeycardScan.objects.all()
    if not new_scan_queryset:
        response_data = {'success':False, 'error_mess':"No NewKeycardScan objects at all"}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    # Verify that the scan object is the one we need, not one initiated later by someone else, for example.
    new_scan_right_pk_qs = new_scan_queryset.filter(pk = new_scan_pk)  # make sure we have the newKeycardScan object we started with, not one that another staff user initiated *after* us. 

    if not new_scan_right_pk_qs:
        response_data = {'success':False, 'error_mess':"No NewKeycardScan obj with pk " + new_scan_pk}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    new_scan = new_scan_right_pk_qs[0]
    min_till_timeout = 2
    timed_out, time_diff_minutes = new_scan.timed_out(minutes=min_till_timeout)
    if timed_out:
    #if new_scan.timed_out(minutes=min_till_timeout):
        response_data = {'success':False, 'error_mess':"Sorry, the system timed out. You have %d minutes to scan the card, then hit 'Done'.... So don't take %f minutes next time, please, fatty. Run to that lock! You could use the exercise." % (min_till_timeout,time_diff_minutes)}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    if not new_scan.rfid:  
        response_data = {'success':False, 'error_mess':"NewKeycardScan does not have rfid"}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    # if waiting for new keycard to be scanned, but timed out

    # Verify that the rfid is not the same as that of another ACTIVE keycard
    keycards_with_same_rfid_qs = RFIDkeycard.objects.filter(the_rfid=new_scan.rfid)
    for k in keycards_with_same_rfid_qs:
        if k.is_active():
            response_data = {'success':False, 'error_mess':"A keycard with the same RFID is already assigned to %s." % k.lockuser} # to do:  include actual link to this lockuser
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
            
    # OK, so far so good. Set waiting and ready-to-assign status,
    # grab the assigner, and save NewKeycardScan object
    new_scan.waiting_for_scan = False
    new_scan.ready_to_assign = True 
    new_scan.assigner_user = request.user
    new_scan.save()

    response_data = {'success':True, 'rfid':new_scan.rfid}
    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
