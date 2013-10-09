Other
==================

:mod:`ttools`
-----------------------

.. automodule:: app.tests.ttools
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`helpers`
-----------------------
In :mod:`app.forms`, :func:`app.helpers.parse_emails` is used to extract valid emails from a string containing multiple emails and/or separator characters and/or gibberish, using a regular expression. The cleaned string is then stored in the form's `cleaned_data` dictionary.

In :mod:`app.views`, :func:`app.helpers.parse_emails` is used to extract the valid emails from a string containing multiple emails and separator characters. A new CustomerEmail instance is then created for each email address; each CustomerEmail instance is associated with the current Customer instance (submitter of the form) with a ForeignKey relationship.

.. automodule:: app.helpers
    :members:
    :undoc-members:
    :show-inheritance:
