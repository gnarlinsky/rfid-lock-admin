#from django.views.generic.simple import redirect_to, direct_to_template
from django.http import HttpResponse
from django.shortcuts import render_to_response
from djock_app.models import Door, LockUser, RFIDkeycard, AccessTime
import random

def fake_assign(request):
    """ just generate a random number to simulate an actual keycard being scanned in and the num retrieved """
    fake_rfid = random.randint(1000000000,9999999999)
    # template is change_form.html?  really?
    return render_to_response('admin/djock_app/change_form.html', {'fake_rfid': fake_rfid} )


    # hmm fuck that actually. maybe play a bit more with what to return, but try to create a custom template tag, like {{ fake_rfid }}. Good # thing to learn anyways. 


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
    Door perms won't be saved though. Fuck it. Just make a note by the button about that or something.  
    or in the code for the activate method 

If there is already a keycard assigned, and it's active, show a Deactivate button:
    keycard objects should have deactivate() method that will set is_active of keycard to false and set doors to null. 


wait........   Can I do this:   you know the dropdown actions... Can't I have those appear on the individual object's page as well????  Because those would be really easy to define in admin.
    Update:  answer -- yeah, I guess you can do this.  http://stackoverflow.com/questions/2805701/is-there-a-way-to-get-custom-django-admin-actions-to-appear-on-the-change-view
    Whatever.  OK, yes, it's going to be gross to see 'activate user' as well as 'activate keycard' but... whatever.   you can restrict those later. 

IF SOMETHING IS NOT ASSOCIATED WITH A SPECIFIC TEMPLATE/DIFFERENT PAGE, I REALLY DON'T WANT TO MAKE A VIEW FOR IT!   IT SHOULD CALL SOME METHOD I DEFINE IN ADMIN.PY!!!!!  Which honestly should just call a model method. like blah.activate().  


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

        Well, what happens when adding a new rfid num for a door? OK, change_list will just show each Door. With a checkmark.  If you check a certain Door, it's list of ok rfid nums would get updated. But how to do this list? 

        Does this make sense OOPily, though? Should that be a keycard field? It makes sense to ask Doors who can access them. But...........
        But.... aren't we dealing with keycards? so maybe it's the keycard that shold have manytomany to doors. 

        then: we can access rfidkeycard.doors and door.rfidkeycard_set
        then can do add/remove like https://docs.djangoproject.com/en/dev/ref/models/relations/#django.db.models.fields.related.RelatedManager. 
        blah  = RFIDKeycard.objects.get  some specific card
        d = Door.objects.blah blah however you get a specific door
        d.rfidkeycard_set.add(blah)
        or .remove(blah) ........
            - **so remember this for active/inactive shit.   don't have to check that because deactivation should
              remove(), and activation should add()


UPDATE !!!!!!!!!!!!!!!!!    doors should be a lockuser field, not rfidkeycard field 
and, as a consequence of that and other shit.........
FUCK HAVING SEPARATE RFIDKEYCARD OBJECTS. IT REALLY DOES ADD EXTRA COMPLEXITY.   IT'S NOT LIKE THERE ARE GOING TO BE more than one keycard per person.  SHIT HAS BEEN CHANGED SINCE I TALKED TO ERICH ABOUT THIS.  THE WHOLE REASON FOR THE KEYCARD SHIT WAS... I DON'T REMEMBER.  BUT FUCK IT. And what about the shit with the revoked time?  Well, i don't even remember the point of that anymore...  but a deactivated keycard ==  deactivated lockuser!





LATER........
- When a user is modified or added (in terms of being active at all or more/fewer doors access), e-mail all the staff. 
"""


