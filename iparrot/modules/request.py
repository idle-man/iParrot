# -*- coding: utf-8 -*-

import json
import requests
from http.cookiejar import CookieJar
from urllib.parse import urlencode

from iparrot.modules.helper import now_timestamp_ms

DEFAULT_TIMEOUT = 5


class HttpRequest(object):
    def __init__(self, session=requests.Session()):
        self.session = session
        self.cookies = {}  # init session cookies, will be used in all requests

    def __del__(self):
        self.session.close()

    def request(self, url, method, params=None, data=None, headers=None, cookies=None, retry=1, timeout=DEFAULT_TIMEOUT):
        # merge with stored cookies
        if isinstance(cookies, CookieJar):
            cookies = requests.utils.dict_from_cookiejar(cookies)
            cookies.update(self.cookies)
        elif isinstance(cookies, dict):
            cookies.update(self.cookies)
        else:
            cookies = self.cookies

        s_time = e_time = 0
        _return = None
        while retry > 0:
            s_time = int(now_timestamp_ms())  # mark request start time
            if method.lower() in ('post', 'put', 'patch'):
                response = self.session.request(
                    url="{}?{}".format(url, urlencode(params)) if params else url,
                    method=method,
                    data=data.encode('utf-8') if isinstance(data, str) else data,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout
                )
            else:
                response = self.session.request(
                    url=url,
                    method=method,
                    params=params.encode('utf-8') if isinstance(params, str) else params,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout)

            e_time = int(now_timestamp_ms())  # mark request end time

            # store response cookies
            if response and response.cookies:
                self.cookies.update(requests.utils.dict_from_cookiejar(response.cookies))

            if response is not None:
                _return = {
                    "result": response.ok,
                    "time": {
                        "start": s_time,
                        "end": e_time,
                        "spent": e_time - s_time
                    },
                    "response": {
                        "status.code": response.status_code,
                        "content": response.text,
                        "headers": dict(response.headers),
                        "cookies": requests.utils.dict_from_cookiejar(response.cookies)
                    },
                    "request": {
                        "method": method,
                        "url": url,
                        "params": params,
                        "data": data,
                        "headers": headers or {},
                        "cookies": cookies or {}
                    }
                }
                if format(response.status_code).startswith('20'):  # success, return
                    return _return
            # fail, retry
            retry -= 1
            e_time = int(now_timestamp_ms())  # default request end time

        if _return is None:  # default return data
            _return = {
                "result": False,
                "time": {
                    "start": s_time,
                    "end": e_time,
                    "spent": e_time - s_time
                },
                "response": {
                    "status.code": "Unknown",
                    "content": "",
                    "headers": {},
                    "cookies": {}
                },
                "request": {
                    "method": method,
                    "url": url,
                    "params": params,
                    "data": data,
                    "headers": headers or {},
                    "cookies": cookies or {}
                }
            }
        return _return

    def close(self):
        self.session.close()


if __name__ == '__main__':
    my_url = 'http://httpbin.org/'
    my_param = {
        'UserId': '083e29e59c0b257813af7cb454b1e0e9',
        'Date': '2019-01-01'}
    my_header = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Token": "w6XCs4YqWnIEbJpDKvQHtMr7OZ8Rjkyl"
    }

    hr = HttpRequest()
    print("http get: " + json.dumps(
        hr.request(url=my_url+'get', method='get', params=my_param, headers=my_header, cookies={'test': '123'}),
        indent=4))
    print("http post: " + json.dumps(
        hr.request(url=my_url+'post', method='post', data=my_param, headers=my_header), indent=4))
    print("http put: " + json.dumps(
        hr.request(url=my_url + 'put', method='put', params=my_param, headers=my_header), indent=4))
    print("http delete: " + json.dumps(
        hr.request(url=my_url + 'delete', method='delete', params=my_param, headers=my_header), indent=4))
    print("http head: " + json.dumps(
        hr.request(url=my_url + 'head', method='head', params=my_param, headers=my_header), indent=4))
