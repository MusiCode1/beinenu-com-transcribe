import urllib.parse


def convert_google_code(code: str):
    parsed_url = urllib.parse.urlparse(code)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    code = query_params["code"][0]

    return code
