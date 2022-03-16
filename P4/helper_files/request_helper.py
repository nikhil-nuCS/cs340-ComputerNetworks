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
        try:
            insecure_http = False
            request_https_response = session.get("https://" + hostname, timeout=3)
            redirect_to_https, http_server, hsts = parse_response_and_get_headers(request_response)
        except:
            pass

    return redirect_to_https, insecure_http, http_server, hsts


def parse_response_and_get_headers(request_response):
    redirect_to_https = False
    hsts = False
    http_server = None
    if request_response in range(300, 310, 1):
        return redirect_to_https, http_server, hsts
    else:
        if "https" in request_response.url:
            redirect_to_https = True
        if "Server" in request_response.headers:
            http_server = request_response.headers["Server"]
        if "Strict-Transport-Security" in request_response.headers:
            hsts = True

    return redirect_to_https, http_server, hsts


def get_server_information(hostname):
    curr_session = Session()
    curr_session.max_redirects = 10
    return get_http_response(curr_session, hostname)

