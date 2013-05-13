from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
import rfid_lock_management.models
from datetime import datetime
from django.utils import simplejson
from termcolor import colored   # temp
from django.utils.timezone import utc
from django.contrib.auth.decorators import login_required
from rfid_lock_management.misc_helpers import get_arg_default
from rfid_lock_management.models import Door, NewKeycardScan, AccessTime, RFIDkeycard, LockUser

@login_required
def chartify(request): 
    """
    Return data in appropriate format for the HighCharts (JavaScript) AccessTime plot. 
    Creates a series for each door.
    """
    tooltip_dict = {}
    tooltip_dict['followPointer']='false'
    tooltip_dict['pointFormat']='"{point.user}"'
    all_series = []
    for door in Door.objects.all(): 
        one_series = {}
        one_series['name'] = '"%s"' % door.name
        one_series['tooltip'] = tooltip_dict
        this_door_access_times = AccessTime.objects.filter(door=door)
        one_series['data'] = []
        for at in this_door_access_times:
            one_series['data'].append(simplejson.loads(at.data_point))  # todo: ugh with the loads'ing           
        all_series.append(one_series)
    extra_context = {'chart_data': simplejson.dumps(all_series, indent="") } 
    return render_to_response('chart.html', dictionary=extra_context, context_instance=RequestContext(request))

def get_allowed_rfids(request, doorid):
    """ Returns list of allowed rfid's for the specified door in JSON format """
    try:
        door = Door.objects.get(pk=doorid)
        allowed_rfids = door.get_allowed_rfids()  # list of Keycard objects
        alloweds = [keycard_obj.the_rfid for keycard_obj in allowed_rfids]
    except:  # door may not exist or any other error . . . 
        alloweds = ""   # but still need to respond

    to_json = {"doorid": int(doorid), "allowed_rfids": alloweds}
    return HttpResponse(simplejson.dumps(to_json), content_type='application/json')

def check(request,doorid, rfid): 
    """ 
    In addition to checking whether the given rfid is valid for the given door, 
    this checks whether we're actually trying to assign a new keycard rather than 
    authenticating. If not doing a new keycard scan, create and save an AccessTime. 
    """
    response = 0

    # Is the request actually for new keycard assignment? 
    new_scan_queryset = NewKeycardScan.objects.all()
    if new_scan_queryset:
        # Note - getting latest NewKeycardScan object by ordering by the field 
        # time_initiated may not actually return the latest created object if 
        # 'start scan' was hit many times in a row -- even microseconds don't 
        # seem to have sufficient resolution to actually get the latest object. 
        new_scan = new_scan_queryset.latest("pk")  # get the latest NewKeycardScan object, 

        # Issue #e
        if new_scan.waiting_for_scan == True:
            new_scan.doorid = doorid  # record the door the new scan request came from (not necessary so far) 
            new_scan.rfid = rfid
            new_scan.save()  
            return HttpResponse(response)

    # Or is the request actually for authenticating an existing keycard for this door? 
    try: 
        rfidkeycard = RFIDkeycard.objects.get(the_rfid=rfid)
    except:
        # no such keycard, so return response of 0
        # (or something else went wrong, but still send back no)
        return HttpResponse(0)

    # Keycard exists, so moving on to check if it's active and get allowed
    # doors (the latter is called on lockuser, so need to check if keycard is
    # active first).
    if rfidkeycard.is_active():
        for door in rfidkeycard.get_allowed_doors():
            if door.id == int(doorid): 
                # So response will be 1 -- authenticated. 
                response=1
                # Before returning, though, create the data_point attribute for
                # the current access, to build the JS chart of visitors later.

                ###################################################### 
                # create the highchart data point for this access time
                ###################################################### 
                lockuser = rfidkeycard.lockuser
                at = AccessTime(the_rfid=rfid,access_time=datetime.now().replace(tzinfo=utc), lockuser=lockuser, door=door ) # todo: access time is going to be a bit later...
                """
                at.lockuser_link_html = make_lockuser_link_html(lockuser.id, lockuser.first_name, lockuser.last_name)
                """
                # TODO: If we reuse keycards/keycard nums, AccessTime objects'
                # lockusers -- as seen on AccessTimes change_list, for ex -- will be
                # incorrect, since lockuser is the CURRENT owner of the keycard  associated with that access time, so this would not 
                # be valid for access times of the PREVIOUS owner. It's probably best to
                # associate AccessTimes with lockusers at creation time. I.e. determine
                # the current lockuser in *views.py* (check() ) and assign there.

                # Create and assign data point dict to JSONify for the access times highchart  
                x_coord = 'Date.UTC(%d,%d,%d)' % (at.access_time.year, at.access_time.month-1, at.access_time.day)
                y_coord = 'Date.UTC(0,0,0, %d,%d,%d)' % (at.access_time.hour, at.access_time.minute, at.access_time.second)
                user_name = '"%s %s"' % (at.lockuser.first_name, at.lockuser.last_name)  
                data_point_dict = {'x': x_coord, 'y': y_coord, 'user': user_name } 
                at.data_point = simplejson.dumps(data_point_dict)
                at.save()
    return HttpResponse(response)


@login_required
def initiate_new_keycard_scan(request,lockuser_object_id):
    """ Try start waiting for new keycard scan; return success/fail message """
    # If this lockuser already has a current keycard, don't proceed
    # (This should have been prevented at template level also)
    try: 
        lu = LockUser.objects.get(id=lockuser_object_id)
    except:
        response_data = {'success':False, "error_mess":"This lock user was probably not found in the system."}
        # Probably the error is DoesNotExist: LockUser matching query does not exist.
        #   but send this response on ANY type of exception
        # todo: include an error code? and log? 

        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


    if lu.get_current_rfid():
        response_data = {'success':False, 'error_mess':"This lock user is already assigned a keycard."} # Todo: So when stuff like this happens in production...  Should it sent some kind of automated error report to whomever is developing/maintaining the site? 
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        n = NewKeycardScan()

        n.waiting_for_scan = True
        n.assigner_user = request.user
        n.save()   

        response_data = {'success':True, 'new_scan_pk':n.pk}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    


# todo: 
@login_required
#def finished_new_keycard_scan(request, lockuser_object_id):
def finished_new_keycard_scan(request,new_scan_pk):
    """  Verify this is the NewKeycardScan object we initiated, that the rfid
        is not the same as that of a currently active keycard, and that we 
        haven't timed out. Then get the rfid from the newly-scanned card. 

        Also verifying __, ____, .........

        The new RFIDkeycard object is created upon LockUser save, after change_form form has been submitted.
    """
    # TODO:  raise exceptions.   
    # TODO:  Error codes to aid developers? So Staff user sees "ERROR (code 2). Try again," not "ERROR (scary message  about the exact error). Try again." ....Or just quietly log the error. 

    #if not new_scan_queryset:
    #    response_data = {'success':False, 'error_mess':"No NewKeycardScan objects at all"}
    #    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    # Verify that the scan object is the one we need - that we have the 
    #   NewKeycardScan object we started with, not one that another staff
    #   user initiated *after* us, for ex.  
    #new_scan_queryset = NewKeycardScan.objects.all()
    #new_scan_right_pk_qs = new_scan_queryset.filter(pk = new_scan_pk)  # 
    new_scan_qs = NewKeycardScan.objects.filter(pk = new_scan_pk)  
    if not new_scan_qs:
        response_data = {'success':False, 'error_mess':"No NewKeycardScan obj with pk " + new_scan_pk + "."}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    new_scan = new_scan_qs[0]
    #min_till_timeout = 2
    #timed_out, time_diff_minutes = new_scan.timed_out(minutes=min_till_timeout)
    timed_out, time_diff_minutes = new_scan.timed_out()  # defaults to two minutes
    #print colored("received tuple from new_scan.timed_out(), it's this: ", "red")
    #print colored("(" + str(timed_out) + ", " + str(time_diff_minutes) + ")", "red")
    if timed_out:
    #if new_scan.timed_out(minutes=min_till_timeout):
        #response_data = {'success':False, 'error_mess':"Sorry, the system timed out. You have %d minutes to scan the card, then hit 'Done'.... So don't take %f minutes next time, please, fatty. Run to that lock! You could use the exercise." % (min_till_timeout,time_diff_minutes)}
        default_timeout_minutes = get_arg_default(NewKeycardScan.timed_out,'minutes')
        response_data = {'success':False, 'error_mess':"Sorry, the system timed out. You have %d minutes to scan the card, then hit 'Done.' "  % default_timeout_minutes}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    if not new_scan.rfid:  
        response_data = {'success':False, 'error_mess':"NewKeycardScan does not have RFID."}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    # if waiting for new keycard to be scanned, but timed out

    # Verify that the rfid is not the same as that of another ACTIVE keycard
    keycards_with_same_rfid_qs = RFIDkeycard.objects.filter(the_rfid=new_scan.rfid)

    #for k in keycards_with_same_rfid_qs:
    for k in keycards_with_same_rfid_qs.select_related():
        if k.is_active():
            response_data = {'success':False, 'error_mess':"A keycard with the same RFID is already assigned to %s." % k.lockuser} # to do:  include actual link to this lockuser
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
            
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



    # OK, so far so good. Set waiting and ready-to-assign status,
    # grab the assigner, and save NewKeycardScan object
    new_scan.waiting_for_scan = False
    new_scan.ready_to_assign = True 
    new_scan.assigner_user = request.user  # todo:  wasn't assigner_user already set? 
    new_scan.save()

    response_data = {'success':True, 'rfid':new_scan.rfid}
    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
