import requests
import geocoder
import math
from datetime import datetime, timezone


class Calculations():
    def __init__(self):
        self.lat_deg = 0
        self.lat_min = 0
        self.long_deg = 0
        self.long_min = 0
        self.dec_deg = 0
        self.dec_min = 0
        self.ra_hour = 0
        self.ra_min = 0
        self.altitude = 0
        self.azimuth = 0
        self.magdec = 0
        self.object = ""

    def getDeclination(self, lat1, long1):
        URL = "https://www.ngdc.noaa.gov/geomag-web/calculators/calculateDeclination?lat1=" + str(
            lat1) + "&lon1=" + str(long1) + "&key=zNEw7&resultFormat=json"
        page = requests.get(URL)

        contents = page.text
        contents = contents.split(",")
        self.magdec = float(((contents[2]).split(":"))[1])

    def getObjectInfo(self):
        URL = "https://in-the-sky.org/data/object.php?id=" + self.object
        page = requests.get(URL)

        contents = page.text
        try:
            contents = (contents.split("Right ascension:</td><td>"))[1]
            contents = contents.split("<sup>h</sup>")
            self.ra_hour = contents[0]
            self.ra_min = (contents[1].split("<sup>m</sup>"))[0]
            contents = (contents[1].split("Declination:</td><td>"))[1]
            contents = contents.split("&deg;")
            self.dec_deg = contents[0]
            self.dec_min = (contents[1].split("&#39;"))[0]
            return True
        except:
            return False

    def getCurrentLocation(self):
        location = geocoder.ip("me")
        latitude, longitude = location.latlng
        self.lat_deg = math.floor(latitude)
        self.lat_min = (latitude - self.lat_deg) * 60
        self.long_deg = math.floor(longitude)
        self.long_min = (longitude - self.long_deg) * 60

    def objTest(self):
        # Originally had in compute function, but errored out here, so it got moved for simplicity
        self.dec_deg = int(self.dec_deg)
        self.dec_min = float(self.dec_min)
        self.ra_hour = int(self.ra_hour)
        self.ra_min = float(self.ra_min)

        if (math.isnan(self.dec_deg) or (abs(self.dec_deg) >= 90) or
                math.isnan(self.dec_min) or (self.dec_min < 0) or (self.dec_min >= 60) or
                math.isnan(self.ra_hour) or (self.ra_hour < 0) or (self.ra_hour >= 24) or
                math.isnan(self.ra_min) or (self.ra_min < 0) or (self.ra_min >= 60)):
            print("Invalid object data")
            return False
        else:
            return True

    def locTest(self):
        if (math.isnan(self.lat_deg) or (abs(self.lat_deg) >= 90) or
                math.isnan(self.lat_min) or (self.lat_min < 0) or (self.lat_min >= 60) or
                math.isnan(self.long_deg) or (abs(self.long_deg) >= 180) or
                math.isnan(self.long_min) or (self.long_min < 0) or (self.long_min >= 60)):
            print("Invalid location data")
            return False
        else:
            return True

    # convert right ascension (hours, minutes) to degrees as real
    def ra2real(self):
        self.ra_hour = int(self.ra_hour)
        self.ra_min = float(self.ra_min)
        return 15 * (self.ra_hour + self.ra_min / 60)

    # convert angle (deg, min) to degrees as real
    def dms2real(self, deg, min):
        rv = 0
        if (deg < 0):
            rv = deg - min / 60
        else:
            rv = deg + min / 60
        return rv

    # Compute the Mean Sidereal Time in units of degrees.
    # Use lon := 0 to get the Greenwich MST.
    # East longitudes are positive; West longitudes are negative
    # returns: time in degrees
    def mean_sidereal_time(self, now, long):
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        minute = now.minute
        second = now.second

        if ((month == 1) or (month == 2)):
            year = year - 1
            month = month + 12

        a = math.floor(year / 100)
        b = 2 - a + math.floor(a / 4)
        c = math.floor(365.25 * year)
        d = math.floor(30.6001 * (month + 1))

        # days since J2000.0
        jd = b + c + d - 730550.5 + day + (hour + minute / 60.0 + second / 3600.0) / 24.0

        # julian centuries since J2000.0
        jt = jd / 36525.0

        # the mean sidereal time in degrees
        mst = 280.46061837 + 360.98564736629 * jd + 0.000387933 * jt * jt - jt * jt * jt / 38710000 + long

        # in degrees modulo 360.0
        if (mst > 0.0):
            while (mst > 360.0):
                mst = mst - 360.0
        else:
            while (mst < 0.0):
                mst = mst + 360.0

        return mst

    def coord2horizon(self, utc, ra, dec, lat, long):
        # compute hour angle in degrees
        ha = self.mean_sidereal_time(utc, long) - ra
        if (ha < 0):
            ha = ha + 360

        # convert degrees to radians
        ha = ha * math.pi / 180
        dec = dec * math.pi / 180
        lat = lat * math.pi / 180

        # compute altitude in radians
        sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ha)
        alt = math.asin(sin_alt)

        # compute azimuth in radians
        # divide by zero error at poles or if alt = 90 deg
        cos_az = (math.sin(dec) - math.sin(alt) * math.sin(lat)) / (math.cos(alt) * math.cos(lat))
        az = math.acos(cos_az)

        # convert radians to degrees
        self.altitude = alt * 180 / math.pi
        self.azimuth = az * 180 / math.pi

        # choose hemisphere
        if (math.sin(ha) > 0):
            self.azimuth = 360 - self.azimuth
            return self.altitude, self.azimuth

    def compute(self, obj_input):
        self.getCurrentLocation()
        lat = self.dms2real(self.lat_deg, self.lat_min)
        long = self.dms2real(self.long_deg, self.long_min)
        self.getDeclination(lat, long)

        if obj_input == "None":
            return self.magdec
        else:
            self.object = obj_input
            obj_real = self.getObjectInfo()
            if obj_real is True:
                now = datetime.now(tz=timezone.utc)

                if (self.objTest() is True and self.locTest() is True) and obj_input != "":
                    # not time dependent (ra, dec, lat, or lon)
                    ra = self.ra2real()
                    dec = self.dms2real(self.dec_deg, self.dec_min)
                    self.coord2horizon(now, ra, dec, lat, long)
                else:
                    return False, False, False
            else:
                return False, False, False

            return self.magdec, self.altitude, self.azimuth
