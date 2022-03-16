import math
import subprocess


# Function to calculate the RTT
def get_rtt(ip_address, port):
    rtt_cmd = 'sh -c "time echo -e \'\\x1dclose\\x0d\' | telnet ' + ip_address + ' ' + port + '"'
    cmd_response = subprocess.check_output(rtt_cmd, timeout=5, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
    split_response = cmd_response.split("\n\n")
    for each_response in split_response:
        if "real" in each_response:
            cmd_real_time = each_response.split("\n")[0].split("\t")[1].split("m")[1]
            cmd_real_time = float(cmd_real_time[:-1]) * 1000
            return cmd_real_time

    return math.inf


def get_rtt_information(list_of_addresses):
    times = []
    for each_address in list_of_addresses:
        times.append(get_rtt(each_address, "80"))
    minimum = min(times)
    maximum = max(times)

    return [minimum, maximum]
