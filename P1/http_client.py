import sys
import socket

recursion_count = 0


def perform_http_get(queried_url: str):
    """
    :param queried_url: URL entered as an argument to the program
    :return: None
    Performs HTTP GET request if the maximum recursion limit is not exceeded.
    """
    if recursion_count >= 10:
        sys.stderr.write("Maximum number of redirects exceeded\n")
        sys.exit(7)

    check_url_correctness(queried_url)
    get_http_get_response(queried_url)


def check_argument_correctness(args: list):
    """
    :param args: List of arguments passed during program execution
    :return: None
    Checks the number of arguments passed to the program.
    If more or less than 2 parameters are passed the program would exit with a non-zero code.
    """
    if len(args) != 2:
        sys.stderr.write("Enter in format: python3 http_client.py http://<url>\n")
        sys.exit(7)


def check_url_correctness(url: str):
    """
    :param url: URL entered
    :return: None
    Checks correctness on the URL entered for the program.
    If the URL entered follows an HTTPS protocol or any unsupported protocol, program exits with a non-zero code.
    """
    if url[0:8] == "https://":
        sys.stderr.write("HTTPS not supported\n")
        sys.exit(7)

    if url[0:7] != "http://":
        sys.stderr.write("Enter in format: python3 http_client.py http://<url>/<path>\n")
        sys.exit(7)


def get_http_get_response(url: str):
    """
    :param url: URL entered
    :return: None
    Creates a socket to connect to the server to query the requested URL.
    Parses the URL to split and create a valid HTTP request message to be sent.
    """
    url = url[7:]
    splitted_url = url.split("/")
    url_host = splitted_url[0]
    port = 80
    if url_host.find(":") != -1:
        # Check to see if a port number is passed in the URL
        port_index = url.find(":")
        port = url_host[port_index + 1:]
        port = int(port)
        host_name = url_host[0:port_index]
    else:
        host_name = url_host

    path_addr_index = url.find("/")
    if path_addr_index != -1:
        # Check to see if the URL contains a path name
        path = "/" + url[path_addr_index + 1:]
    else:
        path = "/"

    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Creates a socket via which communication takes place.
    # Following the python socket programming documentation found online
    conn_socket.connect((host_name, port))

    client_data = "GET " + path + " HTTP/1.0\r\nHost: " + host_name + "\r\n\r\n"
    conn_socket.sendall(client_data.encode())
    message = receive_socket_data(conn_socket)
    conn_socket.close()
    # Closing the socket connection once the response has been received
    parse_http_response(message)


def parse_http_response(response: str):
    """
    :param response: Response received from the server
    :return: None
    Performs parsing of the response received from the server.
    Handles different status codes.
    Performs redirection upon receiving 301 or 302 code.
    """
    arr = response.split("\r\n\r\n")
    # Response ends with the sequence of characters as found on Wireshark
    http_headers = arr[0]
    http_response_content = arr[1]
    http_fields = http_headers.split("\r\n")
    http_response_message = http_fields[0]
    http_fields = http_fields[1:]
    http_fields_dict = {}
    for field in http_fields:
        # Creating a dictionary storing the HTTP response headers and their values
        key, value = field.split(":", 1)
        http_fields_dict[key] = value

    if "text/html" not in http_fields_dict["Content-Type"]:
        sys.stderr.write("Content type is not text/html\n")
        sys.exit(7)

    http_version = http_response_message[:8]
    status_message = http_response_message[9:]
    status_code = int(status_message.split(" ")[0])
    phrase = " ".join(status_message.split(" ")[1:])
    # Extracting the status code and phrase

    if status_code >= 400:
        content = get_body_content(http_response_content)
        sys.stderr.write("Encountered " + str(status_code) + "\n")
        sys.stdout.write(content + "\n")
        sys.exit(7)

    elif status_code >= 300:
        if "Location" in http_fields_dict:
            new_url = http_fields_dict["Location"]
            sys.stderr.write("Redirected to: " + new_url)
            if status_code == 301:
                sys.stderr.write("\n" + str(status_code) + " Resource Moved Permanently\n")
            elif status_code == 302:
                sys.stderr.write("\n" + str(status_code) + " Resource Temporarily Moved\n")
            global recursion_count
            recursion_count += 1
            new_url = new_url.strip()
            perform_http_get(new_url)

    elif status_code >= 200:
        body_content = get_body_content(http_response_content)
        sys.stdout.write(body_content + "\n")
        sys.exit(0)


def get_body_content(html_content: str):
    """
    :param html_content: HTTP response content received from the server
    :return: HTML content with tags
    Filters the HTML content from the response.
    """
    body_index_start = html_content.find("<!DOCTYPE html")
    if body_index_start == -1:
        body_index_start = html_content.find("<!doctype html")
    if body_index_start == -1:
        body_index_start = html_content.find("<html")
    body_index_end = html_content.find("</html>")
    body_content = html_content[body_index_start:body_index_end + 7]
    return body_content


def receive_socket_data(conn_socket):
    """
    :param conn_socket: Socket connection created to perform communication with server
    :return: Response returned by the server
    Receives the response from the server until the message content is fully received on the socket.
    """
    server_response = ""
    while True:
        message = conn_socket.recv(4096)
        if len(message) == 0:
            break
        server_response += message.decode("utf-8", "ignore")
    return server_response


if __name__ == '__main__':
    requested_url = sys.argv
    check_argument_correctness(requested_url)
    perform_http_get(requested_url[1])
