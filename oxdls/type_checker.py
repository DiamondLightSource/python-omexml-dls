
class TypeChecker(object):

    @staticmethod
    def Color(value):
        '''
        A simple type that identifies itself as a Color, the value is an integer between -2,147,483,648 and 2,147,483,647 (inclusive).
        The value is a signed 32 bit encoding of RGBA so "-1" is #FFFFFFFF or solid white.
        NOTE: Prior to the 2012-06 schema the default values were incorrect and produced a transparent red not solid white.

        Colour is set using RGBA to integer conversion calculated using function from:
        https://docs.openmicroscopy.org/omero/5.5.1/developers/Python.html
        
        Colours: Red=-16776961, Green=16711935, Blue=65535
        '''
        if isinstance(value, int) and value >= -2147483648 and value <= 2147483647:
            logging.error("%s must be an integer", self.attribute_name)
            return False
        return True

    @staticmethod
    def FontFamily(value):
        '''Options: "serif", "sans-serif", "cursive", "fantasy", or "monospace"'''
        return value in {
            "serif",
            "sans-serif",
            "cursive",
            "fantasy",
            "monospace"
            }

    @staticmethod
    def Marker(value):
        '''Options: "Arrow"'''
        return value in {
            "Arrow"
            }

    @staticmethod
    def PercentFraction(value):
        '''A simple type that restricts the value to a float between 0 and 1 (inclusive).'''
        try:
            value = float(value)
            if value >= 0.0 and value <= 1.0:
                return True
        except ValueError:
            logging.error("Percent fraction must be castable to a float")
        return False

    # Units
    @staticmethod
    def UnitsAngle(value):
        '''Options: "deg", "rad", or "gon"'''
        return value in {
            "deg",  # Degrees
            "rad",  # Radians
            "gon"   # Gradian
            }

    @staticmethod
    def UnitsElectricPotential(value):
        '''
        Options:
            "YV",   # yottavolt
            "ZV",   # zettavolt
            "EV",   # exavolt
            "PV",   # petavolt
            "TV",   # teravolt
            "GV",   # gigavolt
            "MV",   # megavolt
            "kV",   # kilovolt
            "hV",   # hectovolt
            "daV",  # decavolt
            "V",    # volt
            "dV",   # decivolt
            "cV",   # centivolt
            "mV",   # millivolt
            "µV",   # microvolt
            "nv",   # nanovolt
            "pV",   # picovolt
            "fV",   # femtovolt
            "aV",   # attovolt
            "zV",   # zeptovolt
            "yV"    # yoctovolt
        '''
        return value in {
            "YV",   # yottavolt
            "ZV",   # zettavolt
            "EV",   # exavolt
            "PV",   # petavolt
            "TV",   # teravolt
            "GV",   # gigavolt
            "MV",   # megavolt
            "kV",   # kilovolt
            "hV",   # hectovolt
            "daV",  # decavolt
            "V",    # volt
            "dV",   # decivolt
            "cV",   # centivolt
            "mV",   # millivolt
            "µV",   # microvolt
            "nv",   # nanovolt
            "pV",   # picovolt
            "fV",   # femtovolt
            "aV",   # attovolt
            "zV",   # zeptovolt
            "yV"    # yoctovolt
            }

    @staticmethod
    def UnitsFrequency(value):
        '''
        Options:
            "YHz",  # yottahertz
            "ZHz",  # zettahertz
            "EHz",  # exahertz
            "PHz",  # petahertz
            "THz",  # terahertz
            "GHz",  # gigahertz
            "MHz",  # megahertz
            "kHz",  # kilohertz
            "hHz",  # hectohertz
            "daHz", # decahertz
            "Hz",   # hertz
            "dHz",  # decihertz
            "cHz",  # centihertz
            "mHz",  # millihertz
            "µHz",  # microhertz
            "nHz",  # nanohertz
            "pHz",  # picohertz
            "fHz",  # femtohertz
            "aHz",  # attohertz
            "zHz",  # zeptohertz
            "yHz"   # yoctohertz
        '''
        return value in {
            "YHz",  # yottahertz
            "ZHz",  # zettahertz
            "EHz",  # exahertz
            "PHz",  # petahertz
            "THz",  # terahertz
            "GHz",  # gigahertz
            "MHz",  # megahertz
            "kHz",  # kilohertz
            "hHz",  # hectohertz
            "daHz", # decahertz
            "Hz",   # hertz
            "dHz",  # decihertz
            "cHz",  # centihertz
            "mHz",  # millihertz
            "µHz",  # microhertz
            "nHz",  # nanohertz
            "pHz",  # picohertz
            "fHz",  # femtohertz
            "aHz",  # attohertz
            "zHz",  # zeptohertz
            "yHz"   # yoctohertz
        }

    @staticmethod
    def UnitsLength(value):
        '''
        Options:
            "Ym",   # yottameter SI unit.
            "Zm",   # zettameter SI unit.
            "Em",   # exameter SI unit.
            "Pm",   # petameter SI unit.
            "Tm",   # terameter SI unit.
            "Gm",   # gigameter SI unit.
            "Mm",   # megameter SI unit.
            "km",   # kilometer SI unit.
            "hm",   # hectometer SI unit.
            "dam",  # decameter SI unit.
            "m",    # meter SI unit.
            "dm",   # decimeter SI unit.
            "cm",   # centimeter SI unit.
            "mm",   # millimeter SI unit.
            "µm",   # micrometer SI unit.
            "nm",   # nanometer SI unit.
            "pm",   # picometer SI unit.
            "fm",   # femtometer SI unit.
            "am",   # attometer SI unit.
            "zm",   # zeptometer SI unit.
            "ym",   # yoctometer SI unit.
            "Å",    # ångström SI-derived unit.
            "thou", # thou Imperial unit (or mil, 1/1000 inch).
            "li",   # line Imperial unit (1/12 inch).
            "in",   # inch Imperial unit.
            "ft",   # foot Imperial unit.
            "yd",   # yard Imperial unit.
            "mi",   # terrestrial mile Imperial unit.
            "ua",   # astronomical unit SI-derived unit. The official term is ua as the SI standard assigned AU to absorbance unit.
            "ly",   # light year.
            "pc",   # parsec.
            "pt",   # typography point Imperial-derived unit (1/72 inch). Use of this unit should be limited to font sizes.
            "pixel",    # pixel abstract unit.  This is not convertible to any other length unit without a calibrated scaling factor. Its use should should be limited to ROI objects, and converted to an appropriate length units using the PhysicalSize units of the Image the ROI is attached to.
            "reference frame",    # reference frame abstract unit.  This is not convertible to any other length unit without a scaling factor.  Its use should be limited to uncalibrated stage positions, and converted to an appropriate length unit using a calibrated scaling factor
        '''
        return value in {
            "Ym",   # yottameter SI unit.
            "Zm",   # zettameter SI unit.
            "Em",   # exameter SI unit.
            "Pm",   # petameter SI unit.
            "Tm",   # terameter SI unit.
            "Gm",   # gigameter SI unit.
            "Mm",   # megameter SI unit.
            "km",   # kilometer SI unit.
            "hm",   # hectometer SI unit.
            "dam",  # decameter SI unit.
            "m",    # meter SI unit.
            "dm",   # decimeter SI unit.
            "cm",   # centimeter SI unit.
            "mm",   # millimeter SI unit.
            "µm",   # micrometer SI unit.
            "nm",   # nanometer SI unit.
            "pm",   # picometer SI unit.
            "fm",   # femtometer SI unit.
            "am",   # attometer SI unit.
            "zm",   # zeptometer SI unit.
            "ym",   # yoctometer SI unit.
            "Å",    # ångström SI-derived unit.
            "thou", # thou Imperial unit (or mil, 1/1000 inch).
            "li",   # line Imperial unit (1/12 inch).
            "in",   # inch Imperial unit.
            "ft",   # foot Imperial unit.
            "yd",   # yard Imperial unit.
            "mi",   # terrestrial mile Imperial unit.
            "ua",   # astronomical unit SI-derived unit. The official term is ua as the SI standard assigned AU to absorbance unit.
            "ly",   # light year.
            "pc",   # parsec.
            "pt",   # typography point Imperial-derived unit (1/72 inch). Use of this unit should be limited to font sizes.
            "pixel",    # pixel abstract unit.  This is not convertible to any other length unit without a calibrated scaling factor. Its use should should be limited to ROI objects, and converted to an appropriate length units using the PhysicalSize units of the Image the ROI is attached to.
            "reference frame",    # reference frame abstract unit.  This is not convertible to any other length unit without a scaling factor.  Its use should be limited to uncalibrated stage positions, and converted to an appropriate length unit using a calibrated scaling factor
        }

    @staticmethod
    def UnitsPower(value):
        '''
        Options:
            "YW",   # yottawatt unit.
            "ZW",   # zettawatt unit.
            "EW",   # exawatt unit.
            "PW",   # petawatt unit.
            "TW",   # terawatt unit.
            "GW",   # gigawatt unit.
            "MW",   # megawatt unit.
            "kW",   # kilowatt unit.
            "hW",   # hectowatt unit.
            "daW",  # decawatt unit.
            "W",    # watt unit.
            "dW",   # deciwatt unit.
            "cW",   # centiwatt unit.
            "mW",   # milliwatt unit.
            "µW",   # microwatt unit.
            "nW",   # nanowatt unit.
            "pW",   # picowatt unit.
            "fW",   # femtowatt unit.
            "aW",   # attowatt unit.
            "zW",   # zeptowatt unit.
            "yW",   # yoctowatt unit.
        '''
        return value in {
            "YW",   # yottawatt unit.
            "ZW",   # zettawatt unit.
            "EW",   # exawatt unit.
            "PW",   # petawatt unit.
            "TW",   # terawatt unit.
            "GW",   # gigawatt unit.
            "MW",   # megawatt unit.
            "kW",   # kilowatt unit.
            "hW",   # hectowatt unit.
            "daW",  # decawatt unit.
            "W",    # watt unit.
            "dW",   # deciwatt unit.
            "cW",   # centiwatt unit.
            "mW",   # milliwatt unit.
            "µW",   # microwatt unit.
            "nW",   # nanowatt unit.
            "pW",   # picowatt unit.
            "fW",   # femtowatt unit.
            "aW",   # attowatt unit.
            "zW",   # zeptowatt unit.
            "yW",   # yoctowatt unit.
        }

    @staticmethod
    def UnitsPressure(value):
        '''
        Options:
            "YPa",  # yottapascal SI unit.
            "ZPa",  # zettapascal SI unit.
            "EPa",  # exapascal SI unit.
            "PPa",  # petapascal SI unit.
            "TPa",  # terapascal SI unit.
            "GPa",  # gigapascal SI unit.
            "MPa",  # megapascal SI unit.
            "kPa",  # kilopascal SI unit.
            "hPa",  # hectopascal SI unit.
            "daPa", # decapascal SI unit.
            "Pa",   # pascal SI unit.  Note the C++ enum is mixed case due to PASCAL being a macro used by the Microsoft C and C++ compiler.
            "dPa",  # decipascal SI unit.
            "cPa",  # centipascal SI unit.
            "mPa",  # millipascal SI unit.
            "µPa",  # micropascal SI unit.
            "nPa",  # nanopascal SI unit.
            "pPa",  # picopascal SI unit.
            "fPa",  # femtopascal SI unit.
            "aPa",  # attopascal SI unit.
            "zPa",  # zeptopascal SI unit.
            "yPa",  # yoctopascal SI unit.
            "bar",  # bar SI-derived unit.
            "Mbar", # megabar SI-derived unit.
            "kbar", # kilobar SI-derived unit.
            "dbar", # decibar SI-derived unit.
            "cbar", # centibar SI-derived unit.
            "mbar", # millibar SI-derived unit.
            "atm",  # standard atmosphere SI-derived unit.
            "psi",  # pound-force per square inch Imperial unit.
            "Torr", # torr SI-derived unit.
            "mTorr",# millitorr SI-derived unit.
            "mm Hg",# millimetre of mercury SI-derived unit
        '''
        return value in {
            "YPa",  # yottapascal SI unit.
            "ZPa",  # zettapascal SI unit.
            "EPa",  # exapascal SI unit.
            "PPa",  # petapascal SI unit.
            "TPa",  # terapascal SI unit.
            "GPa",  # gigapascal SI unit.
            "MPa",  # megapascal SI unit.
            "kPa",  # kilopascal SI unit.
            "hPa",  # hectopascal SI unit.
            "daPa", # decapascal SI unit.
            "Pa",   # pascal SI unit.  Note the C++ enum is mixed case due to PASCAL being a macro used by the Microsoft C and C++ compiler.
            "dPa",  # decipascal SI unit.
            "cPa",  # centipascal SI unit.
            "mPa",  # millipascal SI unit.
            "µPa",  # micropascal SI unit.
            "nPa",  # nanopascal SI unit.
            "pPa",  # picopascal SI unit.
            "fPa",  # femtopascal SI unit.
            "aPa",  # attopascal SI unit.
            "zPa",  # zeptopascal SI unit.
            "yPa",  # yoctopascal SI unit.
            "bar",  # bar SI-derived unit.
            "Mbar", # megabar SI-derived unit.
            "kbar", # kilobar SI-derived unit.
            "dbar", # decibar SI-derived unit.
            "cbar", # centibar SI-derived unit.
            "mbar", # millibar SI-derived unit.
            "atm",  # standard atmosphere SI-derived unit.
            "psi",  # pound-force per square inch Imperial unit.
            "Torr", # torr SI-derived unit.
            "mTorr",# millitorr SI-derived unit.
            "mm Hg",# millimetre of mercury SI-derived unit
        }

    @staticmethod
    def UnitsTemperature(value):
        '''
        Options:
            "°C",   # degree Celsius unit.
            "°F",   # degree Fahrenheit unit.
            "K",    # Kelvin unit.
            "°R",   # degree Rankine unit.
        '''
        return value in {
            "°C",   # degree Celsius unit.
            "°F",   # degree Fahrenheit unit.
            "K",    # Kelvin unit.
            "°R",   # degree Rankine unit.
        }

    @staticmethod
    def UnitsTime(value):
        '''
        Options:
            "Ys",   # yottasecond SI unit.
            "Zs",   # zettasecond SI unit.
            "Es",   # exasecond SI unit.
            "Ps",   # petasecond SI unit.
            "Ts",   # terasecond SI unit.
            "Gs",   # gigasecond SI unit.
            "Ms",   # megasecond SI unit.
            "ks",   # kilosecond SI unit.
            "hs",   # hectosecond SI unit.
            "das",  # decasecond SI unit.
            "s",    # second SI unit.
            "ds",   # decisecond SI unit.
            "cs",   # centisecond SI unit.
            "ms",   # millisecond SI unit.
            "µs",   # microsecond SI unit.
            "ns",   # nanosecond SI unit.
            "ps",   # picosecond SI unit.
            "fs",   # femtosecond SI unit.
            "as",   # attosecond SI unit.
            "zs",   # zeptosecond SI unit.
            "ys",   # yoctosecond SI unit.
            "min",  # minute SI-derived unit.
            "h",    # hour SI-derived unit.
            "d",    # day SI-derived unit.
        '''
        return value in {
            "Ys",   # yottasecond SI unit.
            "Zs",   # zettasecond SI unit.
            "Es",   # exasecond SI unit.
            "Ps",   # petasecond SI unit.
            "Ts",   # terasecond SI unit.
            "Gs",   # gigasecond SI unit.
            "Ms",   # megasecond SI unit.
            "ks",   # kilosecond SI unit.
            "hs",   # hectosecond SI unit.
            "das",  # decasecond SI unit.
            "s",    # second SI unit.
            "ds",   # decisecond SI unit.
            "cs",   # centisecond SI unit.
            "ms",   # millisecond SI unit.
            "µs",   # microsecond SI unit.
            "ns",   # nanosecond SI unit.
            "ps",   # picosecond SI unit.
            "fs",   # femtosecond SI unit.
            "as",   # attosecond SI unit.
            "zs",   # zeptosecond SI unit.
            "ys",   # yoctosecond SI unit.
            "min",  # minute SI-derived unit.
            "h",    # hour SI-derived unit.
            "d",    # day SI-derived unit.
        }
