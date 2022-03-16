import socket
import ssl
import subprocess

# Following implementation at : https://stackoverflow.com/questions/40557031/command-prompt-to-check-tls-version-required-by-a-host

def get_tls_info(hostname):
    # Default values to be returned
    supported_tls = []
    root_ca = None
    try:
        # CMD command checks for all the TLS versions supported by the hostname
        cmd = "nmap --script ssl-enum-ciphers -p 443 " + hostname
        cmd_response = subprocess.check_output(cmd, timeout=10, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
        if "TLSv1.0" in cmd_response:
            supported_tls.append("TLSv1.0")
        if "TLSv1.1" in cmd_response:
            supported_tls.append("TLSv1.1")
        if "TLSv1.2" in cmd_response:
            supported_tls.append("TLSv1.2")
        if "SSLv2" in cmd_response:
            supported_tls.append("SSLv2")
        if "SSLv3" in cmd_response:
            supported_tls.append("SSLv3")
    except Exception as tls_ex:
        pass

    try:
        # CMD command to retrieve the CA information. It also returns if TLSv1.3 is supported
        openssl_cmd = "echo | timeout 7 openssl s_client -connect " + hostname + ":443"
        openssl_cmd_response = subprocess.check_output(openssl_cmd, timeout=7, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
        if "New, TLSv1.3" in openssl_cmd_response:
            supported_tls.append('TLSv1.3')

        splits = openssl_cmd_response.split("---\n")
        for each_split in splits:
            if "Certificate chain" in each_split:
                certificate_chain = each_split
                break

        # Parsing CA root info
        # For info names which have "," in them, the parser needs to be handle them differently
        issuer_info = certificate_chain.rsplit("\n ", 1)
        root_info = issuer_info[1]
        if "O = \"" in root_info:
            o_split = root_info.split("O = ")[1]
            ou_split = o_split.split("\", ")[0]
            root_ca = ou_split[1:]
        else:
            o_split = root_info.split("O = ")[1]
            root_ca = o_split.split(",")[0]
    except Exception as ex:
        print(ex)
        pass

    return supported_tls, root_ca
