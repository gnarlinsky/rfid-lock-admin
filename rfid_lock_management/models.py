from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.auth.management import create_superuser
from django.db.models import signals
from django.utils.timezone import utc
import datetime
from termcolor import colored   # temp
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission


class Door(models.Model):
    """ 
    Doors with RFID locks installed. 
    """
    name        = models.CharField(max_length=50, unique=True,null=False)  # e.g. "Makerspace," "Bike Project," etc.
    description = models.TextField(null=True, blank=True)

    def __unicode__(self):
        """ 
        Represent Door objects with their name fields 
        """
        return u'%s' % (self.name)


    def save(self,*args,**kwargs):
        """ 
        When a new Door is added, create a corresponding Permission, if it does not exist already 
        """

        super(Door,self).save(*args,**kwargs)

        if not Permission.objects.filter(codename='can_manage_door_%d' % self.pk): 
            content_type = ContentType.objects.get(app_label='rfid_lock_management',model='door')

            Permission.objects.create( \
                    codename='can_manage_door_%d' % self.pk, \
                    name = 'Can manage door to %s' % self.name,\
                    content_type = content_type)   
        
    def get_allowed_rfids(self):
        """ 
        Return the RFIDs allowed to access this Door 
        """
        return_list = []
        for lu in self.lockuser_set.all():
            if lu.get_current_rfid():
                return_list.append(lu.get_current_rfid())
        return return_list 


class NewKeycardScan(models.Model):
    """ 
    For checking whether the current request is for authenticating a keycard or assigning new keycard. 
    """
    #time_initiated = models.DateTimeField(auto_now_add=True)
    # auto_now_add and time zones do not play well together sometimes...
    time_initiated = models.DateTimeField(default=datetime.datetime.now().replace(tzinfo=utc))
    waiting_for_scan = models.BooleanField(default=True) 
    doorid = models.CharField(max_length=50)   # doorid as in the request url
    rfid = models.CharField(max_length=10)   # rfid as in the request url
    ready_to_assign = models.BooleanField(default=False)
    assigner_user = models.ForeignKey(User)

    def timed_out(self,minutes=2):
        """ 
        Check whether specified number of minutes have passed since staff user 
        indicated they were going to go scan in a card in order to assign it.
        Returns tuples with T/F as first item; second item is the time
        differences in minutes, which is useful for including  on LockUser 
        change form to let the staff user know how many minutes before time
        out. 
        """
        now = datetime.datetime.now().replace(tzinfo=utc)
        max_time = datetime.timedelta(minutes=minutes)
        delta = now - self.time_initiated
        time_diff_minutes = round( delta.total_seconds() / 60, 2)
        """
        print colored("*****************************************************************", "blue", "on_white")
        print 'now', now
        print 'maxtime', max_time
        print 'd', delta
        print 'timediffmin ', time_diff_minutes
        print ' is it > ', delta>max_time
        print colored("<<<<<<<<<<<<<*****************************************************************", "blue", "on_white")
        """
        return (delta>max_time, time_diff_minutes)


class RFIDkeycard(models.Model):
    """ 
    Door access represented by a (potentially reusable) RFID keycard
    (or keyfob or whatever) assigned to a LockUser. 
    """
    the_rfid    = models.CharField(max_length=10,null=False,blank=False, editable=False) # the radio-frequency id
    date_revoked = models.DateTimeField(null=True, blank=True) 
    date_created = models.DateTimeField(default=datetime.datetime.now().replace(tzinfo=utc))
    lockuser = models.ForeignKey("LockUser",null=False)
    # If we don't specify a related_name, User would have two reverse relations
    # to rfidkeycard_set, which is impossible. 
    assigner =  models.ForeignKey(User, related_name='RFIDkeycard_assigned')
    revoker =   models.ForeignKey(User, related_name='RFIDkeycard_revoked',null=True)

    def __unicode__(self):
        """
        Represent keycard object with the rfid number 
        """
        return u'%s' % (self.the_rfid)

    def get_allowed_doors(self):
        """ 
        Get the Doors this user is allowed access to. 
        """
        return self.lockuser.get_allowed_doors()

    def is_active(self):
        if self.date_revoked: 
            return False
        else:
            return True

    def deactivate(self,user):
        now = datetime.datetime.now().replace(tzinfo=utc)
        self.date_revoked = now
        self.revoker = user


class AccessTime(models.Model):
    the_rfid    = models.CharField(max_length=10,null=True) 
    access_time = models.DateTimeField(null=True)    # the time the rfid was used
    lockuser    = models.ForeignKey("LockUser",null=True)
    door        = models.ForeignKey("Door",null=True)
    data_point  = models.TextField()  # todo

    def __unicode__(self):
        #return u'%s' % self.access_time
        return self.access_time.strftime("%B %d, %Y, %I:%M %p")  # e.g. 'April 09, 2013, 12:25 PM'

    def get_this_lockuser_html(self):
        """ 
        Returns the HTML with link to /lockuser/the_id/ to display on the 
        AccessTime change list page 
        """
        lockuser_link_html =  "<a href='../lockuser/%d/'>%s</a>" %  (self.lockuser.id, self.lockuser)
        return lockuser_link_html
    get_this_lockuser_html.allow_tags = True

class LockUser(models.Model):
    """
    (Despite the misleading name, LockUsers are not subclassed Users, but subclassed Models.) 
    """
    first_name = models.CharField(max_length=50,null=False)
    last_name = models.CharField(max_length=50, null=False)
    email = models.EmailField(null=False,unique=True) 
    address = models.CharField(max_length=100,blank=True)
    phone_number = models.CharField(max_length=20,null=True,blank=True) 
    birthdate = models.DateField(null=True)
    doors = models.ManyToManyField(Door,blank=True, help_text = "Select at least one space to activate keycard." )
    deactivate_current_keycard = models.BooleanField(default=False, help_text="Revoke keycard access and deactivate user.")    
    current_keycard_revoker = models.ForeignKey(User,null=True)

    def save(self, *args, **kwargs):
        """ 
        Overriding save(): 
            - We'll deactivate a LockUser's current keycard here, if deactivate_current_keycard is checked
              on the LockUser's change_form. 
            - If we're assigning a new keycard, the keycard is created and saved here. 
        """
        # Since rfid_lock_management_rfidkeycard.lockuser_id may not be NULL when saving RFIDkeycard object, we need
        # to save the LockUser object first, so we can get self.id (which is also necessary before any work
        # with FK's and M2M). 
        super(LockUser, self).save(*args, **kwargs)

        # Not doing a check for door existence here. At this point, deactivate_current_keycard is set to true if 
        # there were no doors (see admin.py), but doors may not have been saved yet, 
        # so checking self.doors.exists() would be misleading. 
        #if self.doors.exists(): 
        new_scan_queryset = NewKeycardScan.objects.all()
        if new_scan_queryset:
            new_scan = new_scan_queryset.latest("pk") # get last created NewKeycardScan object
            # Note:  this -- 
            #   new_scan = new_scan_queryset.latest("time_initiated")  
            # -- may not actually return the latest created object if 'start
            # scan' was hit a bunch of times in a row -- microseconds don't seem
            # to be at sufficient resolution to actually get the latest object.
            if new_scan.ready_to_assign:
                new_scan.ready_to_assign = False   
                new_scan.save() # save new_scan before saving new_keycard
                # assign the rfid from the keycard that was just scanned
                new_keycard = RFIDkeycard(lockuser=self, the_rfid=new_scan.rfid, assigner=new_scan.assigner_user)
                new_keycard.save()
        current_keycard = self.get_current_rfid() 
        
        # Deactivate a LockUser's current keycard here, if deactivate_current_keycard 
        # is checked on the LockUser's change_form, or if no doors were selected. 
        # not doing a check for door existence here. At this point,
        # deactivate_current_keycard is set to true if there were no doors (see
        # admin.py), but doors may not have been saved yet, so checking
        # self.doors.exists() would be misleading. 
        if current_keycard and self.deactivate_current_keycard: 
            current_keycard.deactivate(self.current_keycard_revoker)
            current_keycard.save()# save keycard since have changed it
            # todo: consider putting the  following two statements actually into deactivate() 
            self.deactivate_current_keycard = False   # no current keycard to deactivate anymore
            self.current_keycard_revoker = None
            self.save()


    # todo:  rethink all these
    def get_all_rfids(self):
        """ 
        Get all RFID's associated with this LockUser 
        """
        return self.rfidkeycard_set.all()

    # todo:  get_all_rfids_html not parallel to other prettify methods....actually returns all but
    # current, includes HTML.
    ##  Actually this should be all rfid's but the current one???
    # todo: rename  to indicate that getting all but CURRENT
    def get_all_rfids_html(self):
        """
        Returns HTML for displaying list of all keycards (excluding curent, if any). 
        Includes date assigned and date revoked, as well as rfid number. 
        """
        all_rfid_keycards = self.get_all_rfids()
        all_keycards_except_current = all_rfid_keycards.exclude(date_revoked=None)
        rfid_keycards_info_list = []
        for keycard in all_keycards_except_current:
            rf = keycard.the_rfid
            date_assigned = keycard.date_created.strftime("%B %d, %Y, %I:%M %p")
            assigner = keycard.assigner
            try:
                #date_revoked = keycard.date_revoked.ctime()   
                date_revoked = keycard.date_revoked.strftime("%B %d, %Y, %I:%M %p")
                revoker = keycard.revoker
                info_str = "RFID: %s (activated on %s by %s; revoked on %s by %s)" % (rf,date_assigned, assigner,date_revoked, revoker)
            # Catching exceptions here was really only useful in development, so excluding it from coverage
            except:  # pragma: no cover
                info_str = "RFID: %s (activated on %s by %s [couldn't get revoker] )" % (rf,date_assigned,assigner)
            rfid_keycards_info_list.append(info_str)
        return ",<br>".join(rfid_keycards_info_list)
    get_all_rfids_html.allow_tags = True

    def get_current_rfid(self):
        """ 
        Of all RFID's associated with this LockUser, get the one that's active, i.e. has not been revoked.  
        """
        all_rfid_keycards = self.get_all_rfids()
        curr_rfid = all_rfid_keycards.filter(date_revoked=None)  
        # There should only be one
        try:
            return curr_rfid[0]  
        except:
            return None

    def is_active(self):
        """ 
        Useful in LockUser's list display 
        """
        if self.get_current_rfid(): 
            return True
        else:
            return False
       
    def prettify_get_current_rfid(self):
        """ Returns results of get_current_rfid(), but as a nice pretty string.
        Also display date assigned as well as rfid number on LockUser change form and list display
        """
        curr_rfid = self.get_current_rfid()
        #curr = [str(c.the_rfid) for c in curr_rfid]  # todo - again! haven't coded anythign yet 
            #to account for there only being one current per person!/my fake data forces me to do this...  
        try:
            #curr_keycard_info = "RFID: %s (activated on %s by %s)" % (curr_rfid.the_rfid, curr_rfid.date_created.ctime(), curr_rfid.assigner)
            curr_keycard_info = "RFID: %s (activated on %s by %s)" % (curr_rfid.the_rfid, curr_rfid.date_created.strftime("%B %d, %Y, %I:%M %p"), curr_rfid.assigner)
            return curr_keycard_info
        except:
            return None
    prettify_get_current_rfid.short_description = "Current RFID"

    def get_allowed_doors(self):
        """ Get the Doors this user is allowed access to. """
        return self.doors.all()            

    def prettify_get_allowed_doors(self):
        allowed_doors = self.get_allowed_doors()
        door_names_list = [door.name for door in allowed_doors] 
        return ", ".join(door_names_list)

    def get_allowed_doors_html_links(self):
        """ Returns the HTML (which will have to escape) with links to /door/the_id/ to display on the LockUser change list page """
        allowed_doors = self.get_allowed_doors()
        doors_links_list = []
        for door in allowed_doors:
            door_link_html =  "<a href='../door/%d/'>%s</a>" %  (door.pk, door.name) 
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
    #def get_all_access_times(self, curr_rfid_only=True):
    def get_all_access_times(self):
        """ Returns list of all access times (the actual access_time field, not the objects) for this user, which means that the search should include any other
        RFID's this LockUser ever had. In other words, the search is by *person*, not by RFID.
        Although we're in the process of deciding whether there should only be one keycard/RFID per person. see the comment for RFIDkeycard.get_allowed_doors().
        (TODO) 
        """
        # Get QuerySet of all AccessTime objects for this lockuser
        at_query_set = AccessTime.objects.all().filter(lockuser=self).order_by('access_time')
        # Now get the access_time field of each AccessTime object
        all_access_times_list = [access_time_object.access_time for access_time_object in at_query_set]
        return all_access_times_list

    #def prettify_get_all_access_times(self,curr_rfid_only=True):
    def all_access_times_link(self): 
        """ prettify and sort """
        return "<a href='../../accesstime/?lockuser__id__exact=%d'>View all access times</a>" %  self.id
    all_access_times_link.allow_tags = True
        
    # todo: 
    #def get_last_access_time(self, curr_rfid_only=True):
    def get_last_access_time(self):
        """ Get the last time this person used the lock. 
        Same story with current RFID vs previous one as in the
        comment for get_all_access_time().

        """
        access_times = self.get_all_access_times()
        
        # grab the last one
        if access_times:
            #access_times.sort()
            #return access_times[-1]  
            #access_times.latest('access_time')
            # as get_all_access_times() returns a list of the access_time *fields*, not the objects, already ordered by time, we can just grab the last one in the list
            #access_times.sort()
            return access_times[-1]  
        else:
            return None

    def prettify_get_last_access_time(self):  
        last = self.get_last_access_time()
        if last:
            #return last.ctime()
            return last.strftime("%B %d, %Y, %I:%M %p") 
        else:
            return None

    def prettify_get_last_access_time_and_door(self):  
        """ Includes the door this access time is associated with (for change list) """
        at_query_set = AccessTime.objects.filter(lockuser=self)  # todo: note - a different appraoch than similar methods
        last = at_query_set.latest('access_time')
        
        #if last:
        #    #return last.ctime()
        #    return last.access_time.strftime("%B %d, %Y, %I:%M %p") + " (" + last.door.name + ")"
        #else:
        #    return None
        return last.access_time.strftime("%B %d, %Y, %I:%M %p") + " (" + last.door.name + ")"

    def last_access_time_and_link_to_more(self):  
        """ including link to all access times (for change form) """
        last_time = self.get_last_access_time()
        link = self.all_access_times_link()
        if last_time:
            return "%s (%s)" % (last_time.strftime("%B %d, %Y, %I:%M %p") , link)
        else:
            return None
    last_access_time_and_link_to_more.allow_tags = True

    def last_access_time_and_door_and_link_to_more(self):  
        """ including link to all access times (for change form) """
        at_query_set = AccessTime.objects.filter(lockuser=self)  # todo: note - a different appraoch than similar methods
        last = at_query_set.latest('access_time')
        link = self.all_access_times_link()
        """
        if last:
            return "%s (%s) (%s)" % (last.access_time.strftime("%B %d, %Y, %I:%M %p"), last.door.name, link)
        else:
            return None
        """
        # todo (see __B__)
        return_val = None
        if last:
            return_val =  "%s (%s) (%s)" % (last.access_time.strftime("%B %d, %Y, %I:%M %p"), last.door.name, link)
        return return_val
    last_access_time_and_door_and_link_to_more.allow_tags = True
    last_access_time_and_door_and_link_to_more.short_description = "Last access"
    
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
signals.post_syncdb.disconnect(    create_superuser, sender=auth_models, dispatch_uid='django.contrib.auth.management.create_superuser') # pragma: no cover  (exclude this code from coverage)

# Create our own test user automatically.
def create_testuser(app, created_models, verbosity, **kwargs):  # pragma: no cover
  if not settings.DEBUG:
    return
  try:
    auth_models.User.objects.get(username='superuser')
  except auth_models.User.DoesNotExist:
    print '*' * 80
    print 'Creating test user -- login: superuser, password: superuser'
    print '*' * 80
    assert auth_models.User.objects.create_superuser('superuser', 'x@x.com', 'superuser')
  else:
    print 'Test user already exists.'

signals.post_syncdb.connect(create_testuser,
    sender=auth_models, dispatch_uid='common.models.create_testuser')
