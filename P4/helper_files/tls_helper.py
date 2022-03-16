import socket
import ssl
import subprocess

# https://stackoverflow.com/questions/40557031/command-prompt-to-check-tls-version-required-by-a-host

def get_tls_info(hostname):
    supported_tls = []
    root_ca = None
    try:
        cmd = "nmap --script ssl-enum-ciphers -p 443 " + hostname
        cmd_response = subprocess.check_output(cmd, timeout=7, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
        if "TLSv1.0" in cmd_response:
            supported_tls.append("TLSv1.0")
        if "TLSv1.1" in cmd_response:
            supported_tls.append("TLSv1.1")
        if "TLSv1.2" in cmd_response:
            supported_tls.append("TLSv1.2")

        openssl_cmd = "echo | openssl s_client -connect " + hostname + ":443"
        openssl_cmd_response = subprocess.check_output(openssl_cmd, timeout=7, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
        if 'New, TLSv1.3, Cipher' in openssl_cmd_response:
            supported_tls.append('TLSv1.3')

        # if "C = US" in openssl_cmd_response:
        #     print("Found US")

        max_depth = openssl_cmd_response.split("\n")[0]
        s = max_depth.split("OU = ")
        y = s[0].split("O =")
        split = max_depth.split(",")
        for each_split in split:
            if "O = " in each_split:
                root_ca = each_split.split("O = ")[1]
                break
    except:
        pass

    return supported_tls, root_ca
