from bitarray import bitarray
from msc import int_to_bitarray, bitarray_to_hex, generate_transport_id
from datetime import timedelta, datetime, time
from dateutil.tz import tzutc
import logging
import types

logger = logging.getLogger('mot')

class ContentType:
    '''Content type and subtypes as per ETSI TS 101 756 v1.3.1 (2006-02)'''
    
    def __init__(self, type, subtype):
        self.type = type
        self.subtype = subtype

    def __eq__(self, other):
        if not isinstance(other, ContentType): return False
        return self.type == other.type and self.subtype == other.subtype

    def __hash__(self):
        return hash('%d%d' % (self.type, self.subtype))
        
    def __str__(self):
        return '[%d:%d]' % (self.type, self.subtype)
    
# General Data
ContentType.GENERAL_OBJECT_TRANSFER = ContentType(0, 0)
ContentType.GENERAL_MIME_HTTP = ContentType(0, 1)
    
# Text
ContentType.TEXT_ASCII = ContentType(1, 0)
ContentType.TEXT_ISO = ContentType(1, 1)
ContentType.TEXT_HTML = ContentType(1, 2)
    
# Image
ContentType.IMAGE_GIF = ContentType(2, 0)
ContentType.IMAGE_JFIF = ContentType(2, 1)
ContentType.IMAGE_BMP = ContentType(2, 2)
ContentType.IMAGE_PNG = ContentType(2, 3)
    
# Audio
ContentType.AUDIO_MPEG1_L1 = ContentType(3, 0)
ContentType.AUDIO_MPEG1_L2 = ContentType(3, 1)
ContentType.AUDIO_MPEG1_L3 = ContentType(3, 2)
ContentType.AUDIO_MPEG2_L1 = ContentType(3, 3)
ContentType.AUDIO_MPEG2_L2 = ContentType(3, 4)
ContentType.AUDIO_MPEG2_L3 = ContentType(3, 5)
ContentType.AUDIO_PCM = ContentType(3, 6)
ContentType.AUDIO_AIFF = ContentType(3, 7)
ContentType.AUDIO_ATRAC = ContentType(3, 8)
ContentType.AUDIO_ATRAC2 = ContentType(3, 9)
ContentType.AUDIO_MPEG4 = ContentType(3, 10)
    
# Video
ContentType.VIDEO_MPEG1 = ContentType(4, 0)
ContentType.VIDEO_MPEG2 = ContentType(4, 1)
ContentType.VIDEO_MPEG4 = ContentType(4, 2)
ContentType.VIDEO_H263 = ContentType(4, 3)
    
# MOT Transport
ContentType.MOT_HEADER_UPDATE = ContentType(5, 0)
    
# System
ContentType.SYSTEM_MHEG = ContentType(6, 0)
ContentType.SYSTEM_JAVA = ContentType(6, 1)
    
class MotObject:
    
    def __init__(self, name, body=None, type=ContentType.GENERAL_OBJECT_TRANSFER, transport_id=None):
        self._parameters = {}
        if isinstance(name, basestring): self.add_parameter(ContentName(name))
        else: self.add_parameter(name)
        self._body = body
        self._type = type
        self._transport_id = transport_id if transport_id is not None else generate_transport_id(name)
        
    def add_parameter(self, param):
        if not isinstance(param, HeaderParameter): 
            raise ValueError('parameter {param} of type {type} is not a valid header parameter'.format(param=param, type=param.__class__.__name__))
        self._parameters[param.__class__.__name__] = param
        
    def get_parameters(self):
        return self._parameters.values()
    
    def get_parameter(self, clazz):
        return self._parameters.get(clazz.__name__)
    
    def has_parameter(self, clazz):
        return self.get_parameter(clazz) is not None

    def remove_parameter(self, clazz):
        self._parameters.pop(clazz.__name__)
    
    def get_transport_id(self):
        return self._transport_id
    
    def get_name(self):
        return self.get_parameter(ContentName).name

    def set_body(self, body):
        self._body = body
    
    def get_body(self):
        return self._body
    
    def get_type(self):
        return self._type

    def __str__(self):
        return "{name} [{id}]".format(name=self.get_name(), id=self.get_transport_id())
    
def encode_absolute_time(timepoint):
    
    if timepoint is None: # NOW
        bits = bitarray(32)
        bits.setall(False)
        return bits
        
    bits = bitarray()
    
    # adjust for non-UTC times
    if timepoint.tzinfo is not None and timepoint.tzinfo != tzutc():
        timepoint = timepoint.astimezone(tzutc())
    
    # b0: ValidityFlag: 1 for MJD and UTC are valid
    bits += bitarray('1');
    
    # b1-17: MJD
    a = (14 - timepoint.month) / 12;
    y = timepoint.year + 4800 - a;
    m = timepoint.month + (12 * a) - 3;
    jdn = timepoint.day + ((153 * m) + 2) / 5 + (365 * y) + (y / 4) - (y / 100) + (y / 400) - 32045;
    jd = jdn + (timepoint.hour - 12) / 24 + timepoint.minute / 1440 + timepoint.second / 86400;
    mjd = (int)(jd - 2400000.5);
    bits += int_to_bitarray(mjd, 17)
    
    # b18-19: RFU
    bits += int_to_bitarray(0, 2)

    # b20: UTC Flag
    # b21: UTC - 11 or 27 bits depending on the form
    if timepoint.second > 0:
        bits += bitarray('1')
        bits += int_to_bitarray(timepoint.hour, 5)
        bits += int_to_bitarray(timepoint.minute, 6)
        bits += int_to_bitarray(timepoint.second, 6)
        bits += int_to_bitarray(timepoint.microsecond/1000, 10)
    else:
        bits += bitarray('0')
        bits += int_to_bitarray(timepoint.hour, 5)
        bits += int_to_bitarray(timepoint.minute, 6)

    return bits

def mjd_to_date(mjd):
    return datetime.fromtimestamp((mjd - 40587) * 86400)

def decode_absolute_time(bits):
    
    if not bits.any(): return None # NOW
    
    mjd = int(bits[1:18].to01(), 2)
    date = mjd_to_date(mjd)
    timepoint = datetime.combine(date, time())

    if bits[20]:
        timepoint.replace(hour=int(bits[21:26].to01(), 2))
        timepoint.replace(minute=int(bits[26:32].to01(), 2))
        timepoint.replace(second=int(bits[32:38].to01(), 2))
        timepoint.replace(microsecond=int(bits[38:48].to01(), 2) * 1000)
    else:
        timepoint.replace(hour=int(bits[21:26].to01(), 2))
        timepoint.replace(minute=int(bits[26:32].to01(), 2))    
    return timepoint
    
def encode_relative_time(offset):
    
    bits = bitarray()
    if offset < timedelta(minutes=127):
        minutes = offset.seconds / 60
        two_minutes = minutes / 2 # round to multiples of 2 minutes
        bits += int_to_bitarray(0, 2) # (0-1): Granularity=0
        bits += int_to_bitarray(two_minutes, 6) # (2-7): Interval
    elif offset < timedelta(minutes=1891):
        minutes = offset.seconds / 60
        halfhours = minutes / 30 # round to multiples of 30 minutes
        bits += int_to_bitarray(1, 2) # (0-1): Granularity=1
        bits += int_to_bitarray(halfhours, 6) # (2-7): Interval
    elif offset < timedelta(hours=127):
        hours = offset.seconds / (60 * 60) + offset.days * 24
        twohours = hours / 2
        bits += int_to_bitarray(2, 2) # (0-1): Granularity=2
        bits += int_to_bitarray(twohours, 6) # (2-7): Interval
    elif offset < timedelta(hours=64*24):
        days = offset.days
        bits += int_to_bitarray(2, 3) # (0-1): Granularity=3
        bits += int_to_bitarray(6, days) # (2-7): Interval
    else:
        raise ValueError('relative expiration is greater than the maximum allowed: %s > 63 days' % offset)
    
    return bits

def decode_relative_time(bits):
    raise ValueError('decoding of relative time parameter not done yet')

class UnknownHeaderParameter:

    def __init__(self, id, data):
        self.id = id
        self.data = data

    def __str__(self):
        return 'Unknown header parameter 0x%02x with size %d bytes' % (self.id, self.data.length()/8)

class HeaderParameter:
    
    decoders = {}
    
    def __init__(self, id):
        self.id = id
    
    def encode(self):
        
        # encode the data first
        data = self.encode_data()
        data_length = len(data.tobytes())
        
        bits = bitarray()
        
        # create the correct parameter preamble
        if data_length == 0:
            bits += int_to_bitarray(0, 2) # (0-1): PLI=0
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
        elif data_length == 1:
            bits += int_to_bitarray(1, 2) # (0-1): PLI=1
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
        elif data_length == 4:
            bits += int_to_bitarray(2, 2) # (0-1): PLI=2
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId\
            if data_length < 4: data += bitarray((4 - data_length) * 8)
        elif data_length <= 127:
            bits += int_to_bitarray(3, 2) # (0-1): PLI=3
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
            bits += bitarray('0') # (8): Ext=0
            bits += int_to_bitarray(data_length, 7) # (9-15): DataFieldLength in bytes     
        elif data_length <= 32770:
            bits += int_to_bitarray(3, 2) # (0-1): PLI=3
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
            bits += bitarray('1') # (8): Ext=1
            bits += int_to_bitarray(data_length, 15) # (9-23): DataFieldLength in bytes 
        
        bits += data
        
        return bits
    
    def encode_data(self):
        raise NotImplementedError()
    
    @staticmethod
    def from_bits(bits, i=0):
                
        PLI = int(bits[i:i+2].to01(), 2)
        param_id = int(bits[i+2:i+8].to01(), 2)
        
        if PLI == 0:
            data_start = 1
            data_length = 0
        elif PLI == 1:
            data_start = 1
            data_length = 1
        elif PLI == 2:
            data_start = 1
            data_length = 4
        elif PLI == 3:
            if bits[i+8]:
                data_start = 3 
                data_length = int(bits[i+9:i+24].to01(), 2)
            else:
                data_start = 2 
                data_length = int(bits[i+9:i+16].to01(), 2)
        data = bits[i + (data_start * 8) : i + (data_start * 8) + (data_length * 8)]
        if data_length != data.length()/8: raise ValueError('data length %d is different from signalled data length %d' % (len(data), data_length))
        
        # check we know how to decode this
        if not HeaderParameter.decoders.has_key(param_id):
            raise UnknownHeaderParameter(param_id, bits[i : i + (data_start * 8) + (data_length * 8)])
        decoder = HeaderParameter.decoders[param_id]
        try:
            param = decoder(data)
            logger.debug('decoded parameter %s from param id %d with decoder %s', param, param_id, decoder)
        except:
            logger.error('error decoding parameter from content: header=%s | data=%s | using decoder: %s', 
                         bitarray_to_hex(bits[i:i+(data_start*8)]), bitarray_to_hex(data), decoder)
            raise
        
        return param, data_start + data_length         

class ContentName(HeaderParameter):
    '''Content Name'''
    
    EBU_LATIN = 0
    EBU_LATIN_COMMON_CORE = 1
    EBU_LATIN_CORE = 2
    ISO_LATIN2 = 3
    ISO_LATIN1 = 4
    ISO_IEC_10646 = 15
    
    def __init__(self, name, charset=ISO_LATIN1):
        HeaderParameter.__init__(self, 12)
        self.name = name
        self.charset = charset
        
    def encode_data(self):
        bits = bitarray()
        bits += int_to_bitarray(self.charset, 4) # (0-3): Character set indicator
        bits += int_to_bitarray(0, 4) # (4-7): RFA
        tmp = bitarray()
        tmp.fromstring(self.name)
        bits += tmp
        return bits
    
    @staticmethod
    def decode_data(data):
        charset = int(data[0:4].to01(), 2)
        return ContentName(data[8:].tostring(), charset) # TODO encode to the specific character set
    
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return "<ContentName: %s>" % str(self)
    
        
class MimeType(HeaderParameter):
    '''Content MIME type'''
    
    def __init__(self, mimetype):
        HeaderParameter.__init__(self, 16)
        self.mimetype = mimetype
        
    def encode_data(self):
        bits = bitarray()
        bits.fromstring(self.mimetype)
        return bits
    
    @staticmethod
    def decode_data(data):
        return MimeType(data.tostring())
    
class ExpirationParameter(HeaderParameter):
    
    @staticmethod
    def decode_data(data):
        if len(data)/8 == 1:
            return RelativeExpiration(decode_relative_time(data))
        elif len(data)/8 in [4, 6]:
            return AbsoluteExpiration(decode_absolute_time(data))
        else:
            raise ValueError('unknown data length for expiration: %d bytes' % (len(data)/8))    
    
class RelativeExpiration(ExpirationParameter):
    '''Indicates the maximum time span an object is considered
       valid after the last time the MOT decoder could verify 
       that this object is still broadcast. 
 
       The duration can be at various levels of temporal resolution
       and covered intervals.
 
       two minutes - 2 minutes to 126 minutes
       half hours - half an hour to 31.5 hours
       two hours - 2 hours to 5 days 6 hours'''
    
    def __init__(self, offset):
        HeaderParameter.__init__(self, 4)
        self.offset = offset
        
    def encode_data(self):
        return encode_relative_time(self.offset)
            
class AbsoluteExpiration(ExpirationParameter):
    '''The value, as coded in UTC specifies the absolute time when
       the object expires. The object will not be valid anymore and 
       therefore shall no longer be presented.'''
 
    def __init__(self, timepoint):
        HeaderParameter.__init__(self, 4)
        self.timepoint = timepoint
        
    def encode_data(self):
        return encode_absolute_time(self.timepoint)
           
class Compression(HeaderParameter):
    '''Used to indicate that an object has been compressed and
       which compression algorithm has been applied to the data.'''
          
    def __init__(self, type):
        HeaderParameter.__init__(self, 17)
        self.type = type
        
    def encode_data(self):
        return int_to_bitarray(self.type, 8)
    
    def __eq__(self, that):
        if not isinstance(that, Compression): return False
        return self.type == that.type
    
    @staticmethod
    def decode_data(data):
        return Compression(int(data.to01(), 2))
    
Compression_RESERVED = Compression(0)
Compression.GZIP = Compression(1)    
        
class Priority(HeaderParameter):
    '''Indicates the storage priority, i.e. in case of a memory
       state only the objects having a high priority should
       be stored. It indicates the relevance of the content of the
       particular object for the service.

       The possible values range from 0 = highest to 255 = lowest'''
    
    def __init__(self, priority):
        assert priority >=0 and priority <= 255
        HeaderParameter.__init__(self, 10)
        self.priority = priority
        
    def encode_data(self):
        return int_to_bitarray(self.priority, 8)
    
    @staticmethod
    def decode_data(data):
        return Priority(int(data.to01(), 2))
        
class DirectoryParameter:
    
    def __init__(self, id):
        self.id = id
    
    def encode(self):
        
        # encode the data first
        data = self.encode_data()
        data_length = len(data.tobytes())
        
        bits = bitarray()
        
        # create the correct parameter preamble
        if data_length == 0:
            bits += int_to_bitarray(0, 2) # (0-1): PLI=0
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
        elif data_length == 1:
            bits += int_to_bitarray(1, 2) # (0-1): PLI=1
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
        elif data_length <= 4:
            bits += int_to_bitarray(2, 2) # (0-1): PLI=2
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
        elif data_length <= 127:
            bits += int_to_bitarray(3, 2) # (0-1): PLI=3
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
            bits += bitarray('0') # (8): Ext=0
            bits += int_to_bitarray(data_length, 7) # (9-15): DataFieldLength in bytes     
        elif data_length <= 32770:
            bits += int_to_bitarray(3, 2) # (0-1): PLI=3
            bits += int_to_bitarray(self.id, 6) # (2-7): ParamId
            bits += bitarray('1') # (8): Ext=1
            bits += int_to_bitarray(data_length, 15) # (9-23): DataFieldLength in bytes 
        
        bits += data
        
        return bits

    def encode_data(self):
        return bitarray() 
    
    
class DefaultPermitOutdatedVersions(DirectoryParameter):
    '''When the MOT decoder notices a change to the data carousel then
       the MOT decoder must be told in the new MOT directory if an old
       version of an MOT object can be used until the new version of 
       this object is received.
  
       This parameter defines a default value for all MOT objects that
       do not provide the MOT parameter PermitOutdatedVersions.
 
       If neither parameter is provided, then the MOT decoder shall not 
       present any outdated version of this object.'''
    
    def __init__(self, permit):
        DirectoryParameter.__init__(self, 1)
        self.permit = permit
        
    def encode_data(self):
        bits = bitarray()
        bits.frombytes("\x01" if self.permit else "\x00")
        return bits

class DefaultRelativeExpiration(DirectoryParameter):
    '''Used to indicate a default value that specifies how
       long an object can still be used by the MOT decoder
       after reception loss.
 
       This defines a default value for all MOT objects that do
       not provide the MOT parameter Expiration.
 
       If neither parameter is specified then the MOT object
       never expires.
 
       Indicates the maximum time span an object is considered
       valid after the last time the MOT decoder could verify 
       that this object is still broadcast. 
 
       The duration can be at various levels of temporal resolution
       and covered intervals.
 
       two minutes - 2 minutes to 126 minutes
       half hours - half an hour to 31.5 hours
       two hours - 2 hours to 5 days 6 hours'''
       
    def __init__(self, offset):
        DirectoryParameter.__init__(self, 9)
        self.offset = offset
        
    def encode_data(self):
        return encode_relative_time(self.offset)
    
class DefaultAbsoluteExpiration(DirectoryParameter):
    '''Used to indicate a default value that specifies how
       long an object can still be used by the MOT decoder
       after reception loss.
        
       This defines a default value for all MOT objects that do
       not provide the MOT parameter Expiration.
 
       If neither parameter is specified then the MOT object
       never expires.
 
       The value, as coded in UTC specifies the absolute time when
       the object expires. The object will not be valid anymore and 
       therefore shall no longer be presented.'''
       
    def __init__(self, timepoint):
        DirectoryParameter.__init__(self, 9)
        self.timepoint = timepoint
        
    def encode_data(self):
        return encode_absolute_time(self.timepoint)
    
class SortedHeaderInformation(DirectoryParameter):
    '''Used to signal that the headers within the MOT directory
       are sorted in ascending order of the ContentName
       parameter within every header information block.'''
    
    def __init__(self):
        DirectoryParameter.__init__(self, 0)
        
# register the core parameter decoders
HeaderParameter.decoders[12] = ContentName.decode_data
HeaderParameter.decoders[16] = MimeType.decode_data
HeaderParameter.decoders[4] = ExpirationParameter.decode_data
HeaderParameter.decoders[17] = Compression.decode_data
HeaderParameter.decoders[10] = Priority.decode_data          
        
def is_complete(t, cache):
    
    logger.debug('checking completeness for transport id %d', t)
    
    def check_type_complete(type, transport_id=None):
        if transport_id: 
            datagroups = [x for x in cache[t] if x.get_type() == type]
            logger.debug('found %d datagroups for transport id %d type %d', len(datagroups), transport_id, type)
        else:
            datagroups = []
            for k in cache.keys():
                if cache[k][0].get_type() == type: 
                    datagroups = cache[k]
                    break 
            logger.debug('found %d datagroups for type %d', len(datagroups), type)
        if not len(datagroups): return False
        previous = None
        if datagroups[0].segment_index != 0: 
            return False
        if not datagroups[-1].last: # last datagroup is not signalled last
            return False
        for d in datagroups:
            if previous and d.segment_index != previous.segment_index + 1: 
                return False
            previous = d
        return True
            
    # first check complete bodies
    if not check_type_complete(4, t):
        logger.debug('bodies for transport id %d are not complete', t) 
        return False
    
    # then check for a complete header or a complete directory
    if not check_type_complete(3, t):
        if not check_type_complete(6):
            logger.debug('no complete header and no directory available for object with transport id %s', t)
            return False
        
    return True

def decode_directory_object(data):
    
    logger.debug('decoding directory object from %d bytes of data', len(data))
    
    bits = bitarray()
    bits.frombytes(data)
    
    # parse directory header
    total_size = int(bits[2:32].to01(), 2)
    #if len(data) != total_size: raise ValueError('directory data is different from that signalled: %d != %d bytes', len(data), total_size)
    number_of_objects = int(bits[32:48].to01(), 2)
    logger.debug('directory is signalling that %d objects exist in the carousel', number_of_objects)
    carousel_period = int(bits[48:72].to01(), 2)
    if carousel_period > 0: logger.debug('carousel has a maximum rotation period of %ds', carousel_period/10)
    else: logger.debug('carousel period is undefined')
    segment_size = int(bits[75:88].to01(), 2)
    logger.debug('segment size is %d bytes', segment_size)
    directory_extension_length = int(bits[88:104].to01(), 2)
    logger.debug('directory extension length is %d bytes', directory_extension_length)

    i = 104 + (directory_extension_length * 8) # skip over the directory extenion for now
    
    logger.debug('now parsing header entries')
    headers = {}
    while i < bits.length():
        transport_id = int(bits[i:i+16].to01(), 2)
        logger.debug('parsing header with transport id %d', transport_id)
        i += 16
        
        # core header
        body_size = int(bits[i:i+28].to01(), 2)
        header_size = int(bits[i+28:i+41].to01(), 2)
        content_type = ContentType(int(bits[i+41:i+47].to01(), 2), int(bits[i+47:i+56].to01(), 2))
        logger.debug('core header indicates: body=%d bytes, header=%d bytes, content type=%s', body_size, header_size, content_type)
        end = i + (header_size * 8)
        i += 56
        
        parameters = []
        while i < end:
            try:
                parameter, size = HeaderParameter.from_bits(bits, i)
                parameters.append(parameter)
                i += (size * 8)
                logger.debug('%d bytes of header left to parse for this object', (end - i) / 8)
            except: 
                logger.exception('error parsing parameter %d bytes before the end - skipping rest of parameters', (end - i) / 8)
                i = end
                break
        headers[transport_id] = (content_type, parameters) # tuple for now
    return headers
    
def compile_object(transport_id, cache):
    
    logger.debug('compiling object with transport id %d', transport_id)
    
    params = []
    header = ''
    datagroups = cache[transport_id]

    # compile any headers for this transport ID from header objects
    for datagroup in [x for x in datagroups if x.get_type() == 3]:
        logger.debug('compiling header from datagroup %s', datagroup)
        header += datagroup.get_data() # HAVE TO BE CAREFUL HERE TO ACCOUNT FOR THE SEGMENT HEADER
        
        # parse parameters
        bits = bitarray()
        bits.frombytes(header)
        try:
            type = int(bits[41:47].to01(), 2)
            subtype = int(bits[47:56].to01(), 2)
            content_type = ContentType(type, subtype)
            logger.debug('parsed content type: %s', content_type)
            i = 56
            logger.debug('parsing header parameters')
            while i < len(bits):
                try:
                    param, size = HeaderParameter.from_bits(bits, i)
                    logger.debug('parsed header parameter: %s of size %d', param, size)
                    params.append(param)
                except UnknownHeaderParameter, e:
                    logger.warning('unknown header parameter (0x%02x) at position %d', e.id, (i/8))
                    if not e.data.length(): raise ValueError('unknown header parameter with no size - cannot continue')
                    size = e.data.length() / 8
                i += (size * 8)
        except:
            logger.error('error parsing header: \n%s' % bitarray_to_hex(bits))
            raise
        
    # or check for a directory object and get the parameters from that
    if not len(header):
        logger.debug('compiling header from directory object')
        if not cache.directory:
            directory = ''            
            for k in cache.keys():
                if cache[k][0].get_type() == 6: 
                    for datagroup in cache[k]:
                        directory += datagroup.get_data()
            dir_object = decode_directory_object(directory)
            cache.directory = dir_object
        
        try:
            content_type, params = cache.directory[transport_id]
        except:
            raise
        
    # compile body
    body = ''
    for datagroup in [x for x in datagroups if x.get_type() == 4]:
        body += datagroup.get_data()
              
    name = None
    for param in params:
        if isinstance(param, ContentName): 
            name = param
    if not name: raise ValueError('no name parameter found')
        
    object = MotObject(name, body, content_type, transport_id)
    for param in params: object.add_parameter(param)
    
    # now remove the object from the cache
    cache.pop(transport_id)
      
    return object

class Cache(dict):
    def __init__(self):
        self.directory = None
        
def decode_objects(data, error_callback=None):
    """Decode a series of datagroups and yield the results.
    
    This will either be item by item if the carousel is in Header mode (i.e. once
    both header and body have been acquired), or in bursts of items once the 
    directory has been acquired
    """
        
    cache = Cache() # object cache
    logger.debug('starting to decode objects')
    
    if isinstance(data, bitarray):
        raise NotImplementedError('no support for decoding of objects from a bitarray')
    elif isinstance(data, file):
        raise NotImplementedError('no support for decoding of objects from a file object')
    elif isinstance(data, list) or isinstance(data, types.GeneratorType):
        logger.debug('decoding objects from list/generator: %s', data)
        for d in data:
            logger.debug('got datagroup: %s', d)
            items = cache.get(d.get_transport_id(), [])
            if d not in items: items.append(d)
            items = sorted(items, key=lambda x: (x.get_type(), x.segment_index))
            cache[d.get_transport_id()] = items

            # examine cache for complete objects
            for t in cache.keys():
                if is_complete(t, cache):
                    logger.debug('object with transport id %d is complete', t)
                    object = compile_object(t, cache)
                    yield object
    else:
        raise ValueError('unknown object to decode from: %s' % type(data))
    logger.debug('finished')

class DirectoryEncoder:
    """TODO Encoder for MOT directories, simulates the management of a directory"""

    def __init__(self):
        self.objects = []

    def add(self, object): raise NotImplemented()

    def remove(self, object): raise NotImplemented()

    def clear(self): raise NotImplemented()

    def set(self, objects): raise NotImplemented()
