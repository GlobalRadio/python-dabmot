python-mot
==========

Python API for DAB MOT applications as per ETSI EN 301 234.

This is designed to be used in conjunction with the `python-msc` library and provide MOT objects for encoding and decoding to/from bitstreams.

# Dependencies

# Utilities

# Examples

Creating an MOT object and adding parameters

```python
from mot import MotObject, ContentType

# create MOT object
object = MotObject("TestObject", "\x00" * 1024, ContentType.IMAGE_JFIF)

# add additional parameter - mimetype and absolute expiration
object.add_parameter(MimeType("image/jpg"))
object.add_parameter(AbsoluteExpiration(datetime(2010, 8, 11, 12, 34, 11, 678000)))
```

# Parameters

Parameters exist to cover the full set of core Header and Directory parameters. Other parameters may be used for encoding. In order to register
them for decoding using the standard MOT object decoder, their values must be injected into the `HeaderParameter` object.

For example, for injecting parameter in the SPI specification, decode functions must be registered against their ParamId.

```python
HeaderParameter.decoders[0x25] = ScopeStart.decode_data
HeaderParameter.decoders[0x26] = ScopeEnd.decode_data
HeaderParameter.decoders[0x27] = ScopeId.decode_data
```

The decode function should be a static method taking a single argument of a data bitarray from the Parameter body. For example, from `ScopeId`:

```python
@staticmethod
def decode_data(data):
    return ScopeId(*decode_contentid(data))
```
