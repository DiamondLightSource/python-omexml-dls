

import logging
import re
import uuid

from numpy import asarray

from .utils import *
from .type_checker import TypeChecker

class Types(object):
    def __init__(self):
        self.type_checker = TypeChecker()

    # Simple
    class LSID(object):
        def __init__(self, restriction="\S+"):
            '''
            Setting the appropriate restriction converts LSID into different ID types
            e.g. annotation_id = LSID(); annotation_id.restriction = "Annotation" would create the AnnotationID type.
            See Simple Types @ https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome.html
            '''
            self._set_restriction(restriction)
        
        def _set_restriction(self, value):
            self._restriction = restriction
            self._create_pattern()
        
        def get_restriction(self):
            return self._restriction
        
        restriction = property(get_restriction, None)   # Restriction should be set upon creation.
        
        def _create_pattern(self):
            self.pattern = "(urn:lsid:([\w\-\.]+\.[\w\-\.]+)+:{0}:\S+)|({0}:\S+)".format(self.restriction)

        def check_ID(self, value):
            return re.match(self.pattern, value, flags=re.IGNORECASE)

        def get_ID(self):
            return self.node.get("ID")

        def set_ID(self, value):
            try:
                if not self.check_ID(value):
                    raise ValueError
                self.node.set("ID", value)
            except ValueError:
                logging.error("ID must match pattern")
        ID = property(get_ID, set_ID)

            
    class Binning(object):
        def __init__(self, node):
            self.node = node
            self.pattern = "\dx\d"

        def get_Binning(self):
            return self.node.get("Binning")

        def set_Binning(self, value):
            '''Sets binning in the form "8x8". If an int is given, it will be changed into this form.'''
            if isinstance(value, int):
                value = "%ix%i" %(value, value)
                self.node.set("Binning", value)
            elif isinstance(value, str):
                if re.match(self.pattern, value):
                    self.node.set("Binning", value)
            logging.error('Binning must be either an integer or in the form "8x8"')
        Binning = property(get_Binning, set_Binning)


    # Complex

    class AffineTransform(object):
        def __init__(self, node):
            '''
            A matrix used to transform the shape.
            ⎡ A00, A01, A02 ⎤
            ⎢ A10, A11, A12 ⎥
            ⎣ 0,   0,   1   ⎦
            '''
            self.node = node
        
        def get_A00(self):
            return self.node.get("A00")

        def set_A00(self, value):
            try:
                self.node.set("A00", float(value))
            except ValueError:
                logging.error("Transform matrix values must be castable to float")
                raise
        
        A00 = property(get_A00, set_A00)

        def get_A01(self):
            return self.node.get("A01")

        def set_A01(self, value):
            try:
                self.node.set("A01", float(value))
            except ValueError:
                logging.error("Transform matrix values must be castable to float")
                raise
        
        A01 = property(get_A01, set_A01)

        def get_A02(self):
            return self.node.get("A02")

        def set_A02(self, value):
            try:
                self.node.set("A02", float(value))
            except ValueError:
                logging.error("Transform matrix values must be castable to float")
                raise
        
        A02 = property(get_A02, set_A02)

        def get_A10(self):
            return self.node.get("A10")

        def set_A10(self, value):
            try:
                self.node.set("A10", float(value))
            except ValueError:
                logging.error("Transform matrix values must be castable to float")
                raise
        
        A10 = property(get_A10, set_A10)

        def get_A11(self):
            return self.node.get("A11")

        def set_A11(self, value):
            try:
                self.node.set("A11", float(value))
            except ValueError:
                logging.error("Transform matrix values must be castable to float")
                raise
        
        A11 = property(get_A11, set_A11)

        def get_A12(self):
            return self.node.get("A12")

        def set_A12(self, value):
            try:
                self.node.set("A12", float(value))
            except ValueError:
                logging.error("Transform matrix values must be castable to float")
                raise
        
        A12 = property(get_A12, set_A12)

        def get_as_array(self):
            '''
            A matrix used to transform the shape.
            ⎡ A00, A01, A02 ⎤
            ⎢ A10, A11, A12 ⎥
            ⎣ 0,   0,   1   ⎦
            '''
            return asarray([
                [self.A00,  self.A01,   self.A02],
                [self.A10,  self.A11,   self.A12],
                [0,         0,          1]
                ])

        def set_from_array(self, array):
            '''
            A matrix used to transform the shape.
            ⎡ A00, A01, A02 ⎤
            ⎢ A10, A11, A12 ⎥
            ⎣ 0,   0,   1   ⎦
            '''
            try:
                array = array.astype("f", copy=True)
                self.A00, self.A01, self.A02 = array[0, 0:3]
                self.A10, self.A11, self.A12 = array[1, 0:3]
            except ValueError:
                logging.error("Transform matrix values must be castable to float"
                              " and have the shape 2,3 (anything beyond this will be ignored)")
                raise
        
        array = property(get_as_array, set_from_array)


    class Annotation(LSID):
        def __init__(self, node, ID=None, namespace=None):
            super().__init__("Annotation")
            self.node = node
            self.ns = get_namespaces(self.node)
            if self.ns is None:
                self.ns  = get_namespaces(self.node)
            if ID is not None:
                self.ID = ID
            elif self.ID is None:
                logging.warning("ID is required by the node")
            # We recommend the inclusion of a namespace for annotations you
            # define. If it is absent then we assume the annotation is to
            # use our (OME's) default interpretation for this type.
            self.node.set("namespace", self.ns)
            self.set_ID(str(uuid.uuid4()))
            self.experimenter_id = LSID("Experimenter")
            self.value_type_list = value_type_list
            self.annotation_ref_count = 0

        def get_Annotator(self):
            return self.node.get("Annotator")

        def set_Annotator(self, value):
            if self.experimenter_id.check_ID(value):
                self.node.set("Annotator", value)
        
        Annotator = property(get_Annotator, set_Annotator)

        def get_Description(self):
            description = self.node.find(qn(self.ns["ome"], "Description"))
            if description is None:
                return None
            return get_text(description)

        def set_Description(self, text):
            description = self.node.find(qn(self.ns["ome"], "Description"))
            if description is None:
                description = ElementTree.SubElement(
                    self.node, qn(self.ns["ome"], "Description"))
            try:
                set_text(description, str(text))
            except ValueError:
                logging.error("Description must be castable to string")
                raise
        Description = property(get_Description, set_Description)

        def get_annotation_ref_count(self):
            '''
            The number of annotation references in this annotation

            This can be set with set_annotation_ref_count(value)

            AnnotationRefs can be got using annotation_ref(index)
            ...
            '''
            return len(self.node.findall(qn(self.ns['ome'], "AnnotationRef")))

        def set_annotation_ref_count(self, value):
            assert value >= 0
            annotation_ref_count = self.annotation_ref_count
            if annotation_ref_count > value:
                annotation_refs = self.node.findall(qn(self.ns['ome'], "AnnotationRef"))
                for extra_annotation_refs in annotation_refs[value:]:
                    self.node.remove(extra_annotation_refs)
            else:
                for _ in range(annotation_ref_count, value):
                    new_annotation_ref = Reference(
                        ElementTree.SubElement(self.node, qn(self.ns['ome'], "AnnotationRef")),
                        "Annotation")

        annotation_ref_count = property(get_annotation_ref_count, set_annotation_ref_count)

        def annotation_ref(self, index):
            annotation_refs = self.node.findall(qn(self.ns['ome'], "AnnotationRef"))
            if index > len(annotation_refs):
                logging.error("Trying to get annotation ref with index %i that doesn't not exist."
                              "Create the annotation_refs first using set_annotation_ref_count(value).", index)
                raise ValueError("Trying to get annotation ref with index %i that doesn't not exist." % index)
            return Reference(annotation_refs[index], restriction="Annotation")
        
        def get_Value(self):
            annotation_value = self.node.find(qn(self.ns["ome"], "Value"))
            if annotation_value is None:
                return None
            return get_text(annotation_value)

        def set_Value(self, value):
            annotation_value = self.node.find(qn(self.ns["ome"], "Value"))
            if annotation_value is None:
                annotation_value = ElementTree.SubElement(
                    self.node, qn(self.ns["ome"], "Value"))
            if isinstance(value, self.value_type_list):
                set_text(annotation_value, value)
            else:
                logging.error("Value must be one of the following types: {}".format(
                    self.value_type_list))
        Value = property(get_Value, set_Value)        
        

    class Reference(LSID):
        def __init__(self, node, restriction="\S+", ID=None):
            super().__init__(restriction)
            if ID is not None:
                self.ID = ID
            elif self.ID is None:
                logging.warning("ID is required by the node")
            self.node

    class Settings(Reference):
        def __init__(self, node, restriction="\S+", ID=None):
            super().__init__(node, restriction, ID)


    class ManufacturerSpec(object):
        def __init__(self, node):
            self.node = node

        def get_Manufacturer(self):
            return self.node.get("Manufacturer")
        
        def set_Manufacturer(self, value):
            self.node.set("Manufacturer", value)
        Manufacturer = property(get_Manufacturer, set_Manufacturer)

        def get_Model(self):
            return self.node.get("Model")
        
        def set_Model(self, value):
            self.node.set("Model", value)
        Model = property(get_Model, set_Model)

        def get_SerialNumber(self):
            return self.node.get("SerialNumber")
        
        def set_SerialNumber(self, value):
            self.node.set("SerialNumber", value) 
        SerialNumber = property(get_SerialNumber, set_SerialNumber)

        def get_LotNumber(self):
            return self.node.get("LotNumber")
        
        def set_LotNumber(self, value):
            self.node.set("LotNumber", value)
        LotNumber = property(get_LotNumber, set_LotNumber)


    class Shape(LSID):

        def __init__(self, node, ID=None):
            super().__init__("Shape")
            self.node = node
            self.ns = get_namespaces(self.node)
            if ID is not None:
                self.ID = ID
            elif self.ID is None:
                logging.warning("ID is required by the node")
        
        def get_FillColor(self):
            return self.node.get("FillColor")

        def set_FillColor(self, value):
            if self.type_checker.Color(value):
                self.node.set("FillColor")
        
        FillColor = property(get_FillColor, set_FillColor)

        def get_FillRule(self):
            return self.node.get("FillRule")

        def set_FillRule(self, value):
            allowed = {"EvenOdd", "NonZero"}
            if not value in allowed:
                logging.error("FillRule must be one of the following: %s", allowed)
                raise ValueError
            self.node.set("FillRule")
        
        FillRule = property(get_FillRule, set_FillRule)

        def get_StrokeColor(self):
            return self.node.get("StrokeColor")

        def set_StrokeColor(self, value):
            if self.type_checker.Color(value):
                self.node.set("StrokeColor")

        StrokeColor = property(get_StrokeColor, set_StrokeColor)

        def get_StrokeWidth(self):
            return get_float_attr(self.node, "StrokeWidth")

        def set_StrokeWidth(self, value):
            try:
                self.node.set("StrokeWidth", float(value))
                if self.StrokeWidthUnit is None:
                    self.StrokeWidthUnit = "pixel"
            except ValueError:
                logging.error("StrokeWidth must be castable to float")

        StrokeWidth = property(get_StrokeWidth, set_StrokeWidth)

        def get_StrokeWidthUnit(self):
            return self.node.get("StrokeWidthUnit")

        def set_StrokeWidthUnit(self, value):
            value = str(value)
            if self.type_checker.UnitsLength(value):
                self.node.set("StrokeWidthUnit", value)

        StrokeWidth = property(get_StrokeWidth, set_StrokeWidth)

        def get_StrokeDashArray(self):
            self.node.get("StrokeDashArray")

        def set_StrokeDashArray(self, value):
            self.node.set("StrokeDashArray", str(value))
        
        StrokeDashArray = property(get_StrokeDashArray, set_StrokeDashArray)

        def get_Text(self):
            return self.node.get("Text")

        def set_Text(self, value):
            self.node.set("Text", str(value))

        Text = property(get_Text, set_Text)

        def get_FontFamily(self):
            return self.node.get("FontFamily")

        def set_FontFamily(self, value):
            if self.type_checker.FontFamily(value):
                self.node.set("FontFamily", value)

        def get_FontSize(self):
            return self.node.get("FontSize")

        def set_FontSize(self, value):
            if isinstance(value, int) and value >= 0:
                self.node.set("FontSize", value)
                if self.FontSizeUnit is None:
                    self.FontSizeUnit = "pt"
        
        FontSize = property(get_FontSize, set_FontSize)

        def get_FontSizeUnit(self):
            return self.node.get("FontSizeUnit")

        def set_FontSizeUnit(self, value):
            if self.type_checker.UnitsLength(value):
                self.node.set("FontSizeUnit", value)
        
        FontSizeUnit = property(get_FontSizeUnit, set_FontSizeUnit)

        def get_FontStyle(self):
            return self.node.get("FontStyle")

        def set_FontStyle(self, value):
            allowed = {"Bold", "BoldItalic", "Italic", "Normal"}
            if not value in allowed:
                logging.error("FontStyle must be one of the following: %s", allowed)
                raise ValueError
            self.node.set("FontStyle", value)
        
        FontStyle = property(get_FontStyle, set_FontStyle)

        def get_Locked(self):
            self.node.get("Locked")

        def set_Locked(self, value):
            try:
                self.node.set("Locked", bool(value))
            except ValueError:
                logging.error("Values passed to locked must be either a boolean or castable to a boolean")
                raise
        
        Locked = property(get_Locked, set_Locked)

        def get_TheZ(self):
            '''The Z index of the plane'''
            return get_int_attr(self.node, "TheZ")

        def set_TheZ(self, value):
            if isinstance(value, int) and value >= 0:
                self.node.set("TheZ", value)

        TheZ = property(get_TheZ, set_TheZ)

        def get_TheC(self):
            '''The channel index of the plane'''
            return get_int_attr(self.node, "TheC")

        def set_TheC(self, value):
            if isinstance(value, int) and value >= 0:
                self.node.set("TheC", value)

        TheC = property(get_TheC, set_TheC)

        def get_TheT(self):
            '''The T index of the plane'''
            return get_int_attr(self.node, "TheT")

        def set_TheT(self, value):
            if isinstance(value, int) and value >= 0:
                self.node.set("TheT", value)

        TheT = property(get_TheT, set_TheT)

        def get_Transform(self):
            annotation_value = self.node.find(qn(self.ns["ome"], "Transform"))
            if annotation_value is None:
                return None
            return AffineTransform(annotation_value)
        
        def set_Transform(self, array):
            tform = self.node.find(qn(self.ns["ome"], "Transform"))
            if tform is None:
                tform = ElementTree.SubElement(
                    self.node, qn(self.ns["ome"], "Transform"))
            transform = AffineTransform(tform)
            transform.array = array
        
        Transform = property(get_Transform, set_Transform)       


        def get_annotation_ref_count(self):
            '''
            The number of annotation references in this annotation

            This can be set with set_annotation_ref_count(value)

            AnnotationRefs can be got using annotation_ref(index)
            '''
            return len(self.node.findall(qn(self.ns['ome'], "AnnotationRef")))

        def set_annotation_ref_count(self, value):
            assert value >= 0
            annotation_ref_count = self.annotation_ref_count
            if annotation_ref_count > value:
                annotation_refs = self.node.findall(qn(self.ns['ome'], "AnnotationRef"))
                for extra_annotation_refs in annotation_refs[value:]:
                    self.node.remove(extra_annotation_refs)
            else:
                for _ in range(annotation_ref_count, value):
                    new_annotation_ref = Reference(
                        ElementTree.SubElement(self.node, qn(self.ns['ome'], "AnnotationRef")),
                        "Annotation")

        annotation_ref_count = property(get_annotation_ref_count, set_annotation_ref_count)

        def annotation_ref(self, index):
            annotation_refs = self.node.findall(qn(self.ns['ome'], "AnnotationRef"))
            if index > len(annotation_refs):
                logging.error("Trying to get annotation ref with index %i that doesn't not exist."
                              "Create the annotation_refs first using set_annotation_ref_count(value).", index)
                raise ValueError("Trying to get annotation ref with index %i that doesn't not exist." % index)
            return Reference(annotation_refs[index], restriction="Annotation")


    class LightSource(ManufacturerSpec, LSID):

        def __init__(self, node, ID=None):
            super(ManufacturerSpec, self).__init__()
            super(). __init__("LightSource")
            if ID is not None:
                self.ID = ID
            elif self.ID is None:
                logging.warning("ID is required by the node")
        
        def get_Power(self):
            return get_float_attr(self.node, "Power")
        
        def set_Power(self, value):
            self.node.set("Power", value)
            if not self.get_PowerUnit():
                default_unit = "mW"
                logging.info("Setting PowerUnit to %s", default_unit)
                self.set_PowerUnit(default_unit)
        
        Power = property(get_Power, set_Power)

        def get_PowerUnit(self):
            return self.node.get("PowerUnit")
        
        def set_PowerUnit(self, value):
            self.node.set("PowerUnit", str(value))
        
        PowerUnit = property(get_PowerUnit, set_PowerUnit)
