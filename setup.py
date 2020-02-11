import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="omexml-dls",
    version="1.0.0",
    author="Thomas M Fish",
    author_email="thomas.fish@diamond.ac.uk",
    description="Package for simple and consistent creation and parsing of OME metadata for B24 of Diamond Light Source Ltd.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DiamondLightSource/python-omexml-dls",
    extras_require={
        "test": [
            "pytest"
        ]
    },
    install_requires=[
        "future",
    ],
    py_modules=["oxdls"],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires='>=2.7',
)
