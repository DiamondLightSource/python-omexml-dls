# This file has been modified for B24 of Diamond Light Source Ltd. by Thomas M Fish.
# Changes have been made in 2019 and 2020 to primarily to allow additional metadata to be used, 
# in accordance with the OME schema. Other changes have been made for consistency.
#
# Python-bioformats is distributed under the GNU General Public
# License, but this file is licensed under the more permissive BSD
# license.  See the accompanying file LICENSE for details.
#
# Copyright (c) 2009-2014 Broad Institute
# All rights reserved.

"""omexml.py read and write OME xml

"""

from __future__ import absolute_import, unicode_literals

import xml.etree.ElementTree
from xml.etree import cElementTree as ElementTree

import sys
if sys.version_info.major == 3:
    from io import StringIO
    uenc = 'unicode'
else:
    from cStringIO import StringIO
    uenc = 'utf-8'

import datetime
import logging
from functools import reduce
logger = logging.getLogger(__file__)
import re
import uuid

from .types import Types
from .utils import *

class OMEXML(Types):
    '''Reads and writes OME-XML with methods to get and set it.

    The OMEXML class has four main purposes: to parse OME-XML, to output
    OME-XML, to provide a structured mechanism for inspecting OME-XML and to
    let the caller create and modify OME-XML.

    There are two ways to invoke the constructor. If you supply XML as a string
    or unicode string, the constructor will parse it and will use it as the
    base for any inspection and modification. If you don't supply XML, you'll
    get a bland OME-XML object which has a one-channel image. You can modify
    it programatically and get the modified OME-XML back out by calling to_xml.

    There are two ways to get at the XML. The arduous way is to get the
    root_node of the DOM and explore it yourself using the DOM API
    (http://docs.python.org/library/xml.dom.html#module-xml.dom). The easy way,
    where it's supported is to use properties on OMEXML and on some of its
    derived objects. For instance:

    >>> o = OMEXML()
    >>> print o.image().AcquisitionDate

    will get you the date that image # 0 was acquired.

    >>> o = OMEXML()
    >>> o.image().Name = "MyImage"

    will set the image name to "MyImage".

    You can add and remove objects using the "count" properties. Each of these
    handles hooking up and removing orphaned elements for you and should be
    less error prone than creating orphaned elements and attaching them. For
    instance, to create a three-color image:

    >>> o = OMEXML()
    >>> o.image().Pixels.channel_count = 3
    >>> o.image().Pixels.Channel(0).Name = "Red"
    >>> o.image().Pixels.Channel(1).Name = "Green"
    >>> o.image().Pixels.Channel(2).Name = "Blue"

    See the `OME-XML schema documentation <http://git.openmicroscopy.org/src/develop/components/specification/Documentation/Generated/OME-2011-06/ome.html>`_.

    '''
    def __init__(self, xml=None):
        types = Types()
        if xml is None:
            xml = default_xml
        if isinstance(xml, str):
            xml = xml.encode("utf-8")
        try:
            self.dom = ElementTree.ElementTree(ElementTree.fromstring(xml))
        except UnicodeEncodeError:
            xml = xml.encode("utf-8")
            self.dom = ElementTree.ElementTree(ElementTree.fromstring(xml))
        # determine OME namespaces
        self.ns = get_namespaces(self.dom.getroot())
        if self.ns['ome'] is None:
            raise Exception("Error: String not in OME-XML format")

    def __str__(self):
        #
        # need to register the ome namespace because BioFormats expects
        # that namespace to be the default or to be explicitly named "ome"
        #
        for ns_key in ["ome", "sa", "spw"]:
            ns = self.ns.get(ns_key) or NS_DEFAULT.format(ns_key=ns_key)
            ElementTree.register_namespace(ns_key, ns)
        ElementTree.register_namespace("om", NS_ORIGINAL_METADATA)
        result = StringIO()
        ElementTree.ElementTree(self.root_node).write(result,
                                                      encoding=uenc,
                                                      method="xml")
        return result.getvalue()

    def to_xml(self, indent="\t", newline="\n", encoding=uenc):
        return str(self)

    def get_ns(self, key):
        return self.ns[key]

    @property
    def root_node(self):
        return self.dom.getroot()

    def get_image_count(self):
        '''The number of images (= series) specified by the XML'''
        return len(self.root_node.findall(qn(self.ns['ome'], "Image")))

    def set_image_count(self, value):
        '''Add or remove image nodes as needed'''
        assert value > 0
        root = self.root_node
        if self.image_count > value:
            image_nodes = root.find(qn(self.ns['ome'], "Image"))
            for image_node in image_nodes[value:]:
                root.remove(image_node)
        while(self.image_count < value):
            new_image = self.Image(ElementTree.SubElement(root, qn(self.ns['ome'], "Image")))
            new_image.ID = str(uuid.uuid4())
            new_image.Name = "default.png"
            new_image.AcquisitionDate = xsd_now()
            new_pixels = self.Pixels(
                ElementTree.SubElement(new_image.node, qn(self.ns['ome'], "Pixels")))
            new_pixels.ID = str(uuid.uuid4())
            new_pixels.DimensionOrder = DO_XYCTZ
            new_pixels.PixelType = PT_UINT8
            new_pixels.SizeC = 1
            new_pixels.SizeT = 1
            new_pixels.SizeX = 512
            new_pixels.SizeY = 512
            new_pixels.SizeZ = 1
            new_channel = self.Channel(
                ElementTree.SubElement(new_pixels.node, qn(self.ns['ome'], "Channel")))
            new_channel.ID = "Channel%d:0" % self.image_count
            new_channel.Name = new_channel.ID
            new_channel.SamplesPerPixel = 1

    image_count = property(get_image_count, set_image_count)

    @property
    def plates(self):
        return self.PlatesDucktype(self.root_node)

    @property
    def structured_annotations(self):
        '''Return the structured annotations container

        returns a wrapping of OME/StructuredAnnotations. It creates
        the element if it doesn't exist.
        '''
        node = self.root_node.find(qn(self.ns['sa'], "StructuredAnnotations"))
        if node is None:
            node = ElementTree.SubElement(
                self.root_node, qn(self.ns['sa'], "StructuredAnnotations"))
        return self.StructuredAnnotations(node)

    class Image(types.LSID):
        '''Representation of the OME/Image element'''

        def __init__(self, node, image_id=None):
            '''Initialize with the DOM Image node'''
            super().__init__("Image")
            self.ns = get_namespaces(self.node)

        def get_Name(self):
            return self.node.get("Name")
        def set_Name(self, value):
            self.node.set("Name", value)
        Name = property(get_Name, set_Name)

        def get_AcquisitionDate(self):
            '''The date in ISO-8601 format'''
            acquired_date = self.node.find(qn(self.ns["ome"], "AcquisitionDate"))
            if acquired_date is None:
                return None
            return get_text(acquired_date)

        def set_AcquisitionDate(self, date):
            acquired_date = self.node.find(qn(self.ns["ome"], "AcquisitionDate"))
            if acquired_date is None:
                acquired_date = ElementTree.SubElement(
                    self.node, qn(self.ns["ome"], "AcquisitionDate"))
            set_text(acquired_date, date)
        AcquisitionDate = property(get_AcquisitionDate, set_AcquisitionDate)

        def get_ExperimenterRef(self):
            return self.Reference(self.node.find(qn(self.ns['ome'], "ExperimenterRef")))
        def set_ExperimenterRef(self, ID):
            self.Reference(self.node.find(qn(self.ns['ome'], "ExperimenterRef")), ID, "Experimenter")
        ExperimenterRef = property(get_ExperimenterRef, set_ExperimenterRef)

        def get_ExperimentRef(self):
            return self.Reference(self.node.find(qn(self.ns['ome'], "ExperimentRef")))
        def set_ExperimentRef(self, ID):
            self.Reference(self.node.find(qn(self.ns['ome'], "ExperimentRef")), ID, "Experiment")
        ExperimentRef = property(get_ExperimentRef, set_ExperimentRef)

        def get_ExperimenterGroupRef(self):
            return self.Reference(self.node.find(qn(self.ns['ome'], "ExperimenterGroupRef")))
        def set_ExperimenterGroupRef(self, ID):
            self.Reference(self.node.find(qn(self.ns['ome'], "ExperimenterGroupRef")), ID, "ExperimenterGroup")
        ExperimenterGroupRef = property(get_ExperimenterGroupRef, set_ExperimenterGroupRef)

        def get_InstrumentRef(self):
            return self.Reference(self.node.find(qn(self.ns['ome'], "InstrumentRef")))
        def set_InstrumentRef(self, ID):
            self.Reference(self.node.find(qn(self.ns['ome'], "InstrumentRef")), ID, "Instrument")
        InstrumentRef = property(get_InstrumentRef, set_InstrumentRef)

        def get_ObjectiveSettings(self):
            return self.Settings(self.node.find(qn(self.ns['ome'], "ObjectiveSettings")))
        def set_ObjectiveSettings(self, ID):
            self.Settings(self.node.find(qn(self.ns['ome'], "ObjectiveSettings")), ID, "Objective")
        ObjectiveSettings = property(get_ObjectiveSettings, set_ObjectiveSettings)

        @property
        def Pixels(self):
            '''The OME/Image/Pixels element.

            Example:

            >>> md = bioformats.OMEXML(bioformats.get_omexml_metadata(filename))
            >>> pixels = md.image().Pixels
            >>> channel_count = pixels.SizeC
            >>> stack_count = pixels.SizeZ
            >>> timepoint_count = pixels.SizeT

            '''
            return OMEXML.Pixels(self.node.find(qn(self.ns['ome'], "Pixels")))

        def roiref(self, index=0):
            '''The OME/Image/ROIRef element'''
            return OMEXML.ROIRef(self.node.findall(qn(self.ns['ome'], "ROIRef"))[index])

        def get_roiref_count(self):
            return len(self.node.findall(qn(self.ns['ome'], "ROIRef")))
        def set_roiref_count(self, value):
            '''Add or remove roirefs as needed'''
            assert value > 0
            if self.roiref_count > value:
                roiref_nodes = self.node.find(qn(self.ns['ome'], "ROIRef"))
                for roiref_node in roiref_nodes[value:]:
                    self.node.remove(roiref_node)
            while(self.roiref_count < value):
                iteration = self.roiref_count - 1
                new_roiref = OMEXML.ROIRef(ElementTree.SubElement(self.node, qn(self.ns['ome'], "ROIRef")))
                new_roiref.set_ID("ROI:" + str(iteration))

        roiref_count = property(get_roiref_count, set_roiref_count)

    def image(self, index=0):
        '''Return an image node by index'''
        return self.Image(self.root_node.findall(qn(self.ns['ome'], "Image"))[index])

    class Channel(types.LSID):
        '''The OME/Image/Pixels/Channel element'''

        def __init__(self, node, channel_id=None):
            super().__init__("Channel")
            self.ns = get_namespaces(node)

        def get_Name(self):
            return self.node.get("Name")
        def set_Name(self, value):
            self.node.set("Name", value)
        Name = property(get_Name, set_Name)

        def get_SamplesPerPixel(self):
            return get_int_attr(self.node, "SamplesPerPixel")

        def set_SamplesPerPixel(self, value):
            self.node.set("SamplesPerPixel", str(value))
        SamplesPerPixel = property(get_SamplesPerPixel, set_SamplesPerPixel)

        def get_IlluminationType(self):
            self.node.get("IlluminationType")

        def set_IlluminationType(self, value):
            '''The method of illumination used to capture the channel.'''
            self.node.set("IlluminationType", str(value))
        IlluminationType = property(get_IlluminationType, set_IlluminationType)

        def get_PinholeSize(self):
            return get_float_attr(self.node, "PinholeSize")

        def set_PinholeSize(self, value):
            '''
            The optional PinholeSize attribute allows specifying adjustable
            pin hole diameters for confocal microscopes. Units are set by PinholeSizeUnit - default:µm).
            '''
            try:
                value = float(value)
                if value <= 0.0:
                    raise ValueError
                self.node.set("PinholeSize", value)
                if not self.get_PinholeSizeUnit():
                    default_unit = "µm"
                    logging.info("Setting PinholeSizeUnit to %s", default_unit)
                    self.set_PinholeSizeUnit(default_unit)
            except ValueError:
                logging.error("PinholeSize must be a positive number")
                raise
        PinholeSize = property(get_PinholeSize, set_PinholeSize)

        def get_PinholeSizeUnit(self):
            self.node.get("PinholeSizeUnit")

        def set_PinholeSizeUnit(self, value):
            '''The units of the pin hole diameter for confocal microscopes - default:microns[µm].'''
            self.node.set("PinholeSizeUnit", str(value))
        PinholeSizeUnit = property(get_PinholeSizeUnit, set_PinholeSizeUnit)

        def get_AcquisitionMode(self):
            return self.node.get("AcquisitionMode")

        def set_AcquisitionMode(self, value):
            self.node.set("AcquisitionMode", str(value))
        AcquisitionMode = property(get_AcquisitionMode, set_AcquisitionMode)

        def get_ContrastMethod(self):
            return self.node.get("ContrastMethod")

        def set_ContrastMethod(self, value):
            self.node.set("ContrastMethod", str(value))
        ContrastMethod = property(get_ContrastMethod, set_ContrastMethod)

        def get_ExcitationWavelength(self):
            return get_float_attr(self.node, "ExcitationWavelength")

        def set_ExcitationWavelength(self, value):
            try:
                value = float(value)
                if value <= 0.0:
                    raise ValueError
                self.node.set("ExcitationWavelength", value)
                if not self.get_ExcitationWavelengthUnit():
                    default_unit = "nm"
                    logging.info("Setting ExcitationWavelengthUnit to %s", default_unit)
                    self.set_ExcitationWavelengthUnit(default_unit)
            except ValueError:
                logging.error("ExcitationWavelength must be a positive number")
                raise
        ExcitationWavelength = property(get_ExcitationWavelength, set_ExcitationWavelength)

        def get_ExcitationWavelengthUnit(self):
            return self.node.get("ExcitationWavelengthUnit")

        def set_ExcitationWavelengthUnit(self, value):
            '''The units of the wavelength of emission - default:nanometres[nm].'''
            self.node.set("ExcitationWavelengthUnit", str(value))
        ExcitationWavelengthUnit = property(get_ExcitationWavelengthUnit, set_ExcitationWavelengthUnit)

        def get_Flour(self):
            return self.node.get("Flour")

        def set_Flour(self, value):
            '''
            The Fluor attribute is used for fluorescence images.
            This is the name of the fluorophore used to produce this channel [plain text string]
            '''
            self.node.set("Flour", str(value))
        Flour = property(get_Flour, set_Flour)

        def get_NDFilter(self):
            return get_float_attr(self.node, "NDFilter")

        def set_NDFilter(self, value):
            '''
            Annotations-	
            The NDfilter attribute is used to specify the combined effect of any neutral density filters used.
            The amount of light the filter transmits at a maximum [units:none]
            A fraction, as a value from 0.0 to 1.0.

            NOTE: This was formerly described as "units optical density expressed as a PercentFraction".
            This was how the field had been described in the schema from the beginning but all
            the use of it has been in the opposite direction, i.e. as a amount transmitted,
            not the amount blocked. This change has been made to make the model reflect this usage.
            '''
            try:
                value = float(value)
                if value < 0.0 or value > 1.0:
                    raise ValueError
                self.node.set("NDFilter", value)
            except ValueError:
                logging.error("NDFilter must be a number between 0.0 and 1.0")
        NDFilter = property(get_NDFilter, set_NDFilter)

        def get_PocketCellSetting(self):
            return get_int_attr(self.node, "PocketCellSetting")

        def set_PocketCellSetting(self, value):
            '''The PockelCellSetting used for this channel. This is the amount the polarization of the beam is rotated by. [units:none]'''
            try:
                if not isinstance(value, int):
                    raise ValueError
                self.node.set("PocketCellSetting", value)
            except ValueError:
                logging.error("PocketCellSetting must be an integer")
        PocketCellSetting = property(get_PocketCellSetting, set_PocketCellSetting)

        @property
        def LightSourceSettings(self):
            return OMEXML.Objective(self.node.find(qn(self.ns['ome'], "LightSourceSettings")))

        @property
        def DetectorSettings(self):
            return OMEXML.Objective(self.node.find(qn(self.ns['ome'], "DetectorSettings")))

    class LightSourceSettings(types.Settings):
        def __init__(self, node, settings_id=None):
            self.ns = get_namespaces(node)
            super().__init__(node, settings_id)
            
        def get_Attenuation(self):
            return get_float_attr(self.node, "Attenuation")
        
        def set_Attenuation(self, value):
            '''
            The Attenuation of the light source [units:none]
            A fraction, as a value from 0.0 to 1.0.
            '''
            try:
                value = float(value)
                if value > 1.0 or value < 0.0:
                    raise ValueError
                self.node.set("Attenuation", value)
            except ValueError:
                logging.error("Attenuation must be a value between 0.0 and 1.0.")
                raise
        
        Attenuation = property(get_Attenuation, set_Attenuation)

        def get_Wavelength(self):
            return get_float_attr(self.node, "Wavelength")
        
        def set_Wavelength(self, value):
            '''
            The Wavelength of the light source. Units are set by WavelengthUnit, default="nm".
            '''
            try:
                value = float(value)
                if value < 0.0:
                    raise ValueError
                self.node.set("Wavelength", value)
                if not self.get_WavelengthUnit():
                    default_unit = "nm"
                    logging.info("Setting WavelengthUnit to %s", default_unit)
                    self.set_WavelengthUnit(default_unit)
            except ValueError:
                logging.error("Wavelength must be a positive number")
                raise
        
        Wavelength = property(get_Wavelength, set_Wavelength)

        def get_WavelengthUnit(self):
            return self.node.get("WavelengthUnit")
        
        def set_WavelengthUnit(self, value):
            '''Defaults to "nm"'''
            self.node.set("WavelengthUnit", str(value))
        
        WavelengthUnit = property(get_WavelengthUnit, set_WavelengthUnit)


    class DetectorSettings(types.Settings):
        def __init__(self, node, ID=None):
            super().__init__(node, ID=None, restriction="Detector")
            self.node = node
            self.ns = get_namespaces(node)

        def get_Gain(self):
            return get_float_attr(self.node, "Gain")

        def set_Gain(self, value):
            self.node.set("Gain", value)
        
        Gain = property(get_Gain, set_Gain)

        def get_Voltage(self):
            return get_float_attr(self.node, "Voltage")

        def set_Voltage(self, value):
            self.node.set("Voltage", str(value))
        
        Voltage = property(get_Voltage, set_Voltage)

        def get_VoltageUnits(self):
            return self.node.get("VoltageUnits")

        def set_VoltageUnits(self, value):
            self.node.set("VoltageUnits", str(value))
        
        VoltageUnits = property(get_VoltageUnits, set_VoltageUnits)

        def get_Zoom(self):
            return get_float_attr(self.node, "Zoom")

        def set_Zoom(self, value):
            self.node.set("Zoom", value)
        
        Zoom = property(get_Zoom, set_Zoom)

        def get_ReadOutRate(self):
            return get_float_attr(self.node, "ReadOutRate")

        def set_ReadOutRate(self, value):
            '''
            The speed at which the detector can count pixels.  {used:CCD,EMCCD}
            This is the bytes per second that
            can be read from the detector (like a baud rate).
            Units are set by ReadOutRateUnit.
            '''
            try:
                if value <= 0:
                    raise ValueError
                self.node.set("ReadOutRate", float(value))
                if not self.get_ReadOutRateUnit():
                    default_unit = "MHz"
                    logging.info("Setting ReadOutRateUnit to %s", default_unit)
                    self.set_ReadOutRateUnit(default_unit)
            else:
                logging.error("ReadOutRate value must be a positive number")
                raise
        
        ReadOutRate = property(get_ReadOutRate, set_ReadOutRate)

        def get_ReadOutRateUnit(self):
            return self.node.get("ReadOutRateUnit")

        def set_ReadOutRateUnit(self, value):
            '''Defaults to "MHz"'''
            self.node.set("ReadOutRateUnit", str(value))
        
        ReadOutRateUnit = property(get_ReadOutRateUnit, set_ReadOutRateUnit)        

        def get_Binning(self):
            return self.node.get("Binning")

        def set_Binning(self, value):
            '''Sets binning in the form "8x8". If an int is given, it will be changed into this form.'''
            if isinstance(value, int):
                value = "%ix%i" %(value, value)
            self.node.set("Binning", value)
        
        Binning = property(get_Binning, set_Binning)

        def get_Integration(self):
            return get_int_attr(self.node, "Integration")

        def set_Integration(self, value):
            '''This is the number of sequential frames that get averaged, to improve the signal-to-noise ratio.'''
            try:
                if not isinstance(value, int) or value < 1:
                    raise ValueError
                self.node.set("Integration", int(value))
            else:
                logging.error("Integration value must be a positive int")
                raise
        
        Integration = property(get_Integration, set_Integration)


    #---------------------
    # The following section is from the Allen Institute for Cell Science version of this file
    # which can be found at https://github.com/AllenCellModeling/aicsimageio/blob/master/aicsimageio/vendor/omexml.py
    class TiffData(object):
        """The OME/Image/Pixels/TiffData element
        <TiffData FirstC="0" FirstT="0" FirstZ="0" IFD="0" PlaneCount="1">
            <UUID FileName="img40_1.ome.tif">urn:uuid:ef8af211-b6c1-44d4-97de-daca46f16346</UUID>
        </TiffData>
        For our purposes, there will be one TiffData per 2-dimensional image plane.
        """

        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_FirstZ(self):
            '''The Z index of the plane'''
            return get_int_attr(self.node, "FirstZ")

        def set_FirstZ(self, value):
            self.node.set("FirstZ", str(value))

        FirstZ = property(get_FirstZ, set_FirstZ)

        def get_FirstC(self):
            '''The channel index of the plane'''
            return get_int_attr(self.node, "FirstC")

        def set_FirstC(self, value):
            self.node.set("FirstC", str(value))

        FirstC = property(get_FirstC, set_FirstC)

        def get_FirstT(self):
            '''The T index of the plane'''
            return get_int_attr(self.node, "FirstT")

        def set_FirstT(self, value):
            self.node.set("FirstT", str(value))

        FirstT = property(get_FirstT, set_FirstT)

        def get_IFD(self):
            '''plane index within tiff file'''
            return get_int_attr(self.node, "IFD")

        def set_IFD(self, value):
            self.node.set("IFD", str(value))

        IFD = property(get_IFD, set_IFD)

        def get_plane_count(self):
            '''How many planes in this TiffData. Should always be 1'''
            return get_int_attr(self.node, "PlaneCount")

        def set_plane_count(self, value):
            self.node.set("PlaneCount", str(value))

        plane_count = property(get_plane_count, set_plane_count)

    class Plane(object):
        '''The OME/Image/Pixels/Plane element

        The Plane element represents one 2-dimensional image plane. It
        has the Z, C and T indices of the plane and optionally has the
        X, Y, Z, exposure time and a relative time delta.
        '''
        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_TheZ(self):
            '''The Z index of the plane'''
            return get_int_attr(self.node, "TheZ")

        def set_TheZ(self, value):
            self.node.set("TheZ", str(value))

        TheZ = property(get_TheZ, set_TheZ)

        def get_TheC(self):
            '''The channel index of the plane'''
            return get_int_attr(self.node, "TheC")

        def set_TheC(self, value):
            self.node.set("TheC", str(value))

        TheC = property(get_TheC, set_TheC)

        def get_TheT(self):
            '''The T index of the plane'''
            return get_int_attr(self.node, "TheT")

        def set_TheT(self, value):
            self.node.set("TheT", str(value))

        TheT = property(get_TheT, set_TheT)

        def get_DeltaT(self):
            '''# of seconds since the beginning of the experiment'''
            return get_float_attr(self.node, "DeltaT")

        def set_DeltaT(self, value):
            self.node.set("DeltaT", str(value))

        DeltaT = property(get_DeltaT, set_DeltaT)

        def get_ExposureTime(self):
            exposure_time = self.node.get("ExposureTime")
            if exposure_time is not None:
                return float(exposure_time)
            return None

        def set_ExposureTime(self, value):
            '''Units are seconds. Duration of acquisition????'''
            self.node.set("ExposureTime", str(value))

        ExposureTime = property(get_ExposureTime, set_ExposureTime)

        def get_PositionX(self):
            '''X position of stage'''
            position_x = self.node.get("PositionX")
            if position_x is not None:
                return float(position_x)
            return None

        def set_PositionX(self, value):
            self.node.set("PositionX", str(value))

        PositionX = property(get_PositionX, set_PositionX)

        def get_PositionY(self):
            '''Y position of stage'''
            return get_float_attr(self.node, "PositionY")

        def set_PositionY(self, value):
            self.node.set("PositionY", str(value))

        PositionY = property(get_PositionY, set_PositionY)

        def get_PositionZ(self):
            '''Z position of stage'''
            return get_float_attr(self.node, "PositionZ")

        def set_PositionZ(self, value):
            self.node.set("PositionZ", str(value))

        PositionZ = property(get_PositionZ, set_PositionZ)

        def get_PositionXUnit(self):
            return self.node.get("PositionXUnit")

        def set_PositionXUnit(self, value):
            self.node.set("PositionXUnit", str(value))

        PositionXUnit = property(get_PositionXUnit, set_PositionXUnit)

        def get_PositionYUnit(self):
            return self.node.get("PositionYUnit")

        def set_PositionYUnit(self, value):
            self.node.set("PositionYUnit", str(value))

        PositionYUnit = property(get_PositionYUnit, set_PositionYUnit)

        def get_PositionZUnit(self):
            return self.node.get("PositionZUnit")

        def set_PositionZUnit(self, value):
            self.node.set("PositionZUnit", str(value))

        PositionZUnit = property(get_PositionZUnit, set_PositionZUnit)

    class Pixels(object):
        '''The OME/Image/Pixels element

        The Pixels element represents the pixels in an OME image and, for
        an OME-XML encoded image, will actually contain the base-64 encoded
        pixel data. It has the X, Y, Z, C, and T extents of the image
        and it specifies the channel interleaving and channel depth.
        '''
        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_ID(self):
            return self.node.get("ID")
        def set_ID(self, value):
            self.node.set("ID", value)
        ID = property(get_ID, set_ID)

        def get_DimensionOrder(self):
            '''The ordering of image planes in the file

            A 5-letter code indicating the ordering of pixels, from the most
            rapidly varying to least. Use the DO_* constants (for instance
            DO_XYZCT) to compare and set this.
            '''
            return self.node.get("DimensionOrder")
        def set_DimensionOrder(self, value):
            self.node.set("DimensionOrder", value)
        DimensionOrder = property(get_DimensionOrder, set_DimensionOrder)

        def get_PixelType(self):
            '''The pixel bit type, for instance PT_UINT8

            The pixel type specifies the datatype used to encode pixels
            in the image data. You can use the PT_* constants to compare
            and set the pixel type.
            '''
            return self.node.get("Type")

        def get_PhysicalSizeXUnit(self):
            '''The unit of length of a pixel in X direction.'''
            return self.node.get("PhysicalSizeXUnit")
        def set_PhysicalSizeXUnit(self, value):
            self.node.set("PhysicalSizeXUnit", str(value))
        PhysicalSizeXUnit = property(get_PhysicalSizeXUnit, set_PhysicalSizeXUnit)

        def get_PhysicalSizeYUnit(self):
            '''The unit of length of a pixel in Y direction.'''
            return self.node.get("PhysicalSizeYUnit")
        def set_PhysicalSizeYUnit(self, value):
            self.node.set("PhysicalSizeYUnit", str(value))
        PhysicalSizeYUnit = property(get_PhysicalSizeYUnit, set_PhysicalSizeYUnit)

        def get_PhysicalSizeZUnit(self):
            '''The unit of length of a voxel in Z direction.'''
            return self.node.get("PhysicalSizeZUnit")
        def set_PhysicalSizeZUnit(self, value):
            self.node.set("PhysicalSizeZUnit", str(value))
        PhysicalSizeZUnit = property(get_PhysicalSizeZUnit, set_PhysicalSizeZUnit)

        def get_PhysicalSizeX(self):
            '''The length of a single pixel in X direction.'''
            return get_float_attr(self.node, "PhysicalSizeX")
        def set_PhysicalSizeX(self, value):
            self.node.set("PhysicalSizeX", str(value))
        PhysicalSizeX = property(get_PhysicalSizeX, set_PhysicalSizeX)

        def get_PhysicalSizeY(self):
            '''The length of a single pixel in Y direction.'''
            return get_float_attr(self.node, "PhysicalSizeY")
        def set_PhysicalSizeY(self, value):
            self.node.set("PhysicalSizeY", str(value))
        PhysicalSizeY = property(get_PhysicalSizeY, set_PhysicalSizeY)

        def get_PhysicalSizeZ(self):
            '''The size of a voxel in Z direction or None for 2D images.'''
            return get_float_attr(self.node, "PhysicalSizeZ")
        def set_PhysicalSizeZ(self, value):
            self.node.set("PhysicalSizeZ", str(value))
        PhysicalSizeZ = property(get_PhysicalSizeZ, set_PhysicalSizeZ)

        def set_PixelType(self, value):
            self.node.set("Type", value)
        PixelType = property(get_PixelType, set_PixelType)

        def get_SizeX(self):
            '''The dimensions of the image in the X direction in pixels'''
            return get_int_attr(self.node, "SizeX")
        def set_SizeX(self, value):
            self.node.set("SizeX", str(value))
        SizeX = property(get_SizeX, set_SizeX)

        def get_SizeY(self):
            '''The dimensions of the image in the Y direction in pixels'''
            return get_int_attr(self.node, "SizeY")
        def set_SizeY(self, value):
            self.node.set("SizeY", str(value))
        SizeY = property(get_SizeY, set_SizeY)

        def get_SizeZ(self):
            '''The dimensions of the image in the Z direction in pixels'''
            return get_int_attr(self.node, "SizeZ")

        def set_SizeZ(self, value):
            self.node.set("SizeZ", str(value))
        SizeZ = property(get_SizeZ, set_SizeZ)

        def get_SizeT(self):
            '''The dimensions of the image in the T direction in pixels'''
            return get_int_attr(self.node, "SizeT")

        def set_SizeT(self, value):
            self.node.set("SizeT", str(value))
        SizeT = property(get_SizeT, set_SizeT)

        def get_SizeC(self):
            '''The dimensions of the image in the C direction in pixels'''
            return get_int_attr(self.node, "SizeC")
        def set_SizeC(self, value):
            self.node.set("SizeC", str(value))
        SizeC = property(get_SizeC, set_SizeC)

        def get_TimeIncrement(self):
            '''Time increment (default TimeIncrementUnit is "s")'''
            return get_float_attr(self.node, "TimeIncrement")

        def set_TimeIncrement(self, value):
            self.node.set("TimeIncrement", value)
            if not self.get_TimeIncrementUnit():
                default_unit = "s"
                logging.info("Setting TimeIncrementUnit to %s", default_unit)
                self.set_TimeIncrementUnit(default_unit)
        TimeIncrement = property(get_TimeIncrement, set_TimeIncrement)
    
        def get_TimeIncrementUnit(self):
            '''Default is "s"'''
            return self.node.get("TimeIncrementUnit")

        def set_TimeIncrementUnit(self, value):
            return self.node.set("TimeIncrementUnit", str(value))
        TimeIncrementUnit = property(get_TimeIncrementUnit, set_TimeIncrementUnit)

        def get_channel_count(self):
            '''The number of channels in the image

            You can change the number of channels in the image by
            setting the channel_count:

            pixels.channel_count = 3
            pixels.Channel(0).Name = "Red"
            ...
            '''
            return len(self.node.findall(qn(self.ns['ome'], "Channel")))

        def set_channel_count(self, value):
            assert value > 0
            channel_count = self.channel_count
            if channel_count > value:
                channels = self.node.findall(qn(self.ns['ome'], "Channel"))
                for channel in channels[value:]:
                    self.node.remove(channel)
            else:
                for _ in range(channel_count, value):
                    new_channel = OMEXML.Channel(
                        ElementTree.SubElement(self.node, qn(self.ns['ome'], "Channel")))
                    new_channel.ID = str(uuid.uuid4())
                    new_channel.Name = new_channel.ID
                    new_channel.SamplesPerPixel = 1
                    new_channel.Binning("1x1")

        channel_count = property(get_channel_count, set_channel_count)

        def Channel(self, index=0):
            '''Get the indexed channel from the Pixels element'''
            channel = self.node.findall(qn(self.ns['ome'], "Channel"))[index]
            return OMEXML.Channel(channel)
        channel = Channel
        
        def get_plane_count(self):
            '''The number of planes in the image

            An image with only one plane or an interleaved color plane will
            often not have any planes.

            You can change the number of planes in the image by
            setting the plane_count:

            pixels.plane_count = 3
            pixels.Plane(0).TheZ=pixels.Plane(0).TheC=pixels.Plane(0).TheT=0
            ...
            '''
            return len(self.node.findall(qn(self.ns['ome'], "Plane")))

        def set_plane_count(self, value):
            assert value >= 0
            plane_count = self.plane_count
            if plane_count > value:
                planes = self.node.findall(qn(self.ns['ome'], "Plane"))
                for plane in planes[value:]:
                    self.node.remove(plane)
            else:
                for _ in range(plane_count, value):
                    new_plane = OMEXML.Plane(
                        ElementTree.SubElement(self.node, qn(self.ns['ome'], "Plane")))

        plane_count = property(get_plane_count, set_plane_count)

        def Plane(self, index=0):
            '''Get the indexed plane from the Pixels element'''
            plane = self.node.findall(qn(self.ns['ome'], "Plane"))[index]
            return OMEXML.Plane(plane)
        plane = Plane
        
        def get_tiffdata_count(self):
            return len(self.node.findall(qn(self.ns['ome'], "TiffData")))

        def set_tiffdata_count(self, value):
            assert value >= 0
            tiffdatas = self.node.findall(qn(self.ns['ome'], "TiffData"))
            for td in tiffdatas:
                self.node.remove(td)
            for _ in range(0, value):
                new_tiffdata = OMEXML.TiffData(
                    ElementTree.SubElement(self.node, qn(self.ns['ome'], "TiffData")))

        tiffdata_count = property(get_tiffdata_count, set_tiffdata_count)

        def tiffdata(self, index=0):
            data = self.node.findall(qn(self.ns['ome'], "TiffData"))[index]
            return OMEXML.TiffData(data)


    class Instrument(object):
        '''Representation of the OME/Instrument element'''
        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_ID(self):
            return self.node.get("ID")

        def set_ID(self, value):
            self.node.set("ID", value)

        ID = property(get_ID, set_ID)

        @property
        def Microscope(self):
            return OMEXML.Microscope(self.node.find(qn(self.ns['ome'], "Microscope")))

        @property
        def LightSourceGroup(self, index=0):
            return OMEXML.LightSourceGroup(self.node.findall(qn(self.ns['ome'], "LightSourceGroup"))[index])

        @property
        def Objective(self, index=0):
            return OMEXML.Objective(self.node.findall(qn(self.ns['ome'], "Objective"))[index])

        @property
        def Detector(self, index=0):
            return OMEXML.Detector(self.node.findall(qn(self.ns['ome'], "Detector"))[index])

        @property
        def FilterSet(self, index=0):
            return OMEXML.FilterSet(self.node.findall(qn(self.ns['ome'], "FilterSet"))[index])

        @property
        def Filter(self, index=0):
            return OMEXML.Filter(self.node.findall(qn(self.ns['ome'], "Filter"))[index])

        @property
        def Dichroic(self, index=0):
            return OMEXML.Dichroic(self.node.findall(qn(self.ns['ome'], "Dichroic"))[index])

    def instrument(self, index=0):
        return self.Instrument(self.root_node.findall(qn(self.ns['ome'], "Instrument"))[index])


    class Microscope(types.ManufacturerSpec):

        def get_Type(self):
            return self.node.get("Type")
        
        def set_Type(self, value):
            self.node.set("Type", value)
        
        Type = property(get_Type, set_Type)


    class LightSourceGroup(types.LightSource):
        def __init__(self, node):
            super().__init__(node)


    
    class Detector(types.ManufacturerSpec):

        def get_ID(self):
            return self.node.get("ID")
        
        def set_ID(self, value):
            self.node.set("ID", value)
        
        ID = property(get_ID, set_ID)

        def get_Gain(self):
            return get_float_attr(self.node, "Gain")

        def set_Gain(self, value):
            self.node.set("Gain", str(value))
        
        Gain = property(get_Gain, set_Gain)

        def get_Voltage(self):
            return get_float_attr(self.node, "Voltage")

        def set_Voltage(self, value):
            self.node.set("Voltage", str(value))
        
        Voltage = property(get_Voltage, set_Voltage)

        def get_VoltageUnits(self):
            return self.node.get("VoltageUnits")

        def set_VoltageUnits(self, value):
            self.node.set("VoltageUnits", str(value))
        
        VoltageUnits = property(get_VoltageUnits, set_VoltageUnits)

        def get_Type(self):
            return self.node.get("Type")
        
        def set_Type(self, value):
            self.node.set("Type", str(value))
        
        Type = property(get_Type, set_Type)


    class Objective(types.ManufacturerSpec):

        def get_ID(self):
            return self.node.get("ID")
        
        def set_ID(self, value):
            self.node.set("ID", value)
        ID = property(get_ID, set_ID)

        def get_LensNA(self):
            return get_float_attr(self.node, "LensNA")

        def set_LensNA(self, value):
            self.node.set("LensNA", value)
        LensNA = property(get_LensNA, set_LensNA)

        def get_NominalMagnification(self):
            return get_float_attr(self.node, "NominalMagnification")
        
        def set_NominalMagnification(self, value):
            self.node.set("NominalMagnification", value)
        
        NominalMagnification = property(get_NominalMagnification, set_NominalMagnification)

        def get_CalibratedMagnification(self):
            return get_float_attr(self.node, "CalibratedMagnification")
        
        def set_CalibratedMagnification(self, value):
            self.node.set("CalibratedMagnification", value)
        
        CalibratedMagnification = property(get_CalibratedMagnification, set_CalibratedMagnification)

        def get_WorkingDistanceUnit(self):
            return get_int_attr(self.node, "WorkingDistanceUnit")
        
        def set_WorkingDistanceUnit(self, value):
            self.node.set("WorkingDistanceUnit", str(value))
        
        WorkingDistanceUnit = property(get_WorkingDistanceUnit, set_WorkingDistanceUnit)

    class FilterSet(types.ManufacturerSpec):

        def get_ID(self):
            return self.node.get("ID")
        
        def set_ID(self, value):
            self.node.set("ID", value)
        ID = property(get_ID, set_ID)

    class Filter(types.ManufacturerSpec):

        def get_Type(self):
            return self.node.get("Type")
        
        def set_Type(self, value):
            self.node.set("Type", value)
        Type = property(get_Type, set_Type)

        def get_FilterWheel(self):
            return self.node.get("FilterWheel")
        
        def set_FilterWheel(self, value):
            self.node.set("FilterWheel", value)
        FilterWheel = property(get_FilterWheel, set_FilterWheel)

        def get_ID(self):
            return self.node.get("ID")
        
        def set_ID(self, value):
            self.node.set("ID", value)
        ID = property(get_ID, set_ID)


    class Dichroic(types.ManufacturerSpec):

        def get_ID(self):
            return self.node.get("ID")
        
        def set_ID(self, value):
            self.node.set("ID", value)
        ID = property(get_ID, set_ID)

    class StructuredAnnotations(dict):
        '''The OME/StructuredAnnotations element

        Structured annotations let OME-XML represent metadata from other file
        formats, for example the tag metadata in TIFF files. The
        StructuredAnnotations element is a container for the structured
        annotations.

        Images can have structured annotation references. These match to
        the IDs of structured annotations in the StructuredAnnotations
        element. You can get the structured annotations in an OME-XML document
        using a dictionary interface to StructuredAnnotations.

        Pragmatically, TIFF tag metadata is stored as key/value pairs in
        OriginalMetadata annotations - in the context of CellProfiler,
        callers will be using these to read tag data that's not represented
        in OME-XML such as the bits per sample and min and max sample values.

        '''

        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def __getitem__(self, key):
            for child in self.node:
                if child.get("ID") == key:
                    return child
            raise IndexError('ID "%s" not found' % key)

        def __contains__(self, key):
            return self.has_key(key)

        def keys(self):
            return filter(lambda x: x is not None,
                          [child.get("ID") for child in self.node])

        def has_key(self, key):
            for child in self.node:
                if child.get("ID") == key:
                    return True
            return False

        def add_original_metadata(self, key, value):
            '''Create an original data key/value pair

            key - the original metadata's key name, for instance OM_PHOTOMETRIC_INTERPRETATION

            value - the value, for instance, "RGB"

            returns the ID for the structured annotation.
            '''
            xml_annotation = ElementTree.SubElement(
                self.node, qn(self.ns['sa'], "XMLAnnotation"))
            node_id = str(uuid.uuid4())
            xml_annotation.set("ID", node_id)
            xa_value = ElementTree.SubElement(xml_annotation, qn(self.ns['sa'], "Value"))
            ov = ElementTree.SubElement(
                xa_value, qn(NS_ORIGINAL_METADATA, "OriginalMetadata"))
            ov_key = ElementTree.SubElement(ov, qn(NS_ORIGINAL_METADATA, "Key"))
            set_text(ov_key, key)
            ov_value = ElementTree.SubElement(
                ov, qn(NS_ORIGINAL_METADATA, "Value"))
            set_text(ov_value, value)
            return node_id

        def iter_original_metadata(self):
            '''An iterator over the original metadata in structured annotations

            returns (<annotation ID>, (<key, value>))

            where <annotation ID> is the ID attribute of the annotation (which
            can be used to tie an annotation to an image)

                  <key> is the original metadata key, typically one of the
                  OM_* names of a TIFF tag
                  <value> is the value for the metadata
            '''
            #
            # Here's the XML we're traversing:
            #
            # <StructuredAnnotations>
            #    <XMLAnnotation>
            #        <Value>
            #            <OriginalMetadta>
            #                <Key>Foo</Key>
            #                <Value>Bar</Value>
            #            </OriginalMetadata>
            #        </Value>
            #    </XMLAnnotation>
            # </StructuredAnnotations>
            #
            for annotation_node in self.node.findall(qn(self.ns['sa'], "XMLAnnotation")):
                # <XMLAnnotation/>
                annotation_id = annotation_node.get("ID")
                for xa_value_node in annotation_node.findall(qn(self.ns['sa'], "Value")):
                    # <Value/>
                    for om_node in xa_value_node.findall(
                        qn(NS_ORIGINAL_METADATA, "OriginalMetadata")):
                        # <OriginalMetadata>
                        key_node = om_node.find(qn(NS_ORIGINAL_METADATA, "Key"))
                        value_node = om_node.find(qn(NS_ORIGINAL_METADATA, "Value"))
                        if key_node is not None and value_node is not None:
                            key_text = get_text(key_node)
                            value_text = get_text(value_node)
                            if key_text is not None and value_text is not None:
                                yield annotation_id, (key_text, value_text)
                            else:
                                logger.warn("Original metadata was missing key or value:" + om_node.toxml())
            return

        def has_original_metadata(self, key):
            '''True if there is an original metadata item with the given key'''
            return any([k == key
                        for annotation_id, (k, v)
                        in self.iter_original_metadata()])

        def get_original_metadata_value(self, key, default=None):
            '''Return the value for a particular original metadata key

            key - key to search for
            default - default value to return if not found
            '''
            for annotation_id, (k, v) in self.iter_original_metadata():
                if k == key:
                    return v
            return default

        def get_original_metadata_refs(self, ids):
            '''For a given ID, get the matching original metadata references

            ids - collection of IDs to match

            returns a dictionary of key to value
            '''
            d = {}
            for annotation_id, (k,v) in self.iter_original_metadata():
                if annotation_id in ids:
                    d[k] = v
            return d

        @property
        def OriginalMetadata(self):
            return OMEXML.OriginalMetadata(self)

    class OriginalMetadata(dict):
        '''View original metadata as a dictionary

        Original metadata holds "vendor-specific" metadata including TIFF
        tag values.
        '''
        def __init__(self, sa):
            '''Initialized with the structured_annotations class instance'''
            self.sa = sa

        def __getitem__(self, key):
            return self.sa.get_original_metadata_value(key)

        def __setitem__(self, key, value):
            self.sa.add_original_metadata(key, value)

        def __contains__(self, key):
            return self.has_key(key)

        def __iter__(self):
            for annotation_id, (key, value) in self.sa.iter_original_metadata():
                yield key

        def __len__(self):
            return len(list(self.sa_iter_original_metadata()))

        def keys(self):
            return [key
                    for annotation_id, (key, value)
                    in self.sa.iter_original_metadata()]

        def has_key(self, key):
            for annotation_id, (k, value) in self.sa.iter_original_metadata():
                if k == key:
                    return True
            return False

        def iteritems(self):
            for annotation_id, (key, value) in self.sa.iter_original_metadata():
                yield key, value

    class PlatesDucktype(object):
        '''It looks like a list of plates'''
        def __init__(self, root):
            self.root = root
            self.ns = get_namespaces(self.root)

        def __getitem__(self, key):
            plates = self.root.findall(qn(self.ns['spw'], "Plate"))
            if isinstance(key, slice):
                return [OMEXML.Plate(plate) for plate in plates[key]]
            return OMEXML.Plate(plates[key])

        def __len__(self):
            return len(self.root.findall(qn(self.ns['spw'], "Plate")))

        def __iter__(self):
            for plate in self.root.iterfind(qn(self.ns['spw'], "Plate")):
                yield OMEXML.Plate(plate)

        def newPlate(self, name, plate_id = str(uuid.uuid4())):
            new_plate_node = ElementTree.SubElement(
                self.root, qn(self.ns['spw'], "Plate"))
            new_plate = OMEXML.Plate(new_plate_node)
            new_plate.ID = plate_id
            new_plate.Name = name
            return new_plate

    class Plate(object):
        '''The SPW:Plate element

        This represents the plate element of the SPW schema:
        http://www.openmicroscopy.org/Schemas/SPW/2007-06/
        '''
        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_ID(self):
            return self.node.get("ID")

        def set_ID(self, value):
            self.node.set("ID", value)

        ID = property(get_ID, set_ID)

        def get_Name(self):
            return self.node.get("Name")

        def set_Name(self, value):
            self.node.set("Name", value)

        Name = property(get_Name, set_Name)

        def get_Status(self):
            return self.node.get("Status")

        def set_Status(self, value):
            self.node.set("Status", value)

        Status = property(get_Status, set_Status)

        def get_ExternalIdentifier(self):
            return self.node.get("ExternalIdentifier")

        def set_ExternalIdentifier(self, value):
            return self.node.set("ExternalIdentifier", value)

        ExternalIdentifier = property(get_ExternalIdentifier, set_ExternalIdentifier)

        def get_ColumnNamingConvention(self):
            # Consider a default if not defined of NC_NUMBER
            return self.node.get("ColumnNamingConvention")

        def set_ColumnNamingConvention(self, value):
            assert value in (NC_LETTER, NC_NUMBER)
            self.node.set("ColumnNamingConvention", value)
        ColumnNamingConvention = property(get_ColumnNamingConvention,
                                          set_ColumnNamingConvention)

        def get_RowNamingConvention(self):
            # Consider a default if not defined of NC_LETTER
            return self.node.get("RowNamingConvention")

        def set_RowNamingConvention(self, value):
            assert value in (NC_LETTER, NC_NUMBER)
            self.node.set("RowNamingConvention", value)
        RowNamingConvention = property(get_RowNamingConvention,
                                       set_RowNamingConvention)

        def get_WellOriginX(self):
            return get_float_attr(self.node, "WellOriginX")

        def set_WellOriginX(self, value):
            self.node.set("WellOriginX", str(value))
        WellOriginX = property(get_WellOriginX, set_WellOriginX)

        def get_WellOriginY(self):
            return get_float_attr(self.node, "WellOriginY")

        def set_WellOriginY(self, value):
            self.node.set("WellOriginY", str(value))
        WellOriginY = property(get_WellOriginY, set_WellOriginY)

        def get_Rows(self):
            return get_int_attr(self.node, "Rows")

        def set_Rows(self, value):
            self.node.set("Rows", str(value))

        Rows = property(get_Rows, set_Rows)

        def get_Columns(self):
            return get_int_attr(self.node, "Columns")

        def set_Columns(self, value):
            self.node.set("Columns", str(value))

        Columns = property(get_Columns, set_Columns)

        def get_Description(self):
            description = self.node.find(qn(self.ns['spw'], "Description"))
            if description is None:
                return None
            return get_text(description)

        def set_Description(self, text):
            make_text_node(self.node, self.ns['spw'], "Description", text)
        Description = property(get_Description, set_Description)

        def get_Well(self):
            '''The well dictionary / list'''
            return OMEXML.WellsDucktype(self)
        Well = property(get_Well)

        def get_well_name(self, well):
            '''Get a well's name, using the row and column convention'''
            result = "".join([
                "%02d" % (i+1) if convention == NC_NUMBER
                else "ABCDEFGHIJKLMNOP"[i]
                for i, convention
                in ((well.Row, self.RowNamingConvention or NC_LETTER),
                    (well.Column, self.ColumnNamingConvention or NC_NUMBER))])
            return result

    class WellsDucktype(dict):
        '''The WellsDucktype lets you retrieve and create wells

        The WellsDucktype looks like a dictionary but lets you reference
        the wells in a plate using indexing. Types of indexes:

        list indexing: e.g. plate.Well[14] gets the 14th well as it appears
                       in the XML
        dictionary_indexing:
            by well name - e.g. plate.Well["A08"]
            by row and column - e.g. plate.Well[1,3] (B03)
            by ID - e.g. plate.Well["Well:0:0:0"]
        If the ducktype is unable to parse a well name, it assumes you're
        using an ID.
        '''
        def __init__(self, plate):
            self.plate_node = plate.node
            self.plate = plate
            self.ns = get_namespaces(self.plate_node)

        def __len__(self):
            return len(self.plate_node.findall(qn(self.ns['spw'], "Well")))

        def __getitem__(self, key):
            all_wells = self.plate_node.findall(qn(self.ns['spw'], "Well"))
            if isinstance(key, slice):
                return [OMEXML.Well(w) for w in all_wells[key]]
            if hasattr(key, "__len__") and len(key) == 2:
                well = OMEXML.Well(None)
                for w in all_wells:
                    well.node = w
                    if well.Row == key[0] and well.Column == key[1]:
                        return well
            if isinstance(key, int):
                return OMEXML.Well(all_wells[key])
            well = OMEXML.Well(None)
            for w in all_wells:
                well.node = w
                if self.plate.get_well_name(well) == key:
                    return well
                if well.ID == key:
                    return well
            return None

        def __iter__(self):
            '''Return the standard name for all wells on the plate

            for instance, 'B03' for a well with Row=1, Column=2 for a plate
            with the standard row and column naming convention
            '''
            all_wells = self.plate_node.findall(qn(self.ns['spw'], "Well"))
            well = OMEXML.Well(None)
            for w in all_wells:
                well.node = w
                yield self.plate.get_well_name(well)

        def new(self, row, column, well_id = str(uuid.uuid4())):
            '''Create a new well at the given row and column

            row - index of well's row
            column - index of well's column
            well_id - the ID attribute for the well
            '''
            well_node = ElementTree.SubElement(
                self.plate_node, qn(self.ns['spw'], "Well"))
            well = OMEXML.Well(well_node)
            well.Row = row
            well.Column = column
            well.ID = well_id
            return well

    class Well(WellID, Color):
        def __init__(self, node):
            self.node = node

        def get_Column(self):
            return get_int_attr(self.node, "Column")
        def set_Column(self, value):
            self.node.set("Column", str(value))
        Column = property(get_Column, set_Column)

        def get_Row(self):
            return get_int_attr(self.node, "Row")
        def set_Row(self, value):
            self.node.set("Row", str(value))
        Row = property(get_Row, set_Row)

        def get_ID(self):
            return self.node.get("ID")
        def set_ID(self, value):
            self.node.set("ID", value)
        ID = property(get_ID, set_ID)

        def get_Sample(self):
            return OMEXML.WellSampleDucktype(self.node)
        Sample = property(get_Sample)

        def get_ExternalDescription(self):
            return self.node.get("ExternalDescription")

        def set_ExternalDescription(self, value):
            return self.node.set("ExternalDescription", value)

        ExternalDescription = property(get_ExternalDescription, set_ExternalDescription)

        def get_ExternalIdentifier(self):
            return self.node.get("ExternalIdentifier")

        def set_ExternalIdentifier(self, value):
            return self.node.set("ExternalIdentifier", value)

        ExternalIdentifier = property(get_ExternalIdentifier, set_ExternalIdentifier)

        def get_Color(self):
            return int(self.node.get("Color"))

        def set_Color(self, value):
            self.node.set("Color", str(value))
            
        Color = property(get_Color, set_Color)

    class WellSampleDucktype(list):
        '''The WellSample elements in a well

        This is made to look like an indexable list so that you can do
        things like:
        wellsamples[0:2]
        '''
        def __init__(self, well_node):
            self.well_node = well_node
            self.ns = get_namespaces(self.well_node)

        def __len__(self):
            return len(self.well_node.findall(qn(self.ns['spw'], "WellSample")))

        def __getitem__(self, key):
            all_samples = self.well_node.findall(qn(self.ns['spw'], "WellSample"))
            if isinstance(key, slice):
                return [OMEXML.WellSample(s)
                        for s in all_samples[key]]
            return OMEXML.WellSample(all_samples[int(key)])

        def __iter__(self):
            '''Iterate through the well samples.'''
            all_samples = self.well_node.findall(qn(self.ns['spw'], "WellSample"))
            for s in all_samples:
                yield OMEXML.WellSample(s)

        def new(self, wellsample_id = str(uuid.uuid4()), index = None):
            '''Create a new well sample
            '''
            if index is None:
                index = reduce(max, [s.Index for s in self], -1) + 1
            new_node = ElementTree.SubElement(
                self.well_node, qn(self.ns['spw'], "WellSample"))
            s = OMEXML.WellSample(new_node)
            s.ID = wellsample_id
            s.Index = index

    class WellSample(object):
        '''The WellSample is a location within a well'''
        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_ID(self):
            return self.node.get("ID")
        def set_ID(self, value):
            self.node.set("ID", value)
        ID = property(get_ID, set_ID)

        def get_PositionX(self):
            return get_float_attr(self.node, "PositionX")
        def set_PositionX(self, value):
            self.node.set("PositionX", str(value))
        PositionX = property(get_PositionX, set_PositionX)

        def get_PositionY(self):
            return get_float_attr(self.node, "PositionY")

        def set_PositionY(self, value):
            self.node.set("PositionY", str(value))
        PositionY = property(get_PositionY, set_PositionY)

        def get_Timepoint(self):
            return self.node.get("Timepoint") 

        def set_Timepoint(self, value):
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            self.node.set("Timepoint", value)
        Timepoint = property(get_Timepoint, set_Timepoint)

        def get_Index(self):
            return get_int_attr(self.node, "Index")

        def set_Index(self, value):
            self.node.set("Index", str(value))

        Index = property(get_Index, set_Index)

        def get_ImageRef(self):
            '''Get the ID of the image of this site'''
            ref = self.node.find(qn(self.ns['spw'], "ImageRef"))
            if ref is None:
                return None
            return ref.get("ID")

        def set_ImageRef(self, value):
            '''Add a reference to the image of this site'''
            ref = self.node.find(qn(self.ns['spw'], "ImageRef"))
            if ref is None:
                ref = ElementTree.SubElement(self.node, qn(self.ns['spw'], "ImageRef"))
            ref.set("ID", value)
        ImageRef = property(get_ImageRef, set_ImageRef)

    class ROIRef(object):

        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_ID(self):
            return self.node.get("ID")

        def set_ID(self, value):
            '''
            ID will automatically be in the format "ROI:value"
            and must match the ROI ID (that uses the same
            formatting)
            '''
            self.node.set("ID", "ROI:" + str(value))

        ID = property(get_ID, set_ID)

    def get_roi_count(self):
        return len(self.root_node.findall(qn(self.ns['ome'], "ROI")))

    def set_roi_count(self, value):
        '''Add or remove roi nodes as needed'''
        assert value > 0
        root = self.root_node
        if self.roi_count > value:
            roi_nodes = root.find(qn(self.ns['ome'], "ROI"))
            for roi_node in roi_nodes[value:]:
                root.remove(roi_node)
        while(self.roi_count < value):
            iteration = self.roi_count - 1

            new_roi = self.ROI(ElementTree.SubElement(root, qn(self.ns['ome'], "ROI")))
            new_roi.ID = str(iteration)
            new_roi.Name = "Marker " + str(iteration)
            new_Union = self.Union(
                ElementTree.SubElement(new_roi.node, qn(self.ns['ome'], "Union")))
            new_Rectangle = self.Rectangle(
                ElementTree.SubElement(new_Union.node, qn(self.ns['ome'], "Rectangle")))
            new_Rectangle.set_ID("Shape:" + str(iteration) + ":0")
            new_Rectangle.set_TheZ(0)
            new_Rectangle.set_TheC(0)
            new_Rectangle.set_TheT(0)
            new_Rectangle.set_StrokeColor(-16776961)  # Default = Red
            new_Rectangle.set_StrokeWidth(20)
            new_Rectangle.set_Text(str(iteration))
            new_Rectangle.set_Width(512)
            new_Rectangle.set_Height(512)
            new_Rectangle.set_X(0)
            new_Rectangle.set_Y(0)

    roi_count = property(get_roi_count, set_roi_count)
    
    def roi(self, index=0):
        '''Return an ROI node by index'''
        return self.ROI(self.root_node.findall(qn(self.ns['ome'], "ROI"))[index])

    class ROI(object):

        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_ID(self):
            return self.node.get("ID")

        def set_ID(self, value):
            '''
            ID will automatically be in the format "ROI:value"
            and must match the ROIRef ID (that uses the same
            formatting)
            '''
            self.node.set("ID", "ROI:" + str(value))

        ID = property(get_ID, set_ID)

        def get_Name(self):
            return self.node.get("Name")

        def set_Name(self, value):
            self.node.set("Name", str(value))

        Name = property(get_Name, set_Name)

        @property
        def Union(self):
            '''The OME/ROI/Union element.'''
            return OMEXML.Union(self.node.find(qn(self.ns['ome'], "Union")))

    class Union(object):

        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def Rectangle(self):
            '''The OME/ROI/Union element. Currently only rectangle ROIs are available.'''
            return OMEXML.Rectangle(self.node.find(qn(self.ns['ome'], "Rectangle")))

    class Rectangle(object):

        def __init__(self, node):
            self.node = node
            self.ns = get_namespaces(self.node)

        def get_ID(self):
            return self.node.get("ID")

        def set_ID(self, value):
            self.node.set("ID", str(value))

        ID = property(get_ID, set_ID)

        def get_StrokeColor(self):
            return self.node.get("StrokeColor")

        def set_StrokeColor(self, value):
            self.node.set("StrokeColor", str(value))

        StrokeColor = property(get_StrokeColor, set_StrokeColor)

        def get_StrokeWidth(self):
            return self.node.get("StrokeWidth")

        def set_StrokeWidth(self, value):
            '''
            Colour is set using RGBA to integer conversion calculated using function from:
            https://docs.openmicroscopy.org/omero/5.5.1/developers/Python.html
            
            RGB colours: Red=-16776961, Green=16711935, Blue=65535
            '''
            self.node.set("StrokeWidth", str(value))

        StrokeWidth = property(get_StrokeWidth, set_StrokeWidth)

        def get_Text(self):
            return self.node.get("Text")

        def set_Text(self, value):
            self.node.set("Text", str(value))

        Text = property(get_Text, set_Text)

        def get_Height(self):
            return self.node.get("Height")

        def set_Height(self, value):
            self.node.set("Height", str(value))

        Height = property(get_Height, set_Height)

        def get_Width(self):
            return self.node.get("Width")

        def set_Width(self, value):
            self.node.set("Width", str(value))

        Width = property(get_Width, set_Width)

        def get_X(self):
            return self.node.get("X")

        def set_X(self, value):
            self.node.set("X", str(value))

        X = property(get_X, set_X)

        def get_Y(self):
            return self.node.get("Y")

        def set_Y(self, value):
            self.node.set("Y", str(value))

        Y = property(get_Y, set_Y)

        def get_TheZ(self):
            '''The Z index of the plane'''
            return get_int_attr(self.node, "TheZ")

        def set_TheZ(self, value):
            self.node.set("TheZ", str(value))

        TheZ = property(get_TheZ, set_TheZ)

        def get_TheC(self):
            '''The channel index of the plane'''
            return get_int_attr(self.node, "TheC")

        def set_TheC(self, value):
            self.node.set("TheC", str(value))

        TheC = property(get_TheC, set_TheC)

        def get_TheT(self):
            '''The T index of the plane'''
            return get_int_attr(self.node, "TheT")

        def set_TheT(self, value):
            self.node.set("TheT", str(value))

        TheT = property(get_TheT, set_TheT)