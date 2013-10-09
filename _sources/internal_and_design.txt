Form handling
=================================

Customer contact form handling
--------------------------------------

.. image:: images/end_user_form_screenshot.png
   :width: 300 px

Validation
''''''''''''''
All fields are required.

* **phone number field**: Phone number validation is tricky, as there are so many different ways to write phone numbers --  (123) 456-7890 or 1-123-456-7890 or 456-7890 or 1234567890 or 123-456-BLAH or ..... Perhaps the minimum validation should check that at least seven characters (i.e. a local phone number without any punctuation) have been entered.

* **emails field**: At least one email is required. Since the "Email(s)" field is a single text field, this requirement is handled by using :func:`app.helpers.parse_emails` to verify whether at least one valid email address has been entered; if it has not, the user will see an error stating so (versus the default "This field is required" error, which only appears if the text field is left blank).

.. seealso::
   :func:`app.helpers.parse_emails`


Admin form (for viewing/editing/deleting individual customer records) handling
-------------------------------------------------------------------------------------
.. image:: images/admin_change_form_screenshot.png
   :width: 500 px

Validation
'''''''''''''''''''''
* **emails field**: Unlike the single text field that customers see when filling out the contact form, administrator users see emails as separate fields, and they are able to delete or add extra fields. :func:`app.admin.EmailFormSet.clean` maintains the at-least-one-email requirement (requiring fields in inline forms is a little tricky when extra instances of the form are required).

Multiple emails
=========================

Why create a new model that holds only an `EmailField` and a FK?
-------------------------------------------------------------------------
The contact form allows multiple emails. Since an Customer instance holds all
information associated with one person, it seems natural to create an Customer
attribute for holding emails.  We can handle this by using a TextField to hold
an Customer's email address(es) — or we can create a model to hold a single
email address in an EmailField, and associate the Customer with any number of
these model instances. I went with the latter, for a number of reasons. For
one, this allows an Customer instance to be associated with an unlimited
(barring memory limitations and so forth) number of email addresses without
jumping through a bunch of hoops, and makes changing/deleting/adding emails
easier as well.

For administrative users, it's easier to view, delete, and add email addresses
with multiple fields, or at least it seems so from a user interface perspective.
It also avoids all the headaches with parsing out valid emails and storing them
separately. Additionally, using an `EmailField` lets us use Django's email validation for this type of field.

See the answer to "Why do customers see a single text field for emails, but
administrative users see separate fields?" for additional justification.


.. note::
    .. image:: images/admin_change_list_whole_screenshot_circled_email_col.png
       :width: 500 px


   In the admin change list, the emails column is actually the result of :func:`app.models.Customer.emails` -- this nicely fits into one column and is cleaner than adding additional columns to hold every email associated with a single person.


Why do customers see a single text field for emails, but administrative users see separate fields?
-------------------------------------------------------------------------------------------------------
.. image:: images/admin_change_form_screenshot_circled_inline.png
   :height: 300 px

.. image:: images/end_user_form_screenshot_circled_email.png
   :height: 300 px

From a user interface perspective, it seems cleaner to present email addresses
as separate fields to the administrative user. Viewing, deleting, and creating
email addresses seems more natural as well. But presenting the customer with
separate form fields and an "add more" button seems problematic in a number of
ways, from a user interface perspective:  it's clumsier, adding more stuff on
the screen, and seems sort of confusing and unfamiliar in terms of the
interaction required.

See answer to "Why create a new model that holds only an
`EmailField` and a FK?" above for additional reasoning.

Schema
'''''''''
The decision to use a separate model for emails informs the schema. This is
what Django generates based on the `Customer` and `CustomerEmail` models:

.. code-block:: sql

    CREATE TABLE "app_customer" (
        "id" integer NOT NULL PRIMARY KEY,
        "first_name" varchar(25) NOT NULL,
        "last_name" varchar(25) NOT NULL,
        "street_address" varchar(100) NOT NULL,
        "state" varchar(2) NOT NULL,
        "city" varchar(100) NOT NULL,
        "phone" varchar(20) NOT NULL,
        "all_emails" text NOT NULL
    )

    CREATE TABLE "app_customeremail" (
        "id" integer NOT NULL PRIMARY KEY,
        "customer_id" integer NOT NULL REFERENCES "app_customer" ("id"),
        "email" varchar(100) NOT NULL
    )
