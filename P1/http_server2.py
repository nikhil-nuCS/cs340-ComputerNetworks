import sys
import socket
import os
import select
import datetime  # Importing datetime to get UTC time to send in response according to developer.mozilla.org

conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def start_server(port_number: int):
    """
    :param port_number: Port number on which server is listening for requests
    :return: None
    Starts the server to listen on port number passed to the program.
    Followed the implementation found at https://pymotw.com/3/select/.
    """
    check_port_validity(port_number)
    conn_socket.setblocking(False)
    # Creates a non-blocking socket
    conn_socket.bind(("", port_number))
    conn_socket.listen(5)
    # Specifies the number of unaccepted connections before new connections are refused
    print("Server listening at port = ", port_number)

    inputs = [conn_socket]
    # Sockets to be read from
    outputs = []
    # Sockets to write to

    while inputs:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)

        for each_readable in readable:
            if each_readable is conn_socket:
                # Readable socket is the same socket listening to connections
                client_socket, client_address = each_readable.accept()
                client_socket.setblocking(True)
                inputs.append(client_socket)
                print("Connection established with client with address = ", client_address)
            else:
                client_request = accept_message_from_client(each_readable)
                client_response = parse_client_request(client_request)
                each_readable.sendall(client_response.encode("UTF-8"))
                inputs.remove(each_readable)
                each_readable.close()

        for each_exception in exceptional:
            print('Exception condition on', each_exception.getpeername(), file=sys.stderr)
            # Stop listening for input on the connection
            inputs.remove(each_exception)
            each_exception.close()


def accept_message_from_client(client_socket):
    """
    :param client_socket: "Connection socket"
    :return: Decoded HTTP request
    Decodes the HTTP request from the "connection socket".
    """
    output = ""
    while True:
        message = client_socket.recv(4096)
        if message is not None:
            output += message.decode("UTF-8")
            if output.endswith("\r\n\r\n"):
                # Request should end with the sequence of characters as found on Wireshark
                break
        else:
            break
    return output


def parse_client_request(client_request):
    """
    :param client_request: Decoded HTTP request
    :return: Response for requested file
    Parses the HTTP request and checks that the the request uses the 'GET' method.
    Filters the requested file from the request.
    """
    arr_request = client_request.split("\r\n")
    # Splits the HTTP request by line
    request_header = arr_request[0]
    request_text = request_header.split(" ")
    # Splits the first line of the HTTP request

    if request_text[0] != "GET":
        sys.stderr.write("Unsupported request. Only GET allowed")
        sys.exit(7)

    if request_text[2].startswith("HTTPS"):
        sys.stderr.write("HTTPS not supported")
        sys.exit(7)

    requested_file_name = request_text[1]
    request_response = get_response_for_requested_file(requested_file_name)
    return request_response


def create_response(status_code, phrase, content):
    """
    :param status_code: Status code
    :param phrase: Corresponding response message of status code
    :param content: File content of requested file
    :return: Response for requested file
    Creates a HTTP response displaying the header and content.
    Only displays header if status code is greater than or equal to 400.
    """
    response = "HTTP/1.1 " + str(status_code) + " " + phrase + "\r\n"

    if status_code >= 400:
        # Creating response according to HTTP response code found on developer.mozilla.org
        response += "Connection: close\r\n" + \
                    "Date: " + datetime.date.strftime(datetime.datetime.utcnow(),
                                                      "%a, %d %b %Y %H:%M:%S") + " GMT\r\n\r\n"
        return response
    else:
        response += "Content-Length: " + str(len(content)) + "\r\n" \
                                                             "Connection: close\r\n" + \
                    "Content-Type: text/html; charset=UTF-8\r\n" + \
                    "Date: " + datetime.date.strftime(datetime.datetime.utcnow(),
                                                      "%a, %d %b %Y %H:%M:%S") + " GMT\r\n\r\n" + \
                    content
        return response


def get_response_for_requested_file(requested_file):
    """
    :param requested_file: Requested file
    :return: Response for requested file
    Checks if the requested file exists in the current directory.
    Determines which status code should be shown in the HTTP response.
    """
    requested_file = requested_file[1:]
    print("File name = ", requested_file)
    split_file_name = requested_file.split(".")

    file_name = split_file_name[0]
    extension = split_file_name[-1]

    curr_dir_path = os.getcwd()
    # Returns the current working directory
    path = curr_dir_path + "/" + requested_file

    if os.path.exists(path):
        print("File Exists")
        if extension != "html" and extension != "htm":
            # If the file exists but does not end with ".htm" or ".html", a 403 error response is sent
            print("403 Forbidden")
            response = create_response(403, "Forbidden", None)
            return response
        file = open(path, "r")
        file_content = file.read()
        # Reads the content of the file at the given path
        file.close()
        response = create_response(200, "OK", file_content)
        return response
    else:
        print("404 Not Found")
        response = create_response(404, "Not Found", None)
        return response


def check_port_validity(port: int):
    """
    :param port: Port number entered
    :return: None
    Checks if the port number is within bounds.
    If the port number is less than 1024 or greater than 65535 the program would exit with a non-zero code.
    """
    if port < 1024:
        sys.stderr.write("Port entered is reserved. Please choose a port between 1024 and 65535")
        sys.exit(7)

    elif port > 65535:
        sys.stderr.write("Port entered is out of range. Please choose a port between 1024 and 65535")
        sys.exit(7)


def check_argument_format(args: list):
    """
    :param args: List of arguments passed during program execution
    :return: None
    Checks the number of arguments passed to the program.
    If more or less than 2 parameters are passed the program would exit with a non-zero code.
    """
    if len(args) != 2:
        sys.stderr.write("Enter in format: python3 http_server2.py [port]")
        sys.exit(7)


if __name__ == '__main__':
    args = sys.argv
    check_argument_format(args)
    entered_port = int(args[1])
    start_server(entered_port)
