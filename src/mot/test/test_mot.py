import unittest
from bitarray import bitarray
from mot import ContentName, MimeType, AbsoluteExpiration, RelativeExpiration, Compression, Priority, DefaultPermitOutdatedVersions, bitarray_to_hex
from datetime import datetime, timedelta

class ContentNameTest(unittest.TestCase):
    
    def test_contentname_latin1(self):
        name = ContentName('TEST')
        tmp = bitarray()
        tmp.frombytes('\xCC\x05\x40\x54\x45\x53\x54')
        assert name.encode() == tmp
        
    def test_contentname_utf(self):
        name = ContentName('TEST', charset=ContentName.ISO_IEC_10646)
        tmp = bitarray()
        tmp.frombytes('\xCC\x05\xF0\x54\x45\x53\x54')
        assert name.encode() == tmp
        
class MimeTypeTest(unittest.TestCase):
    
    def test_mimetype(self):
        mimetype = MimeType("image/png")
        tmp = bitarray()
        tmp.frombytes("\xD0\x09\x69\x6D\x61\x67\x65\x2F\x70\x6E\x67")
        assert mimetype.encode() == tmp
        
class ExpirationTest(unittest.TestCase):
    
    def test_expire_in_5_minutes(self):
        expiration = RelativeExpiration(timedelta(minutes=5))
        tmp = bitarray()
        tmp.frombytes("\x44\x02")
        assert expiration.encode() == tmp
        
    def test_expire_at_set_date_shortform(self):
        expiration = AbsoluteExpiration(datetime(2010, 8, 11, 12, 34, 0 ,0))
        tmp = bitarray()
        tmp.frombytes("\x84\xB6\x1E\xC3\x22")
        assert expiration.encode() == tmp
        
    def test_expire_at_set_date_longform(self):
        expiration = AbsoluteExpiration(datetime(2010, 8, 11, 12, 34, 11, 678000))
        tmp = bitarray()
        tmp.frombytes("\xC4\x06\xB6\x1E\xCB\x22\x2E\xA6")
        assert expiration.encode() == tmp
        
class CompressionType(unittest.TestCase):
    
    def test_gzip(self):
        param = Compression.GZIP
        tmp = bitarray()
        tmp.frombytes("\x51\x01")
        assert param.encode() == tmp
        
class PriorityTest(unittest.TestCase):
    
    def test_priority(self):
        param = Priority(4)
        tmp = bitarray()
        tmp.frombytes("\x4A\x04")
        assert param.encode() == tmp
        
class DefaultPermitOutdatedVersionsTest(unittest.TestCase):
    
    def test_permitted(self):
        param = DefaultPermitOutdatedVersions(True)
        assert bitarray_to_hex(param.encode()) == '41 01'

    def test_forbidden(self):
        param = DefaultPermitOutdatedVersions(False)
        assert bitarray_to_hex(param.encode()) == '41 00'


if __name__ == "__main__":
    unittest.main()
