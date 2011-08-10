XeroPy
======

This is a ORM style implementation of the [Xero API](http://developer.xero.com).

Overview
--------

```python
>>> from xero import Xero, XeroException
>>> from datetime import datetime
>>> xero = Xero(XERO_CONSUMER_KEY,
                XERO_CONSUMER_SECRET,
                XERO_PRIVATE_KEY_FILE)
>>> xero.contacts.all()
[{u'Addresses': ({u'AddressType': u'STREET'}, {u'AddressType': u'POBOX'}),
 u'ContactID': u'9568059d-a856-44f4-8961-0060a3dabc8f',
 u'ContactStatus': u'ACTIVE',
 u'EmailAddress': u'130979849416st@corpmail.net',
 u'FirstName': u'first name',
 u'IsCustomer': False,
 u'IsSupplier': False,
 u'LastName': u'last name',
 u'Name': u'[TEST] 130979849416st',
 u'Phones': ({u'PhoneType': u'DEFAULT'},
             {u'PhoneType': u'FAX'},
             {u'PhoneType': u'DDI'},
             {u'PhoneType': u'MOBILE'}),
 u'UpdatedDateUTC': datetime.datetime(2011, 7, 4, 16, 54, 57, 653000)},
 ...]

>>> xero.contacts.get("9568059d-a856-44f4-8961-0060a3dabc8f")
{u'Addresses': ({u'AddressType': u'STREET'}, {u'AddressType': u'POBOX'}),
 u'ContactID': u'9568059d-a856-44f4-8961-0060a3dabc8f',
 u'ContactStatus': u'ACTIVE',
 u'EmailAddress': u'130979849416st@corpmail.net',
 u'FirstName': u'first name',
 u'IsCustomer': False,
 u'IsSupplier': False,
 u'LastName': u'last name',
 u'Name': u'[TEST] 130979849416st',
 u'Phones': ({u'PhoneType': u'DEFAULT'},
             {u'PhoneType': u'FAX'},
             {u'PhoneType': u'DDI'},
             {u'PhoneType': u'MOBILE'}),
 u'UpdatedDateUTC': datetime.datetime(2011, 7, 4, 16, 54, 57, 653000)}

>>> xero.contacts.filter(Since=datetime(2011,7,1))
[{u'Addresses': ({u'AddressType': u'STREET'}, {u'AddressType': u'POBOX'}),
 u'ContactID': u'9568059d-a856-44f4-8961-0060a3dabc8f',
 u'ContactStatus': u'ACTIVE',
 u'EmailAddress': u'130979849416st@corpmail.net',
 u'FirstName': u'first name',
 u'IsCustomer': False,
 u'IsSupplier': False,
 u'LastName': u'last name',
 u'Name': u'[TEST] 130979849416st',
 u'Phones': ({u'PhoneType': u'DEFAULT'},
             {u'PhoneType': u'FAX'},
             {u'PhoneType': u'DDI'},
             {u'PhoneType': u'MOBILE'}),
 u'UpdatedDateUTC': datetime.datetime(2011, 7, 4, 16, 54, 57, 653000)},
 ...]
```

TODO
----
More docs & tests


Copyright (c) 2011 FatBox Inc.
