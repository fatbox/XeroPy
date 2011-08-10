"""
A signature method class for RSA signing, for use with oauth2.
Requires M2Crypto
"""
import base64
import hashlib
# Third party
import oauth2
from M2Crypto import RSA

class SignatureMethod_RSA(oauth2.SignatureMethod):
    """ RSA signature not implemented by oauth2."""
    name = "RSA-SHA1"

    def __init__(self, key_path):
        super(oauth2.SignatureMethod, self).__init__()
        self.key_path = key_path
        self.RSA = RSA.load_key(key_path)

    def signing_base(self, request):
        """Calculates the string that needs to be signed."""
        sig = (
            oauth2.escape(request.method),
            oauth2.escape(request.normalized_url),
            oauth2.escape(request.get_normalized_parameters()),
        )
        raw = '&'.join(sig)
        return raw

    def sign(self, request, consumer, token):
        """Returns the signature for the given request.
        Note: consumer and token are not used, but are there to fit in with
        call in oauth2 module.
        """
        raw = self.signing_base(request)
        digest = hashlib.sha1(raw).digest()
        signature = self.RSA.sign(digest, algo="sha1")
        encoded = base64.b64encode(signature)
        return encoded
