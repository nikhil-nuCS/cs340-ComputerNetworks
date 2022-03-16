import dns.resolver, dns.reversename

import socket


def run_rdns(ip_address):
    try:
        # Using imported library dnspython to resolve the DNS name
        name = dns.reversename.from_address(ip_address)
        rdns_name = str(dns.resolver.resolve(name, "PTR")[0])
        if rdns_name[-1] == '.':
            rdns_name = rdns_name[:-1]
        return rdns_name
    except:
        pass

def run_socket_rdns(ip_address):
    # Added extra function to check if the values returned are the same.
    # Is not in use.
    name = socket.gethostbyaddr(ip_address)
    return name

def get_dns_information(list_of_addresses):
    rdns = []
    for each_address in list_of_addresses:
        domain_name = run_rdns(each_address)
        # Only inserting unique values of RDNS
        if domain_name not in rdns and domain_name is not None:
            rdns.append(domain_name)
    return rdns
