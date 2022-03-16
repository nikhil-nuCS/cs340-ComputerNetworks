import maxminddb


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
        # Only adding unique locations
        if ip_location not in locations:
            locations.append(ip_location)
    return locations


def load_geo_information():
    # Loading the DB once and returning to main program
    reader = maxminddb.open_database("GeoLite2-City.mmdb")
    return reader
