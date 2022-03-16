import os
import sys
import json
import time

from helper_files.ip_helper import get_ip_information
from helper_files.request_helper import get_server_information
from helper_files.tls_helper import get_tls_info
from helper_files.dns_helper import get_dns_information
from helper_files.rtt_helper import get_rtt_information
from helper_files.geo_helper import load_geo_information
from helper_files.geo_helper import get_geo_information


def start_scan(file_name, output_filename):
    json_dict = {}
    file_content = get_file_content(file_name)
    dbms_reader = load_geo_information()

    for each_website in file_content:
        website_details = {}

        print("\nNetwork Scan : ", each_website)
        scan_time = time.time()

        print("\t | Performing IPv4 and IPv6")
        ipv4s, ipv6s = get_ip_information(each_website)

        print("\t | Retrieving HTTP Server")
        redirect_to_https, insecure_http, http_server, hsts = get_server_information(each_website)

        print("\t | Retrieving TLS versions and CAs")
        tls_versions, root_ca = get_tls_info(each_website)

        print("\t | Retrieving RDNS")
        rdns_names = get_dns_information(ipv4s)

        print("\t | Calculating RTT")
        rtt_range = get_rtt_information(ipv4s)

        print("\t | Searching Geolocation")
        geo_locations = get_geo_information(dbms_reader, ipv4s)

        website_details["scan_time"] = scan_time
        website_details["ipv4_addresses"] = ipv4s
        website_details["ipv6_addresses"] = ipv6s
        website_details["redirect_to_https"] = redirect_to_https
        website_details["http_server"] = http_server
        website_details["hsts"] = hsts
        website_details["insecure_http"] = insecure_http
        website_details["tls_versions"] = tls_versions
        website_details["root_ca"] = root_ca
        website_details["rdns_names"] = rdns_names
        website_details["rtt_range"] = rtt_range
        website_details["geo_locations"] = geo_locations

        json_dict[each_website] = website_details
    dbms_reader.close()
    write_to_file(json_dict, output_filename)


def write_to_file(json_content, output_filename):
    with open(output_filename, "w") as f:
        json.dump(json_content, f, sort_keys=True, indent=4)


def get_file_content(filename):
    path = os.getcwd() + "/" + filename
    file = open(path, "r")
    # Reads the content of the file at the given path
    file_content = file.read().split("\n")
    file.close()
    return file_content

def check_argument_correctness(txt_name):
    curr_dir_path = os.getcwd()
    # Returns the current working directory
    path = curr_dir_path + "/" + txt_name
    if os.path.exists(path):
        return True
    return False


if __name__ == '__main__':
    input_file_name = sys.argv[1]
    output_json_name = sys.argv[2]
    if check_argument_correctness(input_file_name):
        start_scan(input_file_name, output_json_name)
