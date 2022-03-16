import math
import subprocess


# Function to calculate the RTT
def get_rtt(ip_address, port):
    try:
        # Following command provided in the instruction and adding a timeout to handle corner cases
        rtt_cmd = 'sh -c "time echo -e \'\\x1dclose\\x0d\' |timeout 2 telnet ' + ip_address + ' ' + port + '"'
        cmd_response = subprocess.check_output(rtt_cmd, timeout=2, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
        split_response = cmd_response.split("\n\n")
        for each_response in split_response:
            if "real" in each_response:
                cmd_real_time = each_response.split("\n")[0].split("\t")[1].split("m")[1]
                # Multiplying it by 1000 to convert the time to ms
                cmd_real_time = float(cmd_real_time[:-1]) * 1000
                return cmd_real_time

        return math.inf
    except Exception as ex:
        # If last possible port is tried and still no result is parsed, return None
        if port == "22":
            return None
        else:
            # If queried port 443 fails, try with port 80
            if port == "443":
                return get_rtt(ip_address,"80")
            # If queried port 80 fails, try with port 22
            elif port == "80":
                return get_rtt(ip_address,"22")


def get_rtt_information(list_of_addresses):
    times = []
    for each_address in list_of_addresses:
        rtt = get_rtt(each_address,"443")
        # If returned rtt is None, skip the value
        if rtt is not None:
            times.append(rtt)

    if len(times) > 0:
        # Find the minimum and maximum RTT values
        # For only 1 IP address, max = min
        minimum = min(times)
        maximum = max(times)
        return [minimum, maximum]
    # If no RTT is found, return None
    else:
        return None
