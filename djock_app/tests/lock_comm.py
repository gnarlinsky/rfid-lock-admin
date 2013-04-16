from django.test import TestCase
from termcolor import colored
from django.test.client import Client

"""
# to run only some tests: 
#   $ ./manage.py test djock_app.LockUserModelTest
"""

###################
# TO DO: 
###################
#  - additional_tests.py 


class LockCommunicationTests(TestCase):  
    #fixtures = ['rename_back_to_initial_data.json']  # to save the test user so can succeed on login tests
    # TO DO: copy and rename the above to something that makes sense for here


    fixtures = ['lockuser_keycard_perm_user_accesstime_door_user.json']

    def setUp(self):
        print colored("\nSETTING UP / TestCase LockCommunicationTests", "white","on_green")

        c = Client()

        # So would set up the Model objects I need here?  #   Rather than reference my test data.
        #   NOPE: Model creation and manipulation are tests in and of themselves.  Tests for other stuff
        #   should assume that we already have the objects we need.
        #self.test_lockuser = LockUser(phone_number = "2175555555", first_name = "Michael", last_name = "Jackson", middle_name = "", birthdate = None, address = "", email = "michael@thejackson5.com")


    # Should take arguments? So that other tests can call it... For example, when door perms
    # for door x are changed, want to test that URL with door x's id return
    # the appropriate response.
    def check_response_and_status(self,client,url,correct_status_code,correct_response_content):
        resp = client.get(url)
        # self.assert(give it url, check if response=1 or 0)
        print colored("\tChecking response status code (%s) for %s" % (correct_status_code,url),"cyan")
        self.assertEqual(resp.status_code,correct_status_code)
        print colored("\tChecking response content (%s) for %s \n" % (correct_response_content, url) ,"cyan")
        self.assertEqual(resp.content,correct_response_content)

    def test_checking_url_response_and_status(self):
        """
        the cases:  door not good; rfid not good; not active
            (although in some cases Django already does the is_active check,
                doublecheck that)
            (Not setting anything up in here, but just using test db,
            just to see if I can do this...

            Testing urls like /checkdoor/doorid/checkrfid/rfid/

            Return 0 if at least one of these is true:
            - No RFIDkeycard with the rfid number;
            - doorid is not in the list of doors this keycard can access
            - keycard not currently active
            - .....  user currently active...
              although some of these imply other ones....
              A lock user being inactive: they wouldn't even have a current rfid

            - Also, the rfid must be exactly 10 digits long (and the only
                characters allowed: alphanumeric, _ [ doublecheck that though ] );
                the door id has to be an int right now, no length limit.
            The urlconf should take care of this.  If either of those
                don't match,  the debug page is displayed (DEBUG is set to
                True in settings.py), but in real life a standard 404
                will be returned -- the status code
        """

        c = Client()   # todo: not saving from SetUp??
        print colored("\nTEST: checking correct response/status for a particular URL - Given URL with door and rfid id's, is the response/status (whether the rfid is good for that door) correct?","blue")
        print colored("\t(In fixture: \n\t- door with doorid 2 does exist; but no doors with id's aaaaa\
                        \n\t- rfid 0123456789 (pk 1) does exist; but not abc123, not 9123456789\
                        \n\t- door 2 is associated with 0123456789 and 1123456789 (pk 2) but not with 2123456789\
                        \n\t- 0123456789 is active (i.e. no date_revoked)\
                        \n\t- 1123456789 is NOT active (i.e. date_revoked is not None)\
                        \n\t- 2123456789 is active  (pk 3) (i.e. no date_revoked)\n\t)", "green")







        print colored("\t(In fixture: \n\t- door with doorid 2 does exist; but no doors with id's aaaaa or 10 \
                        \n\t- rfid 1122135122  does exist; but not abc123, not 9123456789\
                        \n\t- door 2 is associated with 9999999992  and 1122135199  (pk 2) but not with 1122135122 (which does exist, but is associated with a different door) \
                        \n\t- 9999999992  is active (i.e. no date_revoked)\
                        \n\t- 9999999991 is associated with door 2 but is NOT active (i.e. date_revoked is not null)", \
                    "green") 

        # TO DO: the tests below... don't call an additional method, put everything in here?
        # Yes, it modularizes like this, but not in a really comprehensible way, plus have to remember
        #  what the arguments are there............

        # this is not comprehensive....

        self.check_response_and_status(c,"/checkdoor/10/checkrfid/1123456789/", 200,"0")  # door does not exist 
        self.check_response_and_status(c,"/checkdoor/2/checkrfid/9123456789/", 200,"0")   # rfid does not exist 
        self.check_response_and_status(c,"/checkdoor/2/checkrfid/1122135122/", 200,"0")  # rfid not associated with door 2, is active
        self.check_response_and_status(c,"/checkdoor/2/checkrfid/9999999992/", 200,"0")  # rfid associated with door, is active
        self.check_response_and_status(c,"/checkdoor/2/checkrfid/9999999991/", 200,"0")  # rfid was associated with door, but now inactive

        # incorrect checking urls, so should return nothing and a not found error
        self.check_response_and_status(c,"/checkdoor/aaaaa/checkrfid/1123456789/", 404,"")  # door id in wrong format 
        self.check_response_and_status(c,"/checkdoor/2/checkrfid/abc123/",404, "")  # rfid num in wrong format 

       #    The fixture is changed actually, so for (4) above: 

        #(notice the new thing - no door 10.
        #plus, it's not NONE for no date_revoked, but "not null"
        



        # TO DO: tests for get_all_allowed (across doors); e.g. get_allowed_all_doors/
        #       tests for URLS with door id's as well, e.g. get_allowed_one_door/doorid/
        """
        self.check_response_and_status(c,"/get_allowed_all_doors", "200," "<correct json list>")
        self.check_response_and_status(c,"/get_allowed_one_door/<insert door that does not exist>", "xxx", "<correct json list>")
        self.check_response_and_status(c,"/get_allowed_one_door/<insert door with no one allowed>", "xxx", "<correct json list>")
        self.check_response_and_status(c,"/get_allowed_one_door/<insert door with one allowed rfid>", "xxx", "<correct json list>")
        self.check_response_and_status(c,"/get_allowed_one_door/<insert door with many allowed rfids>", "xxx", "<correct json list>")
        """

    def test_get_allowed_rfids_for_door(self):
        """ Using a different fixture for this... current fixtures are defunct,
        so just want to test getting the allowed rfid's for a door quickly:
            Door id = 1, name = 'Makerspace 2':
                allowed rfids:
                        Michael Jackson - 1123456789
                not allowed:
                        Tito Jackson - 3123456789  (this door *is* in Tito's allowed doors, but Tito is INACTIVE)
                        Janet - 2123456789 (this door *is* in the allowed list of doors for a PAST, INACTIVE keycard, which is 4123456789)    (TO DO - pending code for inactive RFIDkeycards)
                        Latoya - 5123456789 (TO DO -- see Janet above)



            Door id = 2, name = 'Door x':
                allowed rfids:
                        Michael
                        Tito
                not allowed:
                        Michael
                        Janet (TO DO -- pending code for inactive RFIDkeycards)

                        Latoya (TO DO -- pending code for inactive RFIDkeycards)

            Door id=3, name='Narnia':
                allowed rfids:  none
                                (though Latoya has perms for Narnia, she is deactivated (TO DO - pending code for inactive RFIDkeycards))
                not allowed:
                        Janet,
                        Michael,
                        Tito,
                        Latoya

            And Latoya Jackson is not allowed anywhere, because inactive, but has door perms for Narnia  (TO DO - pending code for inactive RFIDkeycards)
        """
        c = Client()
        fixtures = ['checks.json']  # early version of fixture, pending (at least) code for inactive RFIDkeycards

        # url: door/(?P<doorid>\d+)/getallowed/$
        # view: get_allowed_rfids(request, doorid=None)
        pass
