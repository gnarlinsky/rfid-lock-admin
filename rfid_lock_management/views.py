from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
import rfid_lock_management.models
from datetime import datetime
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from rfid_lock_management.misc_helpers import get_arg_default
from rfid_lock_management.models import *


def do_json_resp(success, message):
    response_data = {
        'success': success,
        'error_mess': message}
    return HttpResponse(simplejson.dumps(response_data),
                        content_type="application/json")


@login_required
def chartify(request):
    """
    Return data in appropriate format for the HighCharts (JavaScript)
    AccessTime plot.  Creates a series for each door.
    """
    tooltip_dict = {}
    tooltip_dict['followPointer'] = 'false'
    tooltip_dict['pointFormat'] = '"{point.user}"'
    all_series = []
    for door in Door.objects.all():
        one_series = {}
        one_series['name'] = '"%s"' % door.name
        one_series['tooltip'] = tooltip_dict
        this_door_access_times = AccessTime.objects.filter(door=door)
        one_series['data'] = []
        for at in this_door_access_times:
            one_series['data'].append(simplejson.loads(at.data_point))
        all_series.append(one_series)
    extra_context = {'chart_data': simplejson.dumps(all_series, indent="")}
    return render_to_response('chart.html', dictionary=extra_context,
                              context_instance=RequestContext(request))


def get_allowed_rfids(request, doorid):
    """
    Returns list of allowed rfid's for the specified door in JSON format
    (update: no, spaces for now)
    """
    try:
        door = Door.objects.get(pk=doorid)
        allowed_rfids = door.get_allowed_rfids()  # list of Keycard objects
        alloweds = [keycard_obj.the_rfid for keycard_obj in allowed_rfids]
    except:  # door may not exist or any other error . . .
        alloweds = ""   # but still need to respond

    #to_json = {"doorid": int(doorid), "allowed_rfids": alloweds}
    #return HttpResponse(simplejson.dumps(to_json), content_type='application/json')

    # we don't feel like making the arduino parse c, so let's just send a list
    # of numbers separated by spaces
    return HttpResponse(' '.join(alloweds))


def check(request, doorid, rfid):
    """
    In addition to checking whether the given rfid is valid for the given door,
    this checks whether we're actually trying to assign a new keycard rather
    than authenticating. If not doing a new keycard scan, create and save an
    AccessTime.
    """
    response = 0

    # Is the request actually for new keycard assignment?
    new_scan_queryset = NewKeycardScan.objects.all()
    if new_scan_queryset:
        # Note - getting latest NewKeycardScan object by ordering by the field
        # time_initiated may not actually return the latest created object if
        # 'start scan' was hit many times in a row -- even microseconds don't
        # seem to have sufficient resolution to actually get the latest object.

        # get the latest NewKeycardScan object
        new_scan = new_scan_queryset.latest("pk")

        # Issue #e
        if new_scan.waiting_for_scan:
            # record the door the new scan request came from
            new_scan.doorid = doorid
            new_scan.rfid = rfid
            new_scan.save()
            return HttpResponse(response)

    # Or is the request actually for authenticating an existing keycard for
    # this door?  Note -- RFIDkeycard.objects.get(the_rfid=rfid) fails if there
    # is more than one item returned. Only one item would be active.
    # Issue #i
    rfidkeycards_with_same_rfid = RFIDkeycard.objects.filter(the_rfid=rfid)
    if not rfidkeycards_with_same_rfid:
        # no such keycard, so return response of 0
        return HttpResponse(0)
    else:
        for rfidkeycard in rfidkeycards_with_same_rfid:
            # Keycard exists, so moving on to check if it's active and get
            # allowed doors (the latter is called on lockuser, so need to check
            # if keycard is active first).
            if rfidkeycard.is_active():
                for door in rfidkeycard.get_allowed_doors():
                    if door.id == int(doorid):
                        # So response will be 1 -- authenticated.
                        response = 1
                        
                        ######################################################
                        # create the AccessTime for this visit
                        ######################################################
                        lockuser = rfidkeycard.lockuser
                        at = AccessTime(
                            the_rfid=rfid,
                            door=door,
                            lockuser=lockuser,
                            access_time=datetime.datetime.now()
                        )
                        # Now create and assign data point dict to JSONify for
                        # the access times highchart
                        x_coord = 'Date.UTC(%d,%d,%d)' % (
                            at.access_time.year, at.access_time.month-1,
                            at.access_time.day)
                        y_coord = 'Date.UTC(0,0,0, %d,%d,%d)' % (
                            at.access_time.hour, at.access_time.minute,
                            at.access_time.second)
                        user_name = '"%s %s"' % (
                            at.lockuser.first_name, at.lockuser.last_name)
                        data_point_dict = {
                            'x': x_coord, 'y': y_coord, 'user': user_name}
                        at.data_point = simplejson.dumps(data_point_dict)
                        at.save()

    return HttpResponse(response)


@login_required
# Issue #k
def initiate_new_keycard_scan(request, lockuser_object_id):
    """
    Try start waiting for new keycard scan; return success/fail message.
    """
    # If this lockuser already has a current keycard, don't proceed
    # (This should have been prevented at template level also)
    try:
        lu = LockUser.objects.get(id=lockuser_object_id)
    except:
        # Probably the error is DoesNotExist: LockUser matching query does not
        # exist, but send this response on ANY type of exception.
        return do_json_resp(False, "This lock user was probably not found in the system.")

    if lu.get_current_rfid():
        return do_json_resp(False, "This lock user is already assigned a keycard.")
    else:
        n = NewKeycardScan()
        n.waiting_for_scan = True
        n.assigner_user = request.user
        n.save()
        response_data = {'success': True, 'new_scan_pk': n.pk}
        # not do_json_resp, since response_data is different:
        return HttpResponse(simplejson.dumps(response_data),
                            content_type="application/json")


# TODO:  raise exceptions.
@login_required
def finished_new_keycard_scan(request, new_scan_pk):
    """
    Verify this is the NewKeycardScan object we initiated, that the rfid is not
    the same as that of a currently active keycard, and that we haven't timed
    out. Then get the rfid from the newly-scanned card.

    The new RFIDkeycard object is created upon LockUser save, after change_form
    form has been submitted.
    """
    # Verify that the scan object is the one we need - that we have the
    #   NewKeycardScan object we started with, not one that another staff
    #   user initiated *after* us, for ex.
    new_scan_qs = NewKeycardScan.objects.filter(pk=new_scan_pk)
    if not new_scan_qs:
        return do_json_resp(False,
                            "No NewKeycardScan obj with pk {}.".format(new_scan_pk))
    new_scan = new_scan_qs[0]
    min_till_timeout = 2.0
    timed_out = new_scan.timed_out(min_till_timeout)
    if timed_out:
        return do_json_resp(False,
            "Sorry, the system timed out. You have {} minutes to scan the card, then hit 'Done.' ".format(min_till_timeout))
    if not new_scan.rfid:
        return do_json_resp(False, "NewKeycardScan does not have RFID.")
    # Verify that the rfid is not the same as that of another ACTIVE keycard
    keycards_with_same_rfid_qs = RFIDkeycard.objects.filter(the_rfid=new_scan.rfid)
    for k in keycards_with_same_rfid_qs.select_related():
        if k.is_active():
            # todo: include link to this lockuser
            return do_json_resp(False,
                                "A keycard with the same RFID is already assigned to {}.".format(k.lockuser))
    # OK, so far so good. Set waiting and ready-to-assign status,
    # grab the assigner, and save NewKeycardScan object.
    new_scan.waiting_for_scan = False
    new_scan.ready_to_assign = True
    new_scan.assigner_user = request.user  # todo: assigner_user already set in initiate
    new_scan.save()
    response_data = {'success': True, 'rfid': new_scan.rfid}
    # not do_json_resp, since response_data is different:
    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
