from requests import Response, Session


def get_http_response(session, hostname):
    insecure_http = True
    redirect_to_https = False
    hsts = False
    http_server = None
    try:
        request_response = session.get("http://" + hostname, timeout=3)
        redirect_to_https, http_server, hsts = parse_response_and_get_headers(request_response)
    except Exception as exception:
        # If HTTP is not supported, an exception will be thrown and will be handled by running HTTPS
        try:
            insecure_http = False
            request_https_response = session.get("https://" + hostname, timeout=3)
            redirect_to_https, http_server, hsts = parse_response_and_get_headers(request_response)
        except:
            pass

    return redirect_to_https, insecure_http, http_server, hsts


def parse_response_and_get_headers(request_response):
    # Setting default values to return
    redirect_to_https = False
    hsts = False
    http_server = None
    # If 300 to 310 code is received, then HTTPS is not supported
    if request_response in range(300, 310, 1):
        return redirect_to_https, http_server, hsts
    else:
        # If https is present in the queried URL, then HTTPS is True
        if "https" in request_response.url:
            redirect_to_https = True
        # Retrieve the server information
        if "Server" in request_response.headers:
            http_server = request_response.headers["Server"]
        # Retrieve HSTS information
        if "Strict-Transport-Security" in request_response.headers:
            hsts = True

    return redirect_to_https, http_server, hsts


def get_server_information(hostname):
    curr_session = Session()
    # Creating a session which handles maximum redirects parameter
    curr_session.max_redirects = 10
    return get_http_response(curr_session, hostname)

