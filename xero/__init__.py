from xml.dom.minidom import parseString
from xml.etree.ElementTree import tostring, SubElement, Element
from datetime import datetime
from dateutil.parser import parse
from api import XeroPrivateClient, XeroException
from api import XERO_BASE_URL, XERO_API_URL
import urllib

class XeroException404(XeroException):
    pass

class XeroException500(XeroException):
    pass

class XeroBadRequest(XeroException):
    pass

class XeroNotImplemented(XeroException):
    pass

class XeroExceptionUnknown(XeroException):
    pass

class Manager(object):
    DECORATED_METHODS = ('get', 'save', 'filter', 'all', 'put')

    DATETIME_FIELDS = (u'UpdatedDateUTC', u'Updated', u'FullyPaidOnDate')
    DATE_FIELDS = (u'DueDate', u'Date')
    BOOLEAN_FIELDS = (u'IsSupplier', u'IsCustomer')

    MULTI_LINES = (u'LineItem', u'Phone', u'Address', 'TaxRate')
    PLURAL_EXCEPTIONS = {'Addresse':'Address'}

    def __init__(self, name, client):
        self.client = client
        self.name = name

        # setup our singular variants of the name
        # only if the name ends in 0
        if name[-1] == "s":
            self.singular = name[:len(name)-1]
        else:
            self.singular = name

        for method_name in self.DECORATED_METHODS:
            method = getattr(self, method_name)
            setattr(self, method_name, self.__get_data(method))

    def walk_dom(self, dom):
        tree_list = tuple()
        for node in dom.childNodes:
            tagName = getattr(node, 'tagName', None)
            if tagName:
                tree_list += (tagName , self.walk_dom(node),)
            else:
                data = node.data.strip()
                if data:
                    tree_list += (node.data.strip(),)
        return tree_list

    def convert_to_dict(self, deep_list):
        out = {}
        if len(deep_list) > 2:
            lists = [l for l in deep_list if isinstance(l, tuple)]
            keys  = [l for l in deep_list if isinstance(l, unicode)]
            for key, data in zip(keys, lists):

                if len(data) == 1:
                    # we're setting a value
                    # check to see if we need to apply any special
                    # formatting to the value
                    val = data[0]
                    if key in self.BOOLEAN_FIELDS:
                        val = True if val.lower() == 'true' else False
                    if key in self.DATETIME_FIELDS:
                        val = parse(val)
                    if key in self.DATE_FIELDS:
                        val = parse(val).date()

                    out[key] = val

                elif len(data) > 1 and ((key in self.MULTI_LINES) or (key == self.singular)):
                    # our data is a collection and needs to be handled as such
                    if out:
                        out += (self.convert_to_dict(data),)
                    else:
                        out = (self.convert_to_dict(data),)

                elif len(data) > 1:
                    out[key] = self.convert_to_dict(data)

        elif len(deep_list) == 2:
            key = deep_list[0]
            data = deep_list[1]
            out[key] = self.convert_to_dict(data)
        else:
            out = deep_list[0]
        return out

    def dict_to_xml( self, root_elm, dict_data ):
        for key in dict_data.keys():
            _data = dict_data[key]
            _elm  = SubElement(root_elm, key)

            _list_data = (isinstance(_data, list) or isinstance(_data, tuple))
            _is_plural = (key[len(key)-1] == "s")
            _plural_name = key[:len(key)-1]

            if isinstance(_data, dict):
                _elm = self.dict_to_xml(_elm, _data)

            elif _list_data and not _is_plural:
                for _d in _data:
                  __elm = self.dict_to_xml(_elm, _d)

            elif _list_data:
                for _d in _data:
                    _plural_name = self.PLURAL_EXCEPTIONS.get(_plural_name, _plural_name)
                    __elm = self.dict_to_xml(SubElement(_elm, _plural_name), _d)

            else:
                _elm.text = str(_data)

        return root_elm

    def __prepare_data__for_save(self, data):
        if isinstance(data, list) or isinstance(data, tuple):
            root_elm = Element(self.name)
            for d in data:
                sub_elm = SubElement(root_elm, self.singular)
                self.dict_to_xml(sub_elm, d)
        else:
            root_elm = self.dict_to_xml(Element(self.singular), data)

        return tostring(root_elm)

    def __get_results(self, data):
        response = data[u'Response']
        result = response.get(self.name, {})

        if isinstance(result, tuple):
            return result

        if isinstance(result, dict) and result.has_key(self.singular):
            return result[self.singular]

    def __get_data(self, func):
        def wrapper(*args, **kwargs):
            req_args = func(*args, **kwargs)
            response = self.client.request(*req_args)
            body = response[1]
            headers = response[0]
            if headers['status'] == '200':
                if headers['content-type'] == 'application/pdf':
                    return body
                dom  = parseString(body)
                data = self.convert_to_dict(self.walk_dom(dom))
                return self.__get_results(data)

            elif headers['status'] == '404':
                msg = ' : '.join([str(headers['status']), body])
                raise XeroException404(msg)

            elif headers['status'] == '500':
                msg = ' : '.join([str(headers['status']), body])
                raise XeroException500(msg)

            elif headers['status'] == '400' or headers['status'] == '401':
                msg = ' : '.join([str(headers['status']), body])
                raise XeroBadRequest(msg)

            elif headers['status'] == '501':
                msg = ' : '.join([str(headers['status']), body])
                raise XeroNotImplemented(msg)

            else:
                msg = ' : '.join([str(headers['status']), body])
                raise XeroExceptionUnknown(msg)

        return wrapper

    def get(self, id, headers=None):
        uri  = '/'.join([XERO_API_URL, self.name, id])
        return uri, 'GET', None, headers

    def save_or_put(self, data, method='post'):
        headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
                }
        uri = '/'.join([XERO_API_URL, self.name])
        body = 'xml='+urllib.quote(self.__prepare_data__for_save(data))
        return uri, method, body, headers

    def save(self, data):
        return self.save_or_put(data, method='post')

    def put(self, data):
        return self.save_or_put(data, method='PUT')

    def prepare_filtering_date(self, val):
        if isinstance(val, datetime):
            val = val.strftime('%a, %d %b %Y %H:%M:%S GMT')
        else:
            val = '"%s"' % val
        return {'If-Modified-Since': val}

    def filter(self, **kwargs):
        headers = None
        uri  = '/'.join([XERO_API_URL, self.name])
        if kwargs:
            if kwargs.has_key('Since'):
                val     = kwargs['Since']
                headers = self.prepare_filtering_date(val)
                del kwargs['Since']

            def get_filter_params():
                if key in self.BOOLEAN_FIELDS:
                    return 'true' if kwargs[key] else 'false'
                elif key in self.DATETIME_FIELDS:
                    return kwargs[key].isoformat()
                else:
                    return '"%s"' % str(kwargs[key])

            def generate_param(key):
                return '%s==%s' % (
                        key.replace('_','.'),
                        get_filter_params()
                        )

            params = [generate_param(key) for key in kwargs.keys()]

            if params:
                uri += '?where=' + urllib.quote('&&'.join(params))

        return uri, 'GET', None, headers

    def all(self):
        uri = '/'.join([XERO_API_URL, self.name])
        return uri, 'GET', None, None

class Xero(object):
    """
    An ORM interface to the Xero API

    This has only been tested with the Private API
    """

    OBJECT_LIST = (u'Contacts', u'Accounts', u'CreditNotes',
                   u'Currencies', u'Invoices', u'Organisation',
                   u'Payments', u'TaxRates', u'TrackingCategories')

    def __init__(self, consumer_key, consumer_secret, privatekey):
        # instantiate our private api client
        client = XeroPrivateClient(consumer_key,
                                   consumer_secret,
                                   privatekey)

        # iterate through the list of objects we support, for
        # each of them create an attribute on our self that is
        # the lowercase name of the object and attach it to an
        # instance of a Manager object to operate on it
        for name in self.OBJECT_LIST:
            setattr(self, name.lower(), Manager(name, client))
