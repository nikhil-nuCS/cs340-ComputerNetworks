import maxminddb


def get_info(self, ips: list) -> list:
    locations = []

    for ip in ips:
        location = self.reader.get(ip)
        city = None
        province = None
        country = None

        if "country" in location and "en" in location["country"]["names"]:
            country = location["country"]["names"]["en"]
        elif "registered_country" in location and "en" in location["registered_country"]["names"]:
            country = location["registered_country"]["names"]["en"]
        elif "continent" in location and "en" in location["continent"]["names"]:
            country = location["continent"]["names"]["en"]

        if "subdivisions" in location and len(location["subdivisions"]) > 0 and \
                "en" in location["subdivisions"][0]["names"]:
            province = location["subdivisions"][0]["names"]["en"]

        if "city" in location and "en" in location["city"]["names"]:
            city = location["city"]["names"]["en"]

        location_text = ""

        if city:
            location_text = city
        if province:
            if len(location_text) > 0:
                location_text += ', '
            location_text += province
        if country:
            if len(location_text) > 0:
                location_text += ', '
            location_text += country

        if location_text not in locations:
            locations.append(location_text)

    return locations


def search_database(reader, ip_address):
    location = ""
    dbms_response = reader.get(ip_address)
    if "city" in dbms_response and "en" in dbms_response["city"]["names"]:
        location += dbms_response["city"]["names"]["en"] + ", "
    if "subdivisions" in dbms_response and "en" in dbms_response["subdivisions"][0]["names"]:
        location += dbms_response["subdivisions"][0]["names"]["en"] + ", "
    if "country" in dbms_response and "en" in dbms_response["country"]["names"]:
        location += dbms_response["country"]["names"]["en"]

    return location


def get_geo_information(reader, ip_addresses):
    locations = []
    for each_ip in ip_addresses:
        ip_location = search_database(reader, each_ip)
        if ip_location not in locations:
            locations.append(ip_location)
    return locations


def load_geo_information():
    reader = maxminddb.open_database("GeoLite2-City.mmdb")
    return reader
