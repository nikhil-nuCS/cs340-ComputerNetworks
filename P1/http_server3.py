import sys
import socket
import json
import datetime

conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def start_server(port_number: int):
    """
    :param port_number: Port number on which server is listening for requests
    :return: None
    Starts the server to listen on port number passed to the program.
    """
    check_port_validity(port_number)
    conn_socket.bind(("", port_number))
    conn_socket.listen()
    print("Server listening at port = ", port_number)
    receive_request(conn_socket)


def receive_request(conn_socket):
    """
    :param conn_socket: "Accept socket"
    :return: None
    Repeatedly accepts a new connection on the "accept socket", reads the HTTP request, and writes a HTTP response to the connection socket.
    """
    while True:
        client_socket, client_address = conn_socket.accept()
        print("Connection established with client with address = ", client_address)
        client_request = accept_message_from_client(client_socket)
        client_response = parse_client_request(client_request)
        client_socket.sendall(client_response.encode("UTF-8"))
        client_socket.close()


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
        elif not message or message.endswith("\r\n\r\n"):
            print(output)
            break
        return output


def parse_client_request(client_request):
    """
    :param client_request: Decoded HTTP request
    :return: Calculated query result
    Parses the HTTP request and checks that the the request uses the 'GET' method.
    Filters the query parameters from the request.
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

    query_part = request_text[1]
    api_result = calculate_query_result(query_part)
    return api_result


def create_response(status_code, phrase, content):
    """
    :param status_code: Status code
    :param phrase: Corresponding response message of status code
    :param content: JSON object containing query parameters and result
    :return: Response for requested URL
    Creates a HTTP response displaying the header and content if status code is less than 400.
    """
    response = "HTTP/1.1 " + str(status_code) + " " + phrase + "\r\n"

    if status_code < 400:
        # Creating response according to HTTP response code found on developer.mozilla.org
        response += "Content-Length: " + str(len(content)) + "\r\n" + \
                    "Connection: close\r\n" + \
                    "Content-Type: application/json; charset=UTF-8\r\n" + \
                    "Date: " + datetime.date.strftime(datetime.datetime.utcnow(),
                                                      "%a, %d %b %Y %H:%M:%S") + " GMT\r\n\r\n" + \
                    content
    return response


def calculate_query_result(query_parameters):
    """
    :param status_code: Query parameters from URL entered
    :return: Response for requested URL
    Determines which status code should be shown in the HTTP response.
    Calculates the result from multiplying query parameters.
    Creates a JSON object containing query parameters and result.
    """
    params = query_parameters.split("?")
    if params[0] != "/product":
        # Returns a 404 error response if a URL other than "/product" is requested
        print("404 Not Found")
        response = create_response(404, "Not Found", None)
        return response

    if len(params) == 1 or params[1] == "":
        # Returns a 400 error response if there are no parameters given
        print("400 Bad Request")
        response = create_response(400, "Bad Request", None)
        return response

    query_params = params[1]
    individual_params = query_params.split("&")
    # Splits the given parameters
    ans = 1.0
    variable_values = []
    for each_param in individual_params:
        queried_variable = each_param.split("=")
        variable_name = queried_variable[0]
        variable_value = queried_variable[1]
        try:
            # Checks for float or int as per https://www.programiz.com/python-programming/examples/check-string-number
            value = float(variable_value)
            variable_values.append(value)
            ans *= value

        except ValueError:
            # Returns a 400 error response if a given parameter is not a number
            print("400 Bad Request")
            response = create_response(400, "Bad Request", None)
            return response

    # Checks if the result is infinity or negative infinity
    if ans == float("inf"):
        ans = "inf"
    elif ans == float("-inf"):
        ans = "-inf"

    json_content = json.dumps(
        {
            "operation": "product",
            "operands": variable_values,
            "result": ans
        },
        sort_keys=False, indent=4)
    # Followed JSON implementation from https://stackoverflow.com/questions/52893297/how-to-write-the-response-in-a-file-with-json-format-using-python
    # and https://pynative.com/python-json-dumps-and-dump-for-json-encoding/
    response_content = create_response(200, "OK", json_content)
    return response_content


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
        sys.stderr.write("Enter in format: python3 http_server3.py [port]")
        sys.exit(7)


if __name__ == '__main__':
    args = sys.argv
    check_argument_format(args)
    entered_port = int(args[1])
    start_server(entered_port)
