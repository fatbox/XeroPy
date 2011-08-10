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
    DATETIME_FIELDS   = (u'UpdatedDateUTC',)
    BOOLEAN_FIELDS    = (u'IsSupplier', u'IsCustomer')
    MULTY_LINES       = (u'LineItem', u'Phone', u'Address')
    PLURAL_EXCEPTIONS = {'Addresse':'Address'}

    def __init__(self, name, client):
        self.client      = client
        self.__name__    = name
        self.__list_word = name[:len(name)-1].title()
        self.__set_decorators()

    def __set_decorators(self):
        for method_name in self.DECORATED_METHODS:
            method = getattr(self, method_name)
            setattr(self, method_name, self.__get_data(method))

    def get_url_postfix(self):
        return self.__name__.title()

    def get_not_plural(self):
        return self.__name__[:len(self.__name__)-1].title()

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
                    out[key] = data[0]
                elif len(data) > 1 and key in self.MULTY_LINES and out:
                    out  += (self.convert_to_dict(data),)
                elif len(data) > 1 and key in self.MULTY_LINES:
                    out   = (self.convert_to_dict(data),)
                elif len(data) > 1 and key == self.__list_word and out:
                    out += (self.convert_to_dict(data),)
                elif len(data) > 1 and key == self.__list_word:
                    out  = (self.convert_to_dict(data),)
                elif len(data) > 1:
                    out[key] = self.convert_to_dict(data)

        elif len(deep_list) == 2:
            key  = deep_list[0]
            data = deep_list[1]
            out[key] = self.convert_to_dict(data)
        else:
            out = deep_list[0]
        return out

    def __convert_data(self, data):
        if isinstance(data, tuple) or isinstance(data, list):
            data = tuple([self.__convert_fields(line) for line in data])
        elif isinstance(data, dict):
            data = self.__convert_fields(data)
        return data

    def __convert_fields(self, data):
        for key in self.BOOLEAN_FIELDS:
            if data.has_key(key):
                val = data[key]
                val = True if val.lower() == 'true' else False
                data[key] = val
        for key in self.DATETIME_FIELDS:
            if data.has_key(key):
                data[key] = parse(data[key])
        return data

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
                    _plural_name  = self.PLURAL_EXCEPTIONS.get(_plural_name, _plural_name)
                    __elm = self.dict_to_xml(SubElement(_elm, _plural_name), _d)

            else:
                _elm.text = str(_data)

        return root_elm

    def __prepare_data__for_save(self, data):
        name = self.get_url_postfix()
        if isinstance(data, list) or isinstance(data, tuple):
            root_elm = Element(name)
            for d in data:
                sub_elm = SubElement(root_elm, self.get_not_plural())
                self.dict_to_xml(sub_elm, d)
        else:
            root_elm = self.dict_to_xml(Element(self.get_not_plural()), data)

        return tostring(root_elm)

    def __get_results(self, data):
        name     = self.get_url_postfix()
        response = data[u'Response']
        result   = response.get(name, {})
        single   = name[:len(name)-1]
        return result if isinstance(result, tuple) else result[single] \
               if result.has_key(single) else None

    def __get_data(self, func):
        def wrapper(*args, **kwargs):
            req_args = func(*args, **kwargs)
            response = self.client.request(*req_args)
            body     = response[1]
            headers  = response[0]
            if headers['status'] == '200':
                if headers['content-type'] == 'application/pdf':
                    return body
                dom  = parseString(body)
                data = self.convert_to_dict(self.walk_dom(dom))
                return self.__convert_data(self.__get_results(data))

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
        name = self.get_url_postfix()
        uri  = '/'.join([XERO_API_URL, name, id])
        return uri, 'GET', None, headers

    def __save_data(self, data, method='PUT'):
        headers = {"Content-Type" :
                   "application/x-www-form-urlencoded; charset=utf-8"}
        name = self.get_url_postfix()
        uri  = '/'.join([XERO_API_URL, name])
        body = 'xml='+urllib.quote(self.__prepare_data__for_save(data))
        return uri, method, body, headers

    def save(self, data):
        return self.__save_data(data, method='post')

    def put(self, data):
        return self.__save_data(data, method='PUT')

    def get_filter_params(self, key, val):
        if key in self.BOOLEAN_FIELDS:
            return 'true' if val else 'false'
        elif key in self.DATETIME_FIELDS:
            return val.isoformat()
        else:
            return '"%s"' % str(val)

    def prepare_filtering_date(self, val):
        isdt = isinstance(val, datetime)
        val  = val.strftime('%a, %d %b %Y %H:%M:%S GMT') if isdt else '"%s"' % val
        return {'If-Modified-Since' : val}

    def filter(self, **kwargs):
        headers = None
        name = self.get_url_postfix()
        uri  = '/'.join([XERO_API_URL, name])
        if kwargs:
            if kwargs.has_key('Since'):
                val     = kwargs['Since']
                headers = self.prepare_filtering_date(val)
                del kwargs['Since']

            params = ['%s==%s' % (key.replace('_','.'),
                       self.get_filter_params(key, kwargs[key])) \
                                       for key in kwargs.keys()]

            if params:
                uri += '?where=' + urllib.quote('&&'.join(params))

        return uri, 'GET', None, headers

    def all(self):
        name = self.get_url_postfix()
        uri  = '/'.join([XERO_API_URL, name])
        return uri, 'GET', None, None

class Xero(object):
    """ Main object for retriving data from XERO """

    INSTANCES__LIST = (u'Contacts', u'Accounts', u'CreditNotes',
                       u'Currencies', u'Invoices', u'Organisation',
                       u'Payments', u'TaxRates', u'TrackingCategories')

    def __init__(self, consumer_key, consumer_secret, privatekey):
        self.consumer_key    = consumer_key
        self.consumer_secret = consumer_secret
        self.privatekey      = privatekey
        self.client = XeroPrivateClient(consumer_key, consumer_secret,
                                        privatekey)
        self.__set_managers(self.client)

    def __set_managers(self, client):
         for name in self.INSTANCES__LIST:
            setattr(self, name.lower(), Manager(name, client))
