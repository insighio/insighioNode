import usocket, os, gc
from device_info import wdt_reset

# from here: https://github.com/rdehuyss/micropython-ota-updater/blob/master/app/httpclient.py
CHUNK_SIZE = const(512)  # bytes


class Response:
    def __init__(self, socket, saveToFile=None):
        self._socket = socket
        self._saveToFile = saveToFile
        self._encoding = "utf-8"
        if saveToFile is not None:
            with open(saveToFile, "w") as outfile:
                data = self._socket.read(CHUNK_SIZE)
                while data:
                    print("saving http file, reading chunk: " + str(CHUNK_SIZE))
                    wdt_reset()
                    outfile.write(data)
                    data = self._socket.read(CHUNK_SIZE)
                outfile.close()

            self.close()

    def close(self):
        if self._socket:
            self._socket.close()
            self._socket = None

    @property
    def content(self):
        if self._saveToFile is not None:
            raise SystemError("You cannot get the content from the response as you decided to save it in {}".format(self._saveToFile))

        try:
            result = self._socket.read()
            return result
        finally:
            self.close()

    @property
    def text(self):
        return str(self.content, self._encoding)

    def json(self):
        try:
            import ujson

            result = ujson.load(self._socket)
            return result
        finally:
            self.close()


class HttpClient:
    def __init__(self, headers={}):
        self._headers = headers

    def is_chunked_data(self, data):
        return getattr(data, "__iter__", None) and not getattr(data, "__len__", None)

    def request(self, method, url, data=None, json=None, file=None, custom=None, saveToFile=None, headers={}, stream=None):
        chunked = data and self.is_chunked_data(data)
        redirect = None  # redirection url, None means no redirection

        def _write_headers(sock, _headers):
            headers_cont = b""
            for k in _headers:
                headers_cont += b"{}: {}\r\n".format(k, _headers[k])
            return headers_cont

        try:
            proto, dummy, host, path = url.split("/", 3)
        except ValueError:
            proto, dummy, host = url.split("/", 2)
            path = ""
        if proto == "http:":
            port = 80
        elif proto == "https:":
            try:
                import ussl
            except:
                import ssl as ussl


            port = 443
        else:
            raise ValueError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
        if len(ai) < 1:
            raise ValueError("You are not connected to the internet...")
        ai = ai[0]

        s = usocket.socket(ai[0], ai[1], ai[2])
        try:
            s.connect(ai[-1])
            if proto == "https:":
                gc.collect()
                s = ussl.wrap_socket(s, server_hostname=host)
            content = b""
            # s.write(b'%s /%s HTTP/1.0\r\n' % (method, path))
            content += b"%s /%s HTTP/1.0\r\n" % (method, path)
            if not "Host" in headers:
                # s.write(b'Host: %s\r\n' % host)
                content += b"Host: %s\r\n" % host
            # Iterate over keys to avoid tuple alloc
            content += _write_headers(s, self._headers)
            content += _write_headers(s, headers)

            # add user agent
            content += b"User-Agent: MicroPython Client\r\n"
            if json is not None:
                assert data is None
                import ujson

                data = ujson.dumps(json)
                content += b"Content-Type: application/json\r\n"

            if data:
                if chunked:
                    content += b"Transfer-Encoding: chunked\r\n"
                else:
                    content += b"Content-Length: %d\r\n" % len(data)
            content += b"\r\n"
            if data:
                if chunked:
                    for chunk in data:
                        content += b"%x\r\n" % len(chunk)
                        content += chunk
                        content += b"\r\n"
                    content += "0\r\n\r\n"
                else:
                    content += data
            elif file:
                content += b"Content-Length: %d\r\n" % os.stat(file)[6]
                content += b"\r\n"
                with open(file, "r") as file_object:
                    for line in file_object:
                        content += line + "\n"
            elif custom:
                custom(s)
            else:
                content += b"\r\n"
            s.write(content)

            l = s.readline()
            # print('l: ', l)
            l = l.split(None, 2)
            status = int(l[1])
            reason = ""
            if len(l) > 2:
                reason = l[2].rstrip()
            while 1:
                l = s.readline()
                if not l or l == b"\r\n":
                    break
                # print('l: ', l)
                if l.startswith(b"Transfer-Encoding:"):
                    if b"chunked" in l:
                        raise ValueError("Unsupported " + l)
                elif l.startswith(b"Location:") and not 200 <= status <= 299:
                    if status in [301, 302, 303, 307, 308]:
                        redirect = l[10:-2].decode()
                    else:
                        raise NotImplementedError("Redirect {} not yet supported".format(status))
        except OSError:
            s.close()
            raise

        if redirect:
            s.close()
            if status in [301, 302, 303]:
                return self.request("GET", url=redirect, **kw)
            else:
                return self.request(method, redirect, **kw)
        else:
            resp = Response(s, saveToFile)
            resp.status_code = status
            resp.reason = reason
            return resp

    def head(self, url, **kw):
        return self.request("HEAD", url, **kw)

    def get(self, url, **kw):
        return self.request("GET", url, **kw)

    def post(self, url, **kw):
        return self.request("POST", url, **kw)

    def put(self, url, **kw):
        return self.request("PUT", url, **kw)

    def patch(self, url, **kw):
        return self.request("PATCH", url, **kw)

    def delete(self, url, **kw):
        return self.request("DELETE", url, **kw)
