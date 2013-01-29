from django.db import models

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

   # def get_active_allowed_lockusers(self):
   #     """ So a more specific case of get_allowed_lockusers()."""
   #  but wait......    with the current setup, are inactive lockusers still associated with
   #  doors?

class RFIDkeycard(models.Model):
    """ Let's try this: door access represented by a (reusable) RFID *keycard*
    (or keyfob or whatever) assigned to a LockUser. Also specifies the door(s)
    this RFID has access to; can get times when it was used (i.e. AccessTimes),
    and ........

    Note for nk when  get to LockUser: when a lockuser is "deactivated," their card is deactivated as well -
        and the date_revoked will be automatically populated (so in addition to manually revoking a card).
         This means that if there's no revoked date, the card is still active, and don't need
         a separate is_active field here... just ask: is_active() --> can just check if there's a revoked date,
         OR if today's date is between assigned/revoked...
    """
    the_rfid    = models.IntegerField(max_length=24,null=True) # the radio-frequency id
    date_revoked = models.DateTimeField(null=True, blank=True) # note that blank=True is at form validation level, while null=True is at db level
    # actually, this should not be a field that staff users can fill in.  It should be created
    # automatically when the associated **LockUser** is deactivated!

    date_created = models.DateTimeField(auto_now_add=True) 

    # Nope.  Don't have to do the below; just use auto_now_add
    #def __init__(self,*args,**kwargs):   # i don't have to include args, kwargs, right? 
    #    """ We want to automatically create the date this keycard was created/assigned. """
    #    super(RFIDkeycard, self).__init__(*args,**kwargs)
    #    # date_created = blah blah blah        

    def __unicode__(self):
        # Represent keycard object with the rfid number (which may not be unique, blah blah
        #   blah, but it's a useful for showing on the page for a particular LockUser, for ex.
        return u'%d' % (self.the_rfid)

    def get_date_assigned(self): 
        # get from __init__
        pass
    
    def get_this_lockuser(self):
        return ", ".join([str(lu) for lu in self.lockuser_set.all()])


    # not even using anywhere... ??
    def get_allowed_doors(self):
        """ Get the Doors this user is allowed access to. """
        lu = get_this_lockuser()
        return lu.doors
    


    # def get_access_times(self):
    #   """ Get the access times associated with this keycard """
    
    # def is_active(self):
    # """ Hmm...  ???   based on - is today's date between date assigned and date revoked.  ???  
    #  Or actually based on the is_active FIELD in LockUser...?

class AccessTime(models.Model):
    ########### FK?????????????????????????????????????? ###############
    # Hmm, going with no.  The accessTime is associated with a certain key, period. 
    #rfid           = models.ForeignKey('RFIDkeycard')
    the_rfid           = models.IntegerField(max_length=24,null=True) # the radio-frequency id, however represented....
    access_time    = models.DateTimeField(null=True)    # the time the rfid was used

    #def __unicode__(self):
       # """ The default looks like 'Dec. 10, 2012, 6 a.m.', but going for more detail with ctime"""
       # """Well, that was the plan, but this is not having an affect """
        #return self.access_time.isoformat()

    def get_this_lockuser(self):
        """ Return the user's name associated with the RFID for this access time """
        ################################################################################
        #Or should there be only one get_this_user method in another class, and any other get_this_lockuser
        # would call that one? 
        #  So.......   this would take the rfid as an argument and then call the rfid keycard user? but
        #  wouldn't that one be limited to active keycard users?   Blech, just think about this later. It's
        #  probly just a matter of slightly changing the filter parameters.
        ################################################################################
        # Get QuerySet of all LockUser objects whose RFIDkeycard rfid number  matches the RFID associated with this AccessTime
        #_at_query_set = LockUser.objects.filter(rfid_num__exact=self.rfid)

        # to do: look through past RFID's?
        #if _at_query_set:
        #    return _at_query_set[0]   # There SHOULD only be one. Check for that. 
        #else: # nobody is assigned this RFID
        #    return "No associated user found"
        #return ", ".join([str(lu) for lu in self.lockuser_set.all()])
        #LockUser.objects.all().rfids????????
        # Get RFIDkeycard (there should only be one!) with the rfid associated with this access time; 
        # get the lock user names associated with those RFIDkeycards
        _rfid_keycard = RFIDkeycard.objects.all().filter(the_rfid__exact=self.the_rfid)
        if _rfid_keycard:
            return _rfid_keycard[0].get_this_lockuser()
        else:
            return None
        

class LockUser(models.Model):
    """ (Despite the misleading name, LockUsers are not subclassed Users, but subclassed Models.) """
    # The radio-frequency id, however it will be represented:
    # The first argument is what the label for this field should read/the verbose name (optional,
    # defaults to same as field's name, with spaces converted to underscores)
    #the_rfid            = models.IntegerField("RF ID",max_length=24,null=True, help_text = "some blackboxing is about to happen...   button to fake-assign, etc.")
    #rfid           = models.ManyToManyField(RFID,through='Openership')     # defaults to the current active rfid for
    # this user?
    #rfid           = models.ForeignKey(RFID,related_name='lockusers')
    # nope, something's wrong here. At the very least, if you're going to have a field FK'd to another model, don't call it
    # *num*. Just call it rfid, and actually call RFIDkeycard's rfid field "rfid_num."  
    #rfid           = models.ForeignKey('RFIDkeycard',null=True)
    
    # So there may be multiples, perhaps even all inactive. There should be a method to get the
    # *current* one. 
    rfids            = models.ManyToManyField("RFIDkeycard", help_text = "some blackboxing is about to happen...   button to fake-assign, etc.")

    # doors should be limited to the Doors, and should show up as checkable items for a specific LockUser. 
    ################################################################################
    # (Also, which specific doors are check-able/show up should depend on the permissions [or staff vs
    # superuser, etc.] for the person doing the assigning. E.g. someone only involved with the Bike Project
    # shouldn't be able to assign keycard access to the Makerspace door. 
    doors = models.ManyToManyField(Door)


    ####  contact infoz ######
    first_name      = models.CharField(max_length=50)
    middle_name     = models.CharField(max_length=50,blank=True)
    last_name       = models.CharField(max_length=50)
    address         = models.CharField(max_length=100,blank=True)
    email           = models.EmailField()
    phone_number    = models.IntegerField(max_length=30,null=True)
    birthdate       = models.DateField(null=True)

    # Is this person allowed access? (Non-superuser staff should not have the ability to delete models -- 
    # but rather to DEACTIVATE.)  Note:  a deactivated keycard == deactivated user
    #is_active       =   models.BooleanField(default=False)

    def is_active(self):
        """ Determine whether this lock user is active, based on whether they have a current active rfid """
        if self.get_current_rfid():
            return True
        else:
            return False


    def get_all_rfids(self):
        """ Get all RFID's associated with this Lock User (i.e. not just the current one, which is just the rfid field) """
        return self.rfids.all()

    def prettify_get_all_rfids(self):
        _rfid_keycards = self.get_all_rfids()
        _rfid_nums_list = [str(r.the_rfid) for r in _rfid_keycards]
        return ", ".join(_rfid_nums_list)

    def get_current_rfid(self):
        """ Get the currently active RFID
        Of all RFID's associated with this LockUser, get the one that's active, i.e. has not been revoked. 
        """
        #_rfid_keycards = self.rfids.all()   # or call get_all_rfids for consistency
        _rfid_keycards = self.get_all_rfids()
        curr_rfid = _rfid_keycards.filter(date_revoked=None)  # there should only be one or 0 but obviously i'm not doing any kind of checking or exception handling or anything....         
        return curr_rfid
       
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
        return self.doors.all()

    def prettify_get_allowed_doors(self):
        _doors = self.get_allowed_doors()
        _door_names_list = [d.name for d in _doors] 
        return ", ".join(_door_names_list)
        
    ######################################## hmmmmmm.........  hold up.  
   # Should access times be a manytomany here???
    def get_all_access_times(self, curr_rfid_only=True):
        """ Returns list of all access times for this user, which means that the search should include any other
        RFID's this LockUser ever had. In other words, the search is by *person*, not by RFID.
        However, multiple RFID's are not implemented yet, so this defaults to using the current RFID only.
        """

        if curr_rfid_only:
            #curr_rfid = self.get_current_rfid()  
            # until fix the only-1-curr-rfid thing, the above actually may refer to multiple instances...  So just for now, for the purposes of getting on with this, just taking the first item if it exists
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
            print "**********************************"
            a = all_access_times_list[0]
            print dir(a)
            print "================================"
            print a.isoformat()
            print a.isocalendar()
            print a.ctime()
            print "***************************************"
        return all_access_times_list
        #return at_query_set

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



#    def get_the_rfid(self):
#        """ for admin.py....
#        'ManyToManyField fields aren't supported, because that would entail executing a separate SQL statement for each row in the table. If you want to do this nonetheless, give your model a custom method, and add that method's name to list_display.'
#        """
#        return self.rfid

    def __unicode__(self):
        """ In the list of AcessTimes, for example, LockUsers will be represented with their first and last names """
        return u'%s %s' % (self.first_name, self.last_name)


"""
class Openership(models.Model):
    lockUser = models.ForeignKey('LockUser')
    rfid     = models.ForeignKey('RFID')
    date_rfid_assigned = models.DateField(null=True) # to this lockUser
    date_rfid_revoked = models.DateField(null=True)  # from this lockUser
"""

