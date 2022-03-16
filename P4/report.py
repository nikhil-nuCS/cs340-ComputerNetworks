import json
import datetime
import os
import sys
import texttable
from collections import Counter


def create_tables(input_filename, output_filename):
    data = read_file_contents(input_filename)
    table_1 = create_report_1(data)
    table_2 = create_report_2(data)
    table_3 = create_report_3(data)
    table_4 = create_report_4(data)
    table_5 = create_report_5(data)

    final_content = "*** Report 1 ***" + "\n" + table_1.draw() + "\n\n" + \
                    "*** Report 2 ***" + "\n" + table_2.draw() + "\n\n" + \
                    "*** Report 3 ***" + "\n" + table_3.draw() + "\n\n" + \
                    "*** Report 4 ***" + "\n" + table_4.draw() + "\n\n" + \
                    "*** Report 5 ***" + "\n" + table_5.draw() + "\n\n"
    write_to_file(final_content, output_filename)


def write_to_file(content, filename):
    with open(filename, "w") as f:
        f.write(content)


def create_report_1(data):
    report_table_1 = texttable.Texttable()

    report_table_1.set_cols_width([
        20, # Name
        15, # Scan time
        17, # IPv4
        25, # IPv6
        13, # Server
        10, # Redirect HTTPS
        7, # HSTS
        10, # Insecure HTTP
        10, # TLS
        20, # Root CA
        30, # RDNS Name
        14, # RTT
        30 # Location
    ])

    table_headers = ["Website Name", "Scan Time", "IPv4", "IPv6", "Server", "Redirect to HTTPS", "HSTS",
                     "Insecure HTTP", "TLS", "Root CA", "RDNS Names", "RTT range", "Locations"
                     ]
    report_table_1.set_cols_align(['c'] * len(table_headers))

    report_table_1.header(table_headers)
    for each_website in data:
        website_details = data[each_website]
        report_table_1.add_row([
            each_website,
            datetime.datetime.utcfromtimestamp(website_details['scan_time']),
            "\n".join(website_details["ipv4_addresses"]),
            "\n".join(website_details["ipv6_addresses"]),
            website_details["http_server"],
            "True" if website_details["redirect_to_https"] else "False",
            "True" if website_details["hsts"] else "False",
            "True" if website_details["insecure_http"] else "False",
            "\n".join(website_details["tls_versions"]),
            website_details["root_ca"],
            None if len(website_details["rdns_names"]) == 0 else "\n".join(website_details["rdns_names"]),
            str(website_details["rtt_range"][0]) + "-" + str(website_details["rtt_range"][1]),
            "\n".join(website_details["geo_locations"])
        ])

    return report_table_1


def create_report_2(data):
    report_table_2 = texttable.Texttable()
    table_headers = ["Website Name", "RTT Range"]
    report_table_2.set_cols_width([20, 14])
    report_table_2.set_cols_align(['c'] * len(table_headers))
    report_table_2.header(table_headers)
    tuples = []
    for each_website in data:
        website_details = data[each_website]
        tuples.append((each_website, website_details["rtt_range"]))
    sorted_rtt = sorted(tuples, key=lambda x: x[1][0])
    for each_entry in sorted_rtt:
        report_table_2.add_row([
            each_entry[0],
            str(each_entry[1][0]) + " - " + str(each_entry[1][1])
        ])
    return report_table_2


def create_report_3(data):
    report_table_3 = texttable.Texttable()
    table_headers = ["Root CA", "Occurrence"]
    report_table_3.set_cols_width([30, 14])
    report_table_3.set_cols_align(['c'] * len(table_headers))
    report_table_3.header(table_headers)
    root_cas = []
    for each_website in data:
        root_cas.append(data[each_website]["root_ca"])
    freq_root_ca = Counter(root_cas).most_common()

    for each_root_ca in freq_root_ca:
        report_table_3.add_row([
            each_root_ca[0],
            each_root_ca[1]
        ])
    return report_table_3


def create_report_4(data):
    report_table_4 = texttable.Texttable()
    table_headers = ["Servers", "Occurrence"]
    report_table_4.set_cols_width([30, 14])
    report_table_4.set_cols_align(['c'] * len(table_headers))
    report_table_4.header(table_headers)
    https_servers = []
    for each_website in data:
        https_servers.append(data[each_website]["http_server"])
    freq_https_servers = Counter(https_servers).most_common()

    for each_server in freq_https_servers:
        report_table_4.add_row([
            each_server[0],
            each_server[1]
        ])
    return report_table_4


def create_report_5(data):
    report_table_5 = texttable.Texttable()
    table_headers = ["TLSv1.0", "TLSv1.1", "TLSv1.2", "TLSv1.3", "SSLv2", "SSLv3",
                     "Plain HTTP", "HTTPS Redirect", "HSTS", "IPv6"]
    report_table_5.set_cols_width([12, 12, 12, 12, 12, 12, 12, 12, 12, 12])
    report_table_5.set_cols_align(['c'] * len(table_headers))
    report_table_5.header(table_headers)
    total_count = len(data)
    tls_versions = []
    plain_http = 0
    redirect_to_https = 0
    hsts = 0
    supports_ipv6 = 0
    for each_website in data:
        tls_versions.extend(data[each_website]["tls_versions"])
        plain_http += 1 if data[each_website]["insecure_http"] else 0
        redirect_to_https += 1 if data[each_website]["redirect_to_https"] else 0
        hsts += 1 if data[each_website]["hsts"] else 0
        supports_ipv6 += 1 if len(data[each_website]["ipv6_addresses"]) else 0

    freq_tls_versions = Counter(tls_versions).most_common()
    tls_dict = dict(freq_tls_versions)

    report_table_5.add_row([
        str(round(tls_dict.get("TLSv1.0", 0) / total_count * 100, 2)) + "%",
        str(round(tls_dict.get("TLSv1.1", 0) / total_count * 100, 2)) + "%",
        str(round(tls_dict.get("TLSv1.2", 0) / total_count * 100, 2)) + "%",
        str(round(tls_dict.get("TLSv1.3", 0) / total_count * 100, 2)) + "%",
        str(round(tls_dict.get("SSLv2", 0) / total_count * 100, 2)) + "%",
        str(round(tls_dict.get("SSLv3", 0) / total_count * 100, 2)) + "%",
        str(round(plain_http / total_count * 100, 2)) + "%",
        str(round(redirect_to_https / total_count * 100, 2)) + "%",
        str(round(hsts / total_count * 100, 2)) + "%",
        str(round(supports_ipv6 / total_count * 100, 2)) + "%"
    ])
    return report_table_5


def read_file_contents(filename):
    path = os.getcwd() + "/" + filename
    file = open(path, "r")
    # Reads the content of the file at the given path
    file_content = json.load(file)
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
    output_txt_name = sys.argv[2]
    if check_argument_correctness(input_file_name):
        create_tables(input_file_name, output_txt_name)
