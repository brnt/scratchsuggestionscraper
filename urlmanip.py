import re

class URLManip:
    """Class implementing basic URL manipulation and checking"""
    def splitAddress(self, address):
        addressParts = address.replace("http://", "").split("/")
        return addressParts

    def isID(self, url):
        if re.compile("#").search(url):
            return True
        return False

    def cleanURL(self, url):
        url = url.strip()
        if url[:4] != "http":
            url = "http://" + url
        if url[-1:] != ("/" or "#"):
            url += "/"
        return url

    def cleanHref(self, ref):
        ref = ref.strip()
        if ref[:2] == "./":
            ref = ref[2:]
        elif ref[0] == "/":
            ref = ref[1:]
        return ref