import re
import xml.etree.ElementTree
from xml.etree import cElementTree as ElementTree
import datetime

def xsd_now():
    '''Return the current time in xsd:dateTime format'''
    return datetime.datetime.now().isoformat()

DEFAULT_NOW = xsd_now()
#
# The namespaces
#
NS_DATE = "2016-06"
NS_BINARY_FILE = "http://www.openmicroscopy.org/Schemas/{ns_date}/ome.xsd".format(ns_date=NS_DATE)
NS_ORIGINAL_METADATA = "openmicroscopy.org/OriginalMetadata"
NS_DEFAULT = "http://www.openmicroscopy.org/Schemas/{ns_key}/{ns_date}".format(ns_date=NS_DATE)
NS_RE = r"http://www.openmicroscopy.org/Schemas/(?P<ns_key>.*)/[0-9/-]"

NS_MODULO_ANNOTATION = "openmicroscopy.org/omero/dimension/modulo"
NS_MODULO = "http://www.openmicroscopy.org/Schemas/Additions/2011-09"

default_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Warning: this comment is an OME-XML metadata block, which contains
crucial dimensional parameters and other important metadata. Please edit
cautiously (if at all), and back up the original data before doing so.
For more information, see the OME-TIFF documentation:
https://docs.openmicroscopy.org/latest/ome-model/ome-tiff/ -->
<OME xmlns="{ns_ome_default}"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="{ns_ome_default} %(NS_BINARY_FILE)s">
    <Image ID="Image:0" Name="default.png">
        <AcquisitionDate>%(DEFAULT_NOW)s</AcquisitionDate>
        <Pixels BigEndian="false"
                DimensionOrder="XYCZT"
                ID="Pixels:0"
                Interleaved="false"
                SizeC="1"
                SizeT="1"
                SizeX="512"
                SizeY="512"
                SizeZ="1"
                Type="uint8">
            <Channel ID="Channel:0:0" SamplesPerPixel="1">
                <LightPath/>
            </Channel>
        </Pixels>
    </Image>
  <StructuredAnnotations xmlns="{ns_sa_default}s"/>
</OME>""".format(ns_ome_default=NS_DEFAULT.format(ns_key='ome'), ns_sa_default=NS_DEFAULT.format(ns_key='sa'))

#
# These are the OME-XML pixel types - not all supported by subimager
#
PT_INT8 = "int8"
PT_INT16 = "int16"
PT_INT32 = "int32"
PT_UINT8 = "uint8"
PT_UINT16 = "uint16"
PT_UINT32 = "uint32"
PT_FLOAT = "float"
PT_BIT = "bit"
PT_DOUBLE = "double"
PT_COMPLEX = "complex"
PT_DOUBLECOMPLEX = "double-complex"
#
# The allowed dimension types
#
DO_XYZCT = "XYZCT"
DO_XYZTC = "XYZTC"
DO_XYCTZ = "XYCTZ"
DO_XYCZT = "XYCZT"
DO_XYTCZ = "XYTCZ"
DO_XYTZC = "XYTZC"
#
# Original metadata corresponding to TIFF tags
# The text for these can be found in
# loci.formats.in.BaseTiffReader.initStandardMetadata
#
'''IFD # 254'''
OM_NEW_SUBFILE_TYPE = "NewSubfileType"
'''IFD # 256'''
OM_IMAGE_WIDTH = "ImageWidth"
'''IFD # 257'''
OM_IMAGE_LENGTH = "ImageLength"
'''IFD # 258'''
OM_BITS_PER_SAMPLE = "BitsPerSample"

'''IFD # 262'''
OM_PHOTOMETRIC_INTERPRETATION = "PhotometricInterpretation"
PI_WHITE_IS_ZERO = "WhiteIsZero"
PI_BLACK_IS_ZERO = "BlackIsZero"
PI_RGB = "RGB"
PI_RGB_PALETTE = "Palette"
PI_TRANSPARENCY_MASK = "Transparency Mask"
PI_CMYK = "CMYK"
PI_Y_CB_CR = "YCbCr"
PI_CIE_LAB = "CIELAB"
PI_CFA_ARRAY = "Color Filter Array"

'''BioFormats infers the image type from the photometric interpretation'''
OM_METADATA_PHOTOMETRIC_INTERPRETATION = "MetaDataPhotometricInterpretation"
MPI_RGB = "RGB"
MPI_MONOCHROME = "Monochrome"
MPI_CMYK = "CMYK"

'''IFD # 263'''
OM_THRESHHOLDING = "Threshholding" # (sic)
'''IFD # 264 (but can be 265 if the orientation = 8)'''
OM_CELL_WIDTH = "CellWidth"
'''IFD # 265'''
OM_CELL_LENGTH = "CellLength"
'''IFD # 266'''
OM_FILL_ORDER = "FillOrder"
'''IFD # 279'''
OM_DOCUMENT_NAME = "Document Name"
'''IFD # 271'''
OM_MAKE = "Make"
'''IFD # 272'''
OM_MODEL = "Model"
'''IFD # 274'''
OM_ORIENTATION = "Orientation"
'''IFD # 277'''
OM_SAMPLES_PER_PIXEL = "SamplesPerPixel"
'''IFD # 280'''
OM_MIN_SAMPLE_VALUE = "MinSampleValue"
'''IFD # 281'''
OM_MAX_SAMPLE_VALUE = "MaxSampleValue"
'''IFD # 282'''
OM_X_RESOLUTION = "XResolution"
'''IFD # 283'''
OM_Y_RESOLUTION = "YResolution"
'''IFD # 284'''
OM_PLANAR_CONFIGURATION = "PlanarConfiguration"
PC_CHUNKY = "Chunky"
PC_PLANAR = "Planar"

'''IFD # 286'''
OM_X_POSITION = "XPosition"
'''IFD # 287'''
OM_Y_POSITION = "YPosition"
'''IFD # 288'''
OM_FREE_OFFSETS = "FreeOffsets"
'''IFD # 289'''
OM_FREE_BYTECOUNTS = "FreeByteCounts"
'''IFD # 290'''
OM_GRAY_RESPONSE_UNIT = "GrayResponseUnit"
'''IFD # 291'''
OM_GRAY_RESPONSE_CURVE = "GrayResponseCurve"
'''IFD # 292'''
OM_T4_OPTIONS = "T4Options"
'''IFD # 293'''
OM_T6_OPTIONS = "T6Options"
'''IFD # 296'''
OM_RESOLUTION_UNIT = "ResolutionUnit"
'''IFD # 297'''
OM_PAGE_NUMBER = "PageNumber"
'''IFD # 301'''
OM_TRANSFER_FUNCTION = "TransferFunction"

'''IFD # 305'''
OM_SOFTWARE = "Software"
'''IFD # 306'''
OM_DATE_TIME = "DateTime"
'''IFD # 315'''
OM_ARTIST = "Artist"
'''IFD # 316'''
OM_HOST_COMPUTER = "HostComputer"
'''IFD # 317'''
OM_PREDICTOR = "Predictor"
'''IFD # 318'''
OM_WHITE_POINT = "WhitePoint"
'''IFD # 322'''
OM_TILE_WIDTH = "TileWidth"
'''IFD # 323'''
OM_TILE_LENGTH = "TileLength"
'''IFD # 324'''
OM_TILE_OFFSETS = "TileOffsets"
'''IFD # 325'''
OM_TILE_BYTE_COUNT = "TileByteCount"
'''IFD # 332'''
OM_INK_SET = "InkSet"
'''IFD # 33432'''
OM_COPYRIGHT = "Copyright"
#
# Well row/column naming conventions
#
NC_LETTER = "letter"
NC_NUMBER = "number"

def page_name_original_metadata(index):
    '''Get the key name for the page name metadata data for the indexed tiff page

    These are TIFF IFD #'s 285+

    index - zero-based index of the page
    '''
    return "PageName #%d" % index

def get_text(node):
    '''Get the contents of text nodes in a parent node'''
    return node.text

def set_text(node, text):
    '''Set the text of a parent'''
    node.text = text

def qn(namespace, tag_name):
    '''Return the qualified name for a given namespace and tag name

    This is the ElementTree representation of a qualified name
    '''
    return "{%s}%s" % (namespace, tag_name)

def split_qn(qn):
    '''Split a qualified tag name or return None if namespace not present'''
    m = re.match('\{(.*)\}(.*)', qn)
    return m.group(1), m.group(2) if m else None

def get_namespaces(node):
    '''Get top-level XML namespaces from a node.'''
    ns_lib = {'ome': None, 'sa': None, 'spw': None}
    for child in node.iter():
        ns = split_qn(child.tag)[0]
        match = re.match(NS_RE, ns)
        if match:
            ns_key = match.group('ns_key').lower()
            ns_lib[ns_key] = ns
    return ns_lib

def get_float_attr(node, attribute):
    '''Cast an element attribute to a float or return None if not present'''
    attr = node.get(attribute)
    return None if attr is None else float(attr)

def get_int_attr(node, attribute):
    '''Cast an element attribute to an int or return None if not present'''
    attr = node.get(attribute)
    return None if attr is None else int(attr)

def make_text_node(parent, namespace, tag_name, text):
    '''Either make a new node and add the given text or replace the text

    parent - the parent node to the node to be created or found
    namespace - the namespace of the node's qualified name
    tag_name - the tag name of  the node's qualified name
    text - the text to be inserted
    '''
    qname = qn(namespace, tag_name)
    node = parent.find(qname)
    if node is None:
        node = ElementTree.SubElement(parent, qname)
    set_text(node, text)
