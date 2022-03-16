import subprocess


def get_ipv4_addresses(hostname):
    list_of_addresses = []
    default_dns = "8.8.8.8"
    try:
        result = subprocess.check_output(["nslookup", hostname, default_dns], timeout=2, stderr=subprocess.STDOUT).decode("utf-8")
    except:
        return None

    if "Name" not in result:
        return []

    output_response = result.split("\n\n")[1].split("\n")
    for each_line in output_response:
        if each_line.__contains__("Address"):
            ip_address = each_line.split(" ")[1]
            list_of_addresses.append(ip_address)

    return list_of_addresses



def get_ipv6_addresses(hostname):
    list_of_addresses = []

    default_dns = "208.67.222.222"
    request = "nslookup -type=AAAA " + hostname + " " + default_dns
    try:
        result = subprocess.check_output(request, timeout=3, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
    except:
        result = None

    if result.__contains__("No answer") or "has AAAA" not in result:
        return []

    split = result.split("\n\n")
    for each_split in split:
        if each_split.__contains__("Non-authoritative answer"):
            addresses = each_split.split("\n")[1:]
            for each_address in addresses:
                if "has AAAA" in each_address:
                    ipv6_address = each_address.split(" ")[-1]
                    list_of_addresses.append(ipv6_address)

    return list_of_addresses


def get_ip_information(hostname: str):
    ipv4s = get_ipv4_addresses(hostname)
    ipv6s = get_ipv6_addresses(hostname)
    return ipv4s, ipv6s
