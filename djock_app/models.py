from django.db import models

class AccessTime(models.Model):
    rfid           = models.IntegerField(max_length=30,null=True) # the radio-frequency id, however represented....
    access_time    = models.DateTimeField(null=True)    # the time the rfid was used

    def get_this_user(self):
        """ Return the user's name associated with this RFID """

        # Get QuerySet of all LockUser objects whose RFID matches the RFID associated with this AccessTime
        _at_query_set = LockUser.objects.filter(rfid__exact=self.rfid)

        if _at_query_set:
            return _at_query_set[0]
        else: # nobody found assigned this RFID
            return "No associated user found"

class LockUser(models.Model):
    """
    (Despite the misleading name, LockUsers are not subclassed Users, but subclassed Models.)
    """
    # The radio-frequency id, however it will be represented:
    # The first argument is what the label for this field should read/the verbose name (optional,
    # defaults to same as field's name, with spaces converted to underscores)
    rfid            = models.IntegerField("RF ID",max_length=30,null=True, help_text = "RF ID, however it's represented")

    # previous_rfid   = list of previous rfid's this user had?

    first_name      = models.CharField(max_length=50)
    middle_name     = models.CharField(max_length=50,blank=True)
    last_name       = models.CharField(max_length=50)
    address         = models.CharField(max_length=100,blank=True)
    email           = models.EmailField()
    phone_number    = models.IntegerField(max_length=30,null=True)
    birthdate       = models.DateField(null=True)

    # non-superuser staff should not have the ability to delete models -- but rather to DEACTIVATE.
    is_active       =   models.BooleanField(default=True)

    def get_all_access_times(self, curr_rfid_only=True):
        """ Returns list of all access times for this user, which means that the search should include any other
        RFID's this LockUser ever had. In other words, the search is by *person*, not by RFID.
        However, multiple RFID's are not implemented yet, so this defaults to using the current RFID only.
        """
        if curr_rfid_only:
            # Get QuerySet of all AccessTime objects whose RFID matches this LockUser's current RFID:
            at_query_set = AccessTime.objects.filter(rfid__exact=self.rfid)
            # Now get the access_time field of each AccessTime object
            all_access_times_list = [access_time_object.access_time \
                                    for access_time_object in at_query_set]
        #else:
            # records matching RFIDs in previous_rfid and rfid

        return all_access_times_list

    def get_last_access_time(self, curr_rfid_only=True):
        """ Get the last time this person used the lock. Same story with current RFID vs previous one as in the
        comment for get_all_access_time().
        """
        access_times = self.get_all_access_times(curr_rfid_only=curr_rfid_only)
        if access_times:
            access_times.sort()
            return access_times[-1]
        else:
            return None

    def __unicode__(self):
        """ In the list of AcessTimes, for example, LockUsers will be represented with their first and last names """
        return u'%s %s' % (self.first_name, self.last_name)