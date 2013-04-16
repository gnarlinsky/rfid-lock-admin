from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
import djock_app.models
import random
from datetime import datetime
from django.utils import simplejson
from termcolor import colored   # temp
from django.utils.timezone import utc

# todo:  remove or make "private"
def generate_random_access_times(request=None,shell=False, min_t=10, max_t=10):
    """ just for dev - generate random access times in a specified range """
    if not shell:
        min_num_times = int(request.POST.get('min_num_times'))
        max_num_times = int(request.POST.get('max_num_times'))
    else:
        min_num_times = int(min_t)
        max_num_times = int(max_t)
    
    # need to call this from other places (like in the interpreter), so moving to its func
    make_access_times(min_num_times, max_num_times)
    if not shell:
        return HttpResponseRedirect("/lockadmin/")
    else:
        return "done"



"""
# todo: is there a way to use allow_tags or that functionality without using a method? 
# todo:  callback...things.. how to get the url to an object... i feel that i've encountered this somewhere......
def make_lockuser_link_html(the_id, first_name, last_name, middle_name = ""):
    # todo: middle name
    link = "<a href='../lockuser/%d/'>%s %s</a>" % (the_id, first_name, last_name)
    return link
make_lockuser_link_html.allow_tags = True
# todo:  not actually allowing tags 
"""

def make_access_times(min_num_times, max_num_times):
    # for each keycard in the system, generate a random number of access times, in the range specified in the form
    for keycard in djock_app.models.RFIDkeycard.objects.all():
        for i in range(random.randint(min_num_times,max_num_times)):
            #AccessTime(the_rfid=keycard.the_rfid, access_time=get_random_time()).save()
            door = random.choice(keycard.lockuser.doors.all())
            if door.id == 1:   # door 1:  only certain days of the week
                j = 0
                while j<1:
                    the_date_time = get_random_time()
                    if (the_date_time.weekday()==5 or the_date_time.weekday()==6 or the_date_time.weekday()==4):
                        lockuser = keycard.lockuser
                        at=djock_app.models.AccessTime(the_rfid=keycard.the_rfid, access_time=the_date_time, lockuser=lockuser, door=door)
                        """
                        at.lockuser_link_html = make_lockuser_link_html(lockuser.id, lockuser.first_name, lockuser.last_name)
                        at.lockuser_name_html = lockuser_link_html
                        at.save()
                        """
                        # todo
                        assign_data_point_dict_and_save(at)
                        j+=1
            elif door.id == 2:   # door 2:  more than all others
                j = 0
                while j<5:
                    the_date_time = get_random_time()
                    lockuser = keycard.lockuser
                    at=djock_app.models.AccessTime(the_rfid=keycard.the_rfid, access_time=the_date_time, lockuser=lockuser, door=door )
                    """
                    at.lockuser_link_html = make_lockuser_link_html(lockuser.id, lockuser.first_name, lockuser.last_name)
                    """
                    at.save()
                    assign_data_point_dict_and_save(at)
                    j+=1
            elif door.id == 3: # door 3: only for 4 hours during the day
                j = 0
                while j<5:
                    the_date_time = get_random_time()
                    if the_date_time.hour >15 and the_date_time.hour < 19:
                        lockuser = keycard.lockuser
                        at=djock_app.models.AccessTime(the_rfid=keycard.the_rfid, access_time=the_date_time, lockuser=lockuser, door=door)
                        """
                        at.lockuser_link_html = make_lockuser_link_html(lockuser.id, lockuser.first_name, lockuser.last_name)
                        """
                        at.save()
                        assign_data_point_dict_and_save(at)
                        j+=1
            #djock_app.models.AccessTime(the_rfid=keycard.the_rfid, access_time=get_random_time(), lockuser=keycard.lockuser, door=random.choice(keycard.lockuser.doors.all())).save()
            else:  # all other doors
                the_date_time = get_random_time()
                lockuser = keycard.lockuser
                at=djock_app.models.AccessTime(the_rfid=keycard.the_rfid, access_time=the_date_time, lockuser=lockuser, door=door, )
                """
                at.lockuser_link_html = make_lockuser_link_html(lockuser.id, lockuser.first_name, lockuser.last_name)
                """
                at.save()
                assign_data_point_dict_and_save(at)
    return at


from random import randrange
from datetime import timedelta, datetime
def get_random_time():
    """ This function will return a random datetime between two datetime objects.  """
    now = datetime.utcnow().replace(tzinfo=utc)   
    time_period = timedelta(days=180) # about half a year
    start = now - time_period  
    time_period_seconds = time_period.total_seconds()
    random_second = randrange(time_period_seconds)
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
        new_scan = new_scan_queryset.latest("time_initiated")  # get the latest NewKeycardScan object, ordered by the field time_initiated (i.e. time the object was created) 
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
                response=1

                #print colored("**** creating and saving accesstime *****","red","on_white")
                #at = djock_app.models.AccessTime(the_rfid=rfid,access_time=datetime.utcnow().replace(tzinfo=utc), lockuser=rfidkeycard.lockuser, door=djock_app.models.Door.objects.get(id=int(doorid)))  # todo: access time is going to be a bit later...
                #at = djock_app.models.AccessTime(the_rfid=rfid,access_time=datetime.utcnow().replace(tzinfo=utc), lockuser=rfidkeycard.lockuser, door=door) # todo: access time is going to be a bit later...
                lockuser = rfidkeycard.lockuser
                at = djock_app.models.AccessTime(the_rfid=rfid,access_time=datetime.utcnow().replace(tzinfo=utc), lockuser=lockuser, door=door ) # todo: access time is going to be a bit later...

                """
                at.lockuser_link_html = make_lockuser_link_html(lockuser.id, lockuser.first_name, lockuser.last_name)
                """
                # To do: middle name

                # TODO: If we reuse keycards/keycard nums, AccessTime objects'
                # lockusers -- as seen on AccessTimes change_list, for ex -- will be
                # incorrect, since lockuser is the CURRENT owner, so this would not 
                # be valid for access times of the PREVIOUS owner. It's probably best to
                # associate AccessTimes with lockusers at creation time. I.e. determine
                # the current lockuser in *views.py* (check() ) and assign there.


                    
                # todo:  this may be interim....
                # create the highchart data point for this access time

                at.save() 
                assign_data_point_dict_and_save(at)  # todo:  this is interim.... (?)
    return HttpResponse(response)


# todo - see sticky (x) 
def assign_data_point_dict_and_save(at):
    #print colored("----assign_data_point_dict_and_save----------------------", "magenta")
    data_point_dict = {}

    # todo:  here? 
    # data point dict to JSONify for the access times highchart  
    data_point = {}
    data_point_dict['x'] = 'Date.UTC(%d,%d,%d)' % (at.access_time.year, at.access_time.month, at.access_time.day)
    data_point_dict['y'] = 'Date.UTC(0,0,0, %d,%d,%d)' % (at.access_time.hour, at.access_time.minute, at.access_time.second)
    data_point_dict['user'] = '"%s %s"' % (at.lockuser.first_name, at.lockuser.last_name)  
    # todo: 
    #  which is best? the above or, for example, 
    #       data_point_dict['user' = '"%s %s"' % (rfidkeycard.lockuser.first_name, rfidkeycard.lockuser.last_name) 
    # without at.save()

    # todo:   JSONify, assign to AccessTime field
    at.data_point = simplejson.dumps(data_point_dict)
    #print colored("just assigned this dict (here str):  %s" % str(data_point_dict), "white","on_magenta")

    # and save everything
    at.save()

def initiate_new_keycard_scan(request,lockuser_object_id):
#def initiate_new_keycard_scan(request):

    # If this lockuser already has a current keycard, don't proceed
    # (This should have been prevented at template level also)
    try: 
        lu = djock_app.models.LockUser.objects.filter(id=lockuser_object_id)
    except:
        response_data = {'success':False, "error_mess":"WTF? There's no lock user?"}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    if lu[0].get_current_rfid():
        response_data = {'success':False, 'error_mess':"This lock user is already assigned a keycard! You shouldn't have even gotten this far!"} # Todo: So when stuff like this happens in production...  Should it sent some kind of automated error report to whomever is developing/maintaining the site? 
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        n = djock_app.models.NewKeycardScan()
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
    new_scan_queryset = djock_app.models.NewKeycardScan.objects.all()
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
    keycards_with_same_rfid_qs = djock_app.models.RFIDkeycard.objects.filter(the_rfid=new_scan.rfid)
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
