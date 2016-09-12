import sys
import argparse
from bitarray import bitarray
from msc import bitarray_to_int, bitarray_to_hex

parser = argparse.ArgumentParser(description='print debug a segment bitstream containing an MOT header or body')
parser.add_argument('filename',  nargs='?', help='Read bitstream from named file', default=None)
parser.add_argument('-m', dest='mode', nargs=1, help='Segment decode mode', default='h', required=False)

args = parser.parse_args()
if args.filename:
    print 'decoding from', args.filename
    f = open(args.filename, 'rb')
else:
    f = sys.stdin

buf = bitarray()
r = f.read(1024)
while len(r):
    buf.frombytes(r)
    r = f.read(1024)

def decode_parameters(buf):
    param_index = 1
    while len(buf):
        print 'Parameter', param_index
        print '============'
        pli = bitarray_to_int(buf[0:2])
        param_id = bitarray_to_int(buf[2:8])
        print 'PLI:', pli
        print 'ParamId: %d' % param_id, buf[2:8].to01()
        if pli == 0: 
            buf = buf[8:]
        elif pli == 1:
            print 'data length: 8'
            print 'data:', bitarray_to_hex(buf[8:16])
            buf = buf[16:]
        elif pli == 2:
            print 'data length: 32'
            print 'data:', bitarray_to_hex(buf[8:40])
            buf = buf[40:]
        elif pli == 3:
            ext = buf[8]
            if ext:
                n = bitarray_to_int(buf[9:24]) 
                end = 24+(8*n)
                data = buf[24:end]
            else:
                n = bitarray_to_int(buf[9:16]) 
                end = 16+(8*n)
                data = buf[16:end]
            print 'data length:', n
            print 'data:', bitarray_to_hex(data)
            print 'data:', data.tostring()
            buf = buf[end:]
        print
        param_index += 1
 

def decode_body_segment(buf):
    print 'Body Segment'
    print '============'
    print 'repetition:', bitarray_to_int(buf[0:3])
    print 'size:', bitarray_to_int(buf[2:16])
    print
    buf = buf[16:]

def decode_directory_segment(buf):
    print 'Directory Segment'
    print '=============='
    print 'repetition:', bitarray_to_int(buf[0:3])
    print 'size:', bitarray_to_int(buf[2:16])
    print 
    buf = buf[16:]

    print 'Directory Header'
    print '================'
    print 'directory size:', bitarray_to_int(buf[1:32])
    num_objects = bitarray_to_int(buf[32:48])
    print 'number of objects:', num_objects
    print 'carousel period:', bitarray_to_int(buf[48:72])
    print 'segment size:', bitarray_to_int(buf[75:88])
    directory_extension_length = bitarray_to_int(buf[88:104])
    buf = buf[104:]
    print 'directory extension length', directory_extension_length 
    directory_extension_buf = buf[:directory_extension_length*8]
    buf = buf[directory_extension_length*8:]
    print
    
    decode_parameters(directory_extension_buf)

    for i in range(num_objects):
        print '================='
        print 'Object', i+1
        print '================='
        print 'transport id:', bitarray_to_int(buf[0:16])
        buf = buf[16:]

        print 'Header Core'
        print '==========='
        print 'body size:', bitarray_to_int(buf[0:28])
        header_size = bitarray_to_int(buf[28:41])
        print 'header size:', header_size 
        print 'contenttype:', bitarray_to_int(buf[41:47])
        print 'contentsubtype:', bitarray_to_int(buf[47:56])
        print

        header_buf = buf[56:header_size*8]
        decode_parameters(header_buf)

        buf = buf[header_size*8:]


def decode_header_segment(buf):
    # now decode
    print 'Header Segment'
    print '======='
    print 'repetition:', bitarray_to_int(buf[0:3])
    print 'size:', bitarray_to_int(buf[2:16])
    print 
    buf = buf[16:]

    print 'Header Core'
    print '==========='
    print 'body size:', bitarray_to_int(buf[0:28])
    header_size = bitarray_to_int(buf[28:41])
    print 'header size:', header_size 
    print 'contenttype:', bitarray_to_int(buf[41:47])
    print 'contentsubtype:', bitarray_to_int(buf[47:56])
    print

    header_buf = buf[56:(header_size*8)]
    decode_parameters(header_buf)

    buf = buf[header_size*8:]
            
if args.mode[0] == 'h':
    decode_header_segment(buf)
elif args.mode[0] == 'd': 
    decode_directory_segment(buf)
elif args.mode[0] == 'b':
    decode_body_segment(buf)
else: print 'unknown mode:', args.mode[0]

