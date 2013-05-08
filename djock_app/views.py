from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
import djock_app.models
from datetime import datetime
from django.utils import simplejson
from termcolor import colored   # temp
from django.utils.timezone import utc
from django.contrib.auth.decorators import login_required
from djock_app.misc import get_arg_default

# todo
# return series for chartit in JSON format
@login_required
def chartify(request): 

    #########################################################################
    # building array of access times/lockusers/rfids to give the javascript
    #########################################################################
    from django.utils import simplejson
    from djock_app.models import Door, AccessTime
    # todo: tool tip stays same....
    tooltip_dict = {}
    tooltip_dict['followPointer']='false'
    tooltip_dict['pointFormat']='"{point.user}"'

    all_series = []

    # a series is the access times for one door
    for door in Door.objects.all(): 
        one_series = {}
        one_series['name'] = '"%s"' % door.name
        one_series['tooltip'] = tooltip_dict
        # get all AccessTimes for this door
        #this_door_access_times = AccessTime.objects.filter(door_id=door.id)
        this_door_access_times = AccessTime.objects.filter(door=door)
        one_series['data'] = []
        for at in this_door_access_times:
            #print colored("adding data point  for door %s: %s" % (door.name, at.data_point), "white","on_blue") 
            one_series['data'].append(simplejson.loads(at.data_point))  # todo: ugh with the loads'ing           
        all_series.append(one_series)

    extra_context = {'chart_data': simplejson.dumps(all_series, indent="") } 





    return render_to_response('chart.html', dictionary=extra_context, context_instance=RequestContext(request))



# return list of rfid's allowed for all doors, or a particular door,
#   as json list 
def get_allowed_rfids(request, doorid):
    """ Returns list of allowed rfid's for the specified door in JSON format """
    # check that door id is valid. 
    #   Int of a certain length: taken care of in the urlconf
    #   Check that there even is a such 
    # if door id not valid, return ""
    # todo:  return JSON
    door = djock_app.models.Door.objects.filter(pk=doorid)    # doorid should not be pk; note, get returns an rror if no such door; filter returns an empty list
    if door:
        allowed_rfids = door[0].get_allowed_rfids()  # list of Keycard objects
        #alloweds = ",".join([keycard_obj.the_rfid for keycard_obj in allowed_rfids])
        alloweds = [keycard_obj.the_rfid for keycard_obj in allowed_rfids]
    else: # no such door
        alloweds = ""
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
    new_scan_queryset = djock_app.models.NewKeycardScan.objects.all()
    if new_scan_queryset:
        #new_scan = new_scan_queryset.latest("time_initiated")  # get the latest NewKeycardScan object, ordered by the field time_initiated (i.e. time the object was created) 
        # above may not actually return the latest created object if 'start scan' was hit a bunch of times in a row -- even microseconds won't have sufficient resolution to actually get the latest object
        new_scan = new_scan_queryset.latest("pk")  # get the latest NewKeycardScan object, as determined by pk

        # TODO: Things might go awry if someone else initiated a scan later... Currently verifying pk's later,  in
        # finished_keycard_scan, but do earlier. And pass pk info in a smarter way.

        if new_scan.waiting_for_scan == True:
            new_scan.doorid = doorid  # record the door the new scan request came from (not necessary so far) 
            new_scan.rfid = rfid
            new_scan.save()  
            return HttpResponse(response)

    # or is the request actually for authenticating an existing keycard for this door? 
    try: 
        rfidkeycard = djock_app.models.RFIDkeycard.objects.get(the_rfid=rfid)
    except:
        # no such keycard, so return response of 0
        return HttpResponse(0)
    # keycard exists, so moving on to check if it's active and get allowed doors (the latter is called on lockuser, so need to check if keycard is active first)
    if rfidkeycard.is_active():
        for door in rfidkeycard.get_allowed_doors():
            if door.id == int(doorid): 
                # so response will be 1 -- authenticated. 
                response=1
                # Before returning, though, create the data_point attribute for the current access, to build the JS chart of visitors later

                ###################################################### 
                #create the highchart data point for this access time
                ###################################################### 
                lockuser = rfidkeycard.lockuser
                at = djock_app.models.AccessTime(the_rfid=rfid,access_time=datetime.now().replace(tzinfo=utc), lockuser=lockuser, door=door ) # todo: access time is going to be a bit later...
                """
                at.lockuser_link_html = make_lockuser_link_html(lockuser.id, lockuser.first_name, lockuser.last_name)
                """
                # TODO: If we reuse keycards/keycard nums, AccessTime objects'
                # lockusers -- as seen on AccessTimes change_list, for ex -- will be
                # incorrect, since lockuser is the CURRENT owner, so this would not 
                # be valid for access times of the PREVIOUS owner. It's probably best to
                # associate AccessTimes with lockusers at creation time. I.e. determine
                # the current lockuser in *views.py* (check() ) and assign there.

                # todo:  this may be interim....
                data_point_dict = {}
                # data point dict to JSONify for the access times highchart  

                # todo: need this line:? 
                data_point = {}


                # todo:  double check -- subtracting 1 to month because Javascript starts month count at 0, I think
                data_point_dict['x'] = 'Date.UTC(%d,%d,%d)' % (at.access_time.year, at.access_time.month-1, at.access_time.day)
                data_point_dict['y'] = 'Date.UTC(0,0,0, %d,%d,%d)' % (at.access_time.hour, at.access_time.minute, at.access_time.second)
                data_point_dict['user'] = '"%s %s"' % (at.lockuser.first_name, at.lockuser.last_name)  

                at.data_point = simplejson.dumps(data_point_dict)
                at.save()

    return HttpResponse(response)


@login_required
def initiate_new_keycard_scan(request,lockuser_object_id):
    """ Try start waiting for new keycard scan; return success/fail message """
    # If this lockuser already has a current keycard, don't proceed
    # (This should have been prevented at template level also)
    try: 
        lu = djock_app.models.LockUser.objects.get(id=lockuser_object_id)
    except:
        response_data = {'success':False, "error_mess":"WTF? There's no lock user?"}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    if lu.get_current_rfid():
        response_data = {'success':False, 'error_mess':"This lock user is already assigned a keycard! You shouldn't have even gotten this far!"} # Todo: So when stuff like this happens in production...  Should it sent some kind of automated error report to whomever is developing/maintaining the site? 
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        n = djock_app.models.NewKeycardScan()

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
    # TODO:  Error codes to aid developers. So Staff user sees "ERROR (code 2). Try again," not "ERROR (scary message  about the exact error). Try again." 
    new_scan_queryset = djock_app.models.NewKeycardScan.objects.all()

    #if not new_scan_queryset:
    #    response_data = {'success':False, 'error_mess':"No NewKeycardScan objects at all"}
    #    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    # Verify that the scan object is the one we need, not one initiated later by someone else, for example.
    new_scan_right_pk_qs = new_scan_queryset.filter(pk = new_scan_pk)  # make sure we have the newKeycardScan object we started with, not one that another staff user initiated *after* us. 

    if not new_scan_right_pk_qs:
        response_data = {'success':False, 'error_mess':"No NewKeycardScan obj with pk " + new_scan_pk + "."}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    new_scan = new_scan_right_pk_qs[0]
    #min_till_timeout = 2
    #timed_out, time_diff_minutes = new_scan.timed_out(minutes=min_till_timeout)
    timed_out, time_diff_minutes = new_scan.timed_out()  # defaults to two minutes



    if timed_out:
    #if new_scan.timed_out(minutes=min_till_timeout):
        #response_data = {'success':False, 'error_mess':"Sorry, the system timed out. You have %d minutes to scan the card, then hit 'Done'.... So don't take %f minutes next time, please, fatty. Run to that lock! You could use the exercise." % (min_till_timeout,time_diff_minutes)}
        default_timeout_minutes = get_arg_default(djock_app.models.NewKeycardScan.timed_out,'minutes')
        response_data = {'success':False, 'error_mess':"Sorry, the system timed out. You have %d minutes to scan the card, then hit 'Done.' "  % default_timeout_minutes}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    if not new_scan.rfid:  
        response_data = {'success':False, 'error_mess':"NewKeycardScan does not have RFID."}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    # if waiting for new keycard to be scanned, but timed out

    # Verify that the rfid is not the same as that of another ACTIVE keycard
    keycards_with_same_rfid_qs = djock_app.models.RFIDkeycard.objects.filter(the_rfid=new_scan.rfid)
    for k in keycards_with_same_rfid_qs:
        if k.is_active():
            response_data = {'success':False, 'error_mess':"A keycard with the same RFID is already assigned to %s." % k.lockuser} # to do:  include actual link to this lockuser
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
            
    # OK, so far so good. Set waiting and ready-to-assign status,
    # grab the assigner, and save NewKeycardScan object
    new_scan.waiting_for_scan = False
    new_scan.ready_to_assign = True 
    new_scan.assigner_user = request.user  # todo:  wasn't assigner_user already set? 
    new_scan.save()

    response_data = {'success':True, 'rfid':new_scan.rfid}
    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
