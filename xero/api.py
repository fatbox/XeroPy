"""Xero XPI Wrapper.
Implemented using Xero API documentation on:

http://blog.xero.com/developer/api/

"""
__version__ = '$Revision: 116350 $'

import urlparse
import sys
# Third party
import httplib2
import oauth2
import socks
from signature import SignatureMethod_RSA

XERO_BASE_URL = "https://api.xero.com"
REQUEST_TOKEN_URL = "%s/oauth/RequestToken" % XERO_BASE_URL
AUTHORIZE_URL = "%s/oauth/Authorize"  % XERO_BASE_URL
ACCESS_TOKEN_URL = "%s/oauth/AccessToken" % XERO_BASE_URL
XERO_API_URL = "%s/api.xro/2.0" % XERO_BASE_URL

class XeroException(Exception):
    pass

class XeroPrivateClient(oauth2.Client):
    """
    Xero client for Private Application integration

    @param consumer_key  Consumer key as shown on appliction screen

https://api.xero.com

    @param consumer_secret Consumer secret as shown on application screen at

https://api.xero.com

    @param rsa_key_path Path to the  the rsa key.
    @param proxy_host   Proxy host name
    @param proxy_port   Proxy port number

    Usage:
    client = XeroPrivateClient(consumer_key, consumer_secret,
                rsa_key_path, proxy_host, proxy_port)
    client.request(...)
    """
    def __init__(self, consumer_key, consumer_secret,
                rsa_key_path, proxy_host=None, proxy_port=None):
        if proxy_host and proxy_port:
            proxy_info = httplib2.ProxyInfo(socks.PROXY_TYPE_HTTP, proxy_host,
                     proxy_port)
        else:
            proxy_info = None
        consumer = oauth2.Consumer(consumer_key, consumer_secret)
        # For private applications, the consumer key and secret are used as the
        # access token and access secret.
        token = oauth2.Token(consumer_key, consumer_secret)
        oauth2.Client.__init__(self, consumer, token, proxy_info=proxy_info)
        self.set_signature_method(SignatureMethod_RSA(rsa_key_path))

class XeroPublicClient:
    """
    Xero client for Public Application integration. Requires user interaction
    to manually login to Xero and type the verification code in command line.

    @param consumer_key  Consumer key as shown on appliction screen

https://api.xero.com

    @param consumer_secret Consumer secret as shown on application screen at

https://api.xero.com

    @param proxy_host   Proxy host name
    @param proxy_port   Proxy port number

    Usage:
    client = XeroPublicClient(consumer_key, consumer_secret, proxy_host,
                                proxy_port)
    client.authorise()
    client.request(...)
    """
    def __init__(self, consumer_key, consumer_secret,
                    proxy_host=None, proxy_port=None):
        self.consumer = oauth2.Consumer(consumer_key, consumer_secret)
        if proxy_host and proxy_port:
            self.proxy_info = httplib2.ProxyInfo(socks.PROXY_TYPE_HTTP,
                    proxy_host, proxy_port)
        else:
            self.proxy_info = None

    def _get_request_token(self):
        oauth_client = oauth2.Client(self.consumer, proxy_info=self.proxy_info)
        response, content = oauth_client.request(REQUEST_TOKEN_URL, "GET")
        if response["status"] != '200':
            raise XeroException("Invalid response from requesting token: %s" %
                                response["status"])
        # Set this token for the auth request.
        return oauth2.Token.from_string(content)

    def _authorise_token(self, token):
        oauth_req = oauth2.Request.from_token_and_callback(token,
                        http_url=AUTHORIZE_URL)
        http = httplib2.Http(proxy_info=self.proxy_info)
        # Force Xero to believe that we are firefox.
        headers = {"User-Agent": "Mozilla/5.0 "\
                                "(Windows; U; Windows NT 5.1; en-GB; "\
                                "rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 "\
                                "GTB7.0 ( .NET CLR 3.5.30729; .NET4.0E)"
        }
        response, content = http.request(oauth_req.to_url(),
                            method=oauth_req.method, headers=headers)
        # The response content-location seems to contain the url to redirect
        # to.
        login_url = response["content-location"]
        sys.stdout.write("Please paste the following url in browser, sign in "
                            "to Xero, and select your application.\n")
        sys.stdout.write("%s\n" % login_url)
        sys.stdout.write("Please enter the numbers that you see on your "
                        "browser:")
        verifier = sys.stdin.readline()[:-1]
        return verifier

    def _get_access_token(self, token):
        oauth_client = oauth2.Client(self.consumer, token=token,
                        proxy_info=self.proxy_info)
        response, content = oauth_client.request(ACCESS_TOKEN_URL, "GET")
        if response["status"] != '200':
            raise XeroException("Invalid response from getting access token:"
                                "%s" % response["status"])
        # Set this token for the auth request.
        return oauth2.Token.from_string(content)

    def authorise(self):
        req_token = self._get_request_token()
        verifier = self._authorise_token(req_token)
        req_token.set_verifier(verifier)
        self.access_token = self._get_access_token(req_token)
        self.client = oauth2.Client(self.consumer, self.access_token,
                        proxy_info=self.proxy_info)

    def request(self, uri, method="GET", body=None, headers=None):
        response, content = self.client.request(uri, method, body, headers)
        if response["status"] != "200":
            raise XeroException("%s\n%s" % (response, content))
        return response, content