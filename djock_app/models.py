from django.db import models
from django.forms import ModelForm, IntegerField
from django.contrib.auth.models import User
from django.dispatch import dispatcher
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.auth.management import create_superuser
from django.db.models import signals
from django.utils.timezone import utc
import datetime



############### TO DO #############################################
# make sure various stuff are set unique
# consistency with _var vs var
####################################################################


class Door(models.Model):
    """ Doors with RFID locks installed. """
    name    = models.CharField(max_length=50)  # e.g. "Makerspace," "Bike Project," etc.

    def __unicode__(self):
        """ Represent Door objects with their name fields """
        return u'%s' % (self.name)

    def get_allowed_rfids(self):
        """ Return the RFIDs allowed to access this Door """
        #return ", ".join([str(lu.the_rfid) for lu in self.lockuser_set.all()])
        #return self.lockuser_set.all().values_list("rfids")
        return [lu.prettify_get_current_rfid() for lu in self.lockuser_set.all()]

    def prettify_get_allowed_rfids(self):
        return ", ".join(self.get_allowed_rfids())

    def get_allowed_lockusers(self):
        """ Get the LockUsers with access to this Door """
        return ", ".join([str(lu) for lu in self.lockuser_set.all()])

    def get_allowed_lockusers_html_links(self):
        """ Returns the HTML (which will have to escape) with links to /lockuser/the_id/ to display on the Door change list page """

        lockuser_links_list = []
        for lockuser in self.lockuser_set.all():
            lockuser_link_html =  "<a href='../lockuser/%d/'>%s</a>" %  (lockuser.id, lockuser)
            lockuser_links_list.append(lockuser_link_html)
        return ", ".join(lockuser_links_list)

    # Django will HTML-escape the output by default. If you'd rather not escape the output of the method,
    # give the method an allow_tags attribute whose value is True.
    get_allowed_lockusers_html_links.allow_tags = True

    # to do:
    def get_all_access_times(self):
        pass


class NewKeycardScan(models.Model):
    """ For checking whether the current request is for authenticating a keycard or assigning new keycard. """
    time_initiated = models.DateTimeField(auto_now_add=True)
    waiting_for_scan = models.BooleanField(default=True) 
    doorid = models.CharField(max_length=50)   # doorid as in the requesting url
    rfid = models.CharField(max_length=10)   # rfid as in the requesting url
    # to do: additional parameters for door, rfid? 

    def timed_out(self,minutes=2):
        """ Check whether specified number of minutes have passed since user indicated they were going to go scan in a card for assigning it.  Defaults to 2 minutes. """
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        max_time = datetime.timedelta(minutes=minutes)
        if now - self.time_initiated > max_time:
            return True
        return False



class RFIDkeycard(models.Model):
    """ Let's try this: door access represented by a (reusable) RFID *keycard*
    (or keyfob or whatever) assigned to a LockUser. Also specifies the door(s)
    this RFID has access to; can get times when it was used (i.e. AccessTimes),
    and ........

    Note for nk when  get to LockUser: when a lockuser is "deactivated," their card is deactivated as well  (but not the other way around, by the way!) -
        and the date_revoked will be automatically populated (so in addition to manually revoking a card).
         This means that if there's no revoked date, the card is still active, and don't need
         a separate is_active field here... just ask: is_active() --> can just check if there's a revoked date,
         OR if today's date is between assigned/revoked...
    """
    the_rfid    = models.CharField(max_length=10,null=True,editable=True) # the radio-frequency id
    date_revoked = models.DateTimeField(null=True, blank=True) # note that blank=True is at form validation level,
    # while null=True is at db level
    # This should not be a field that staff users can fill in.  It should be created
    # automatically when the associated **LockUser** is deactivated

    date_created = models.DateTimeField(auto_now_add=True)

    ####################################################################
    # Switching to Foreign Key relationship for RFIDkeycard/LockUser
    ####################################################################
    # An RFIDkeycard can only be connected to one LockUser; a LockUser
    #   can have multiple RFIDkeycards (though only one can be active
    #   at a time).
    #   - So now we have a ForeignKeyField in **RFIDkeycard** to LockUser,
    #   - with unique=True, meaning that in the RFIDkeycard table, the
    #     each LockUser field must be unique (i.e. no sharing of keycards)
    #
    # So now, to get a lockuser: rfidkeycard_object.lockuser
    #         to get a lockuser's field: rfidkeycard_object.lockuser.first_name,
    #                                    rfidkeycard_object.lockuser.doors  ??? (m2m)
    #                                    rfidkeycard_object.lockuser.get_blah ???  func???
    ####################################################################
    lockuser = models.ForeignKey("LockUser")


    # Nope.  Don't have to do the below; just use auto_now_add
    #def __init__(self,*args,**kwargs):   # i don't have to include args, kwargs, right?
    #    """ We want to automatically create the date this keycard was created/assigned. """
    #    super(RFIDkeycard, self).__init__(*args,**kwargs)
    #    # date_created = blah blah blah

    def __unicode__(self):
        # Represent keycard object with the rfid number (which may not be unique, blah blah
        #   blah, but it's a useful for showing on the page for a particular LockUser, for ex.
        return u'%s' % (self.the_rfid)

    def get_date_assigned(self):
        # get from __init__
        pass

    def get_allowed_doors(self):
        """ Get the Doors this user is allowed access to. """
        if self.lockuser:
            return self.lockuser.get_allowed_doors()
        else:
            return None

    def prettify_get_allowed_doors(self):
        if self.lockuser:
            return self.lockuser.prettify_get_allowed_doors()
        else:
            return None

    def get_allowed_doors_html_links(self):
        if self.lockuser:
            return self.lockuser.get_allowed_doors_html_links()
        else:
            return None
    # Django will HTML-escape the output by default. If you'd rather not escape the output of the method,
    # give the method an allow_tags attribute whose value is True.
    get_allowed_doors_html_links.allow_tags = True

    def is_active(self):
        if self.date_revoked: # additional checks?
            return False
        else:
            return True

    def deactivate(self):
        # When time zone support is enabled, Django uses time-zone-aware 
        # datetime objects. If your code creates datetime objects, they should
        # be aware too.
        #now = datetime.datetime.now()
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        self.date_revoked = now


    def save(self,*args,**kwargs):
        """ Overriding save():  When assign new keycard, if the LockUser was inactive before, they will
        automatically become active.
        """
        # Check if the object is in the database yet. If no pk, means it hasn't
        #   been saved yet -- i.e. we're creating this RFIDkeycard. Note that 
        #   at this point, other attributes *are* available, like lockuser, 
        #   they just haven't been saved yet.
        if not self.pk and self.lockuser: 
            if self.lockuser.activate == False: 
                # activate the keycard's lock user, and save
                self.lockuser.activate = True
                self.lockuser.save()
        
        # and now save the keycard itself
        super(RFIDkeycard,self).save(*args,**kwargs)


        


class AccessTime(models.Model):
    the_rfid           = models.CharField(max_length=10,null=True) # the radio-frequency id, however represented....
    access_time    = models.DateTimeField(null=True)    # the time the rfid was used

    def get_this_lockuser(self):
        """ Return the user's name associated with the RFID for this access time """
        # Get RFIDkeycard (there should only be one!) with the rfid associated with this access time;
        # get the lock user names associated with those RFIDkeycards
        _rfid_keycard = RFIDkeycard.objects.all().filter(the_rfid__exact=self.the_rfid)
        if _rfid_keycard:
            return _rfid_keycard[0].get_this_lockuser()
        else:
            return None


class LockUser(models.Model):
    """ (Despite the misleading name, LockUsers are not subclassed Users, but subclassed Models.) """


    ################################################################################
    # doors should be limited to the Doors, and should show up as checkable items for a specific LockUser.
    ################################################################################
    # (Also, which specific doors are check-able/show up should depend on the permissions [or staff vs
    # superuser, etc.] for the person doing the assigning. E.g. someone only involved with the Bike Project
    # shouldn't be able to assign keycard access to the Makerspace door.
    doors = models.ManyToManyField(Door,blank=True)

    ####################################################################
    ####  contact infoz ######
    ####################################################################
    first_name      = models.CharField(max_length=50)
    middle_name     = models.CharField(max_length=50,blank=True)
    last_name       = models.CharField(max_length=50)
    address         = models.CharField(max_length=100,blank=True)
    email           = models.EmailField(blank=True)  # blank okay for NOW, later - required
    phone_number    = models.IntegerField(max_length=30,null=True,blank=True) # later - required
    birthdate       = models.DateField(null=True)

    # Is this person allowed access? (Non-superuser staff should not have the ability to delete models --
    # but rather to DEACTIVATE.)
    #   Note that a lockuser can be activated, but have no keycard. 
    activate       =   models.BooleanField(default=False)   #i.e. defaults to deactivated

    # "Deactivate keycard?" on LockUser, RFIDkeycard change_form:
    deactivate_current_keycard = models.BooleanField(default=False)    # So, upon creation, the RFIDkeycard is activated automatically

    def save(self, *args, **kwargs):
        """ Why overriding save(): 
            - If the Lockuser has been deactivated, its current keycard should be deactivated as well.
            - We'll deactivate a LockUser's current keycard here, if deactivate_current_keycard is checked
              on the LockUser's change_form. 
        """
        # saving before any work with keys and m2m, to obtain self.id
        super(LockUser, self).save(*args, **kwargs)

        #rfid_keycards = RFIDkeycard.objects.filter(...)

        try:
            # there should be at most one... for now just get the first one
            current_keycard = self.get_current_rfid()[0]   # self or lu? 
        except:
            current_keycard = None

        # If the Lockuser has been deactivated, its current keycard should be deactivated as well.
        #if lu.activate == False:   # not self.activate?
        # Note that it would seem that this conditional would actually also
        # cover the case where just created a current keycard, and need to 
        # automatically set user to be activated.  However, we can do that in the
        # RFIDkeycard's save(), since there we can check whether RFIDkeycard
        # object was just created
        if current_keycard and self.activate == False:   
            #current_keycard.date_revoked = datetime.now()
            current_keycard.deactivate()
            current_keycard.save()# save keycard if you have changed it

        # We'll deactivate a LockUser's current keycard here, if deactivate_current_keycard is checked on the LockUser's change_form. 
        if current_keycard and self.deactivate_current_keycard:
            #current_keycard.date_revoked = datetime.now()
            current_keycard.deactivate()
            current_keycard.save()# save keycard since have changed it

            self.deactivate_current_keycard = False   # because no current keycard to deactivate anymore

            super(LockUser, self).save(*args, **kwargs)  # save again

            
        # save obj again if you want
        #lu.save()
        #return lu


    #rfids            = models.ManyToManyField("RFIDkeycard", help_text = "(Fake-assign new keycard)", blank=True)  # the field labeled "rfids" should not be required -- it's ok to have an active LockUser that is not currently assigned a keycard.
    ####################################################################
    # Switching to Foreign Key relationship for RFIDkeycard/LockUser
    ####################################################################
    # An RFIDkeycard can only be connected to one LockUser; a LockUser
    #   can have multiple RFIDkeycards (though only one can be active
    #   at a time).
    #   - So now we have a ForeignKeyField in **RFIDkeycard** to LockUser,
    #   - with unique=True, meaning that in the RFIDkeycard table, 
    #     each LockUser field must be unique (i.e. no sharing of keycards)
    #
    #      - so rfids changes from a field to get_rfids()?  How to get
    # To get the RFIDkeycards assigned to this LockUser: lockuser_object.rfidkeycard_set.all()
    ####################################################################
    def get_all_rfids(self):
        """ Get all RFID's associated with this Lock User (i.e. not just the current one, which is just the rfid field) """
        return self.rfidkeycard_set.all()

    def prettify_get_all_rfids(self):
        """ Or... if get_all_rfids() return self.rfids, do I need this? Or any other prettify method? """
        _rfid_keycards = self.get_all_rfids()
        _rfid_nums_list = [str(r.the_rfid) for r in _rfid_keycards]
        return ", ".join(_rfid_nums_list)

    def get_current_rfid(self):
        """ Get the currently active RFID
        Of all RFID's associated with this LockUser, get the one that's active, i.e. has not been revoked. 
        """
        #_rfid_keycards = self.rfids.all()   # or call get_all_rfids for consistency
        _rfid_keycards = self.get_all_rfids()
        _curr_rfid = _rfid_keycards.filter(date_revoked=None)  
        return _curr_rfid
       
    def prettify_get_current_rfid(self):
        """ Returns results of get_current_rfid(), but as a nice pretty string.
        There is probly a better way to do this.... 
        ******* Well, you could just return curr_rfid.the_rfid !!!!!!!!!
        And for multiple vals/queryset, maybe there's a get or something like that?
        """
        curr_rfid = self.get_current_rfid()
        _curr = [str(c.the_rfid) for c in curr_rfid]  # again! yes, stupid, but i haven't coded anythign yet 
            #to account for there only being one current per person!/my fake data forces me to do this...  
        return ", ".join(_curr)

    def get_allowed_doors(self):
        """ Get the Doors this user is allowed access to. """
        return self.doors.all()            # don't have to prettify if just return self.doors?

    def prettify_get_allowed_doors(self):
        _doors = self.get_allowed_doors()
        _door_names_list = [d.name for d in _doors] 
        return ", ".join(_door_names_list)

    def get_allowed_doors_html_links(self):
        """ Returns the HTML (which will have to escape) with links to /door/the_id/ to display on the LockUser change list page """
        doors_links_list = []
        for door in self.doors.all():
            door_link_html =  "<a href='../door/%d/'>%s</a>" %  (door.id, door.name) 
            doors_links_list.append(door_link_html)
        return ", ".join(doors_links_list)
    # Django will HTML-escape the output by default. If you'd rather not escape the output of the method, 
    # give the method an allow_tags attribute whose value is True.
    get_allowed_doors_html_links.allow_tags = True

    # TO DO here...  Hmm, something feels weird with the curr_rfid_only argument. Biggest issue is
    # how to pass arguments to list_display and fieldsets in admin. It's technically possible but
    # it's annoying
    # (http://stackoverflow.com/questions/14033182/list-display-with-a-function-how-to-pass-arguments). 
    # Wouldn't it more consistent/comprehensible/Pythonic to create *separate methods* for (1)
    # getting all access times for all rfid's a lockuser has ever had and (2) only the current
    # active one. 
    def get_all_access_times(self, curr_rfid_only=True):
        """ Returns list of all access times for this user, which means that the search should include any other
        RFID's this LockUser ever had. In other words, the search is by *person*, not by RFID.
        Although we're in the process of deciding whether there should only be one keycard/RFID per person. see the comment for RFIDkeycard.get_allowed_doors().
        """

        if curr_rfid_only:
            #curr_rfid = self.get_current_rfid()  
            # until fix the only-1-curr-rfid thing, the above actually may refer to multiple instances...  
            # So just for now, for the purposes of getting on with this, just taking the first item
            # if it exists. Although we're in the process of deciding whether there should only be
            # one keycard/RFID per person. see the comment for RFIDkeycard.get_allowed_doors()
            if self.get_current_rfid():
                curr_rfid_keycard = self.get_current_rfid()[0]

                # Get QuerySet of all AccessTime objects whose RFID matches this LockUser's current RFID:
                at_query_set = AccessTime.objects.all().filter(the_rfid__exact=curr_rfid_keycard.the_rfid)
                # Now get the access_time field of each AccessTime object
                all_access_times_list = [access_time_object.access_time for access_time_object in at_query_set]
            else:  # no current rfid/lockuser deactivated
                all_access_times_list = None
        #else:
            # records matching RFIDs in previous_rfid and rfid
            #_rfid_keycards = self.get_all_rfids()

        if all_access_times_list:
            a = all_access_times_list[0]
        return all_access_times_list

    ######Note, stuff is not consistent among these get_blah's because sometimes I'm returning the OBJECT, sometimes actual fields of it

    def prettify_get_all_access_times(self,curr_rfid_only=True):
        """ prettify and sort """
        _all_access_times_list = self.get_all_access_times()
        if _all_access_times_list:
            _all_access_times_list.sort()
            _all = [ at.ctime() for at in _all_access_times_list]
            return ", ".join(_all)
        else:
            return None
        

    def get_last_access_time(self, curr_rfid_only=True):
        """ Get the last time this person used the lock. Same story with current RFID vs previous one as in the
        comment for get_all_access_time().
        """
        access_times = self.get_all_access_times(curr_rfid_only=curr_rfid_only)
        
        # sort dates and grab the last one
        if access_times:
            access_times.sort()
            return access_times[-1]  
        else:
            return None

    def prettify_get_last_access_time(self):  
        _last = self.get_last_access_time()
        if _last:
            return _last.ctime()
        else:
            return None

    def __unicode__(self):
        """ In the list of AcessTimes, for example, LockUsers will be represented with their first and last names """
        return u'%s %s' % (self.first_name, self.last_name)





####################################################################
# Prevent interactive question about wanting a superuser created.
####################################################################


# From http://stackoverflow.com/questions/1466827/ --
#
# Prevent interactive question about wanting a superuser created.  (This code
# has to go in this otherwise empty "models" module so that it gets processed by
# the "syncdb" command during database creation.)
signals.post_syncdb.disconnect(
    create_superuser,
    sender=auth_models,
    dispatch_uid='django.contrib.auth.management.create_superuser')


# Create our own test user automatically.

def create_testuser(app, created_models, verbosity, **kwargs):
  if not settings.DEBUG:
    return
  try:
    auth_models.User.objects.get(username='test')
  except auth_models.User.DoesNotExist:
    print '*' * 80
    print 'Creating test user -- login: test, password: test'
    print '*' * 80
    assert auth_models.User.objects.create_superuser('test', 'x@x.com', 'test')
  else:
    print 'Test user already exists.'

signals.post_syncdb.connect(create_testuser,
    sender=auth_models, dispatch_uid='common.models.create_testuser')


######################### notes ######################################
# Note - no need to do explicit memoization, I think. From the docs: 
# "In a newly created QuerySet, the cache is empty. The first
#  time a QuerySet is evaluated -- and, hence, a database query happens -- Django 
#  saves the query results in the QuerySet's cache and returns the results that have
#  been explicitly requested (e.g., the next element, if the QuerySet is being
#  iterated over). Subsequent evaluations of the QuerySet reuse the cached results."
####################################################################



"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

content_type = ContentType.objects.get(app_label='djock_app', model='LockUser')
permission = Permission.objects.get_or_create(codename='can_manage_door',\   # or just get(...  ??
                                       name='Can Manage Door 1',\
                                       content_type=content_type)
"""


