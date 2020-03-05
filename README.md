# [omexml-dls](https://github.com/DiamondLightSource/python-omexml-dls)

Package to help simply and consistently create and parse OME metadata for B24 of Diamond Light Source Ltd. This is a modified copy of [python_bioformats](https://github.com/CellProfiler/python-bioformats)' omexml.py with a section from the Allen Institute for Cell Science's [aicsimageio](https://github.com/AllenCellModeling/aicsimageio/tree/master) version of omexml.py (indicated within the file). This package extends capabilities, predominantly in terms of ROIs, while offering a light-weight distribution of the omexml file.

#### Recommended import:
`from oxdls import OMEXML`

## Current changes (compared to python-bioformats)
* TiffData - this allows IFDs to be defined (created using `set_tiffdata_count(value)`) (from [aicsimageio](https://github.com/AllenCellModeling/aicsimageio/tree/master))
* `set_` and `get_ExposureTime()` functions have been added
* X, Y, Z units have been added for each plane
* Square ROIs (an roiref must be created for each ROI first, then ROIs are created using `set_roi_count(value)`, then for each ROI: ROI > Union > Rectangle, where ROI parameters can be set)
* Small formatting changes to improve consistency