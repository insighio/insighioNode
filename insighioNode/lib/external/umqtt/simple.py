# original version: https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.simple
# used modules from : https://github.com/peterhinch/micropython-mqtt/blob/65ccbaa8eb486a0454faadffec4cf846c8e259dd/mqtt_as/mqtt_as.py

import usocket as socket
import ustruct as struct
from ubinascii import hexlify
import _thread
import utime
from uerrno import EINPROGRESS, ETIMEDOUT
from micropython import const
import asyncio

# Default short delay for good SynCom throughput (avoid sleep(0) with SynCom).
_DEFAULT_MS = const(20)
_SOCKET_POLL_DELAY = const(5)  # 100ms added greatly to publish latency
BUSY_ERRORS = [EINPROGRESS, ETIMEDOUT, 118, 119]


class MQTTClient:
    def __init__(
        self,
        client_id,
        server,
        port=0,
        user=None,
        password=None,
        keepalive=0,
        ssl=False,
        ssl_params={},
    ):
        if port == 0:
            port = 8883 if ssl else 1883
        self.client_id = client_id
        self.sock = None
        self.server = server
        self.port = port
        self.ssl = ssl
        self.ssl_params = ssl_params
        self.pid = 0
        self.cb = None
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False
        self.lock = _thread.allocate_lock()
        self.last_rx = utime.ticks_ms()

    def _timeout(self, t):
        return utime.ticks_diff(utime.ticks_ms(), t) > 10000

    async def _write(self, bytes_wr, length=0, sock=None):
        if sock is None:
            sock = self.sock
        # Wrap bytes in memoryview to avoid copying during slicing
        bytes_wr = memoryview(bytes_wr)
        if length:
            bytes_wr = bytes_wr[:length]
        t = utime.ticks_ms()
        while bytes_wr:
            if self._timeout(t):  # or not self.isconnected():
                return False
            try:
                n = sock.write(bytes_wr)
            except OSError as e:  # ESP32 issues weird 119 errors here
                n = 0
                if e.args[0] not in BUSY_ERRORS:
                    raise
            if n:
                t = utime.ticks_ms()
                bytes_wr = bytes_wr[n:]
            await asyncio.sleep_ms(_SOCKET_POLL_DELAY)
        return True

    async def _read(self, n, sock=None):  # OSError caught by superclass
        if sock is None:
            sock = self.sock
        # Declare a byte array of size n. That space is needed anyway, better
        # to just 'allocate' it in one go instead of appending to an
        # existing object, this prevents reallocation and fragmentation.
        data = bytearray(n)
        buffer = memoryview(data)
        size = 0
        t = utime.ticks_ms()
        while size < n:
            if self._timeout(t):  # or not self.isconnected():
                return None
            try:
                msg = sock.read(n - size)
            except OSError as e:  # ESP32 issues weird 119 errors here
                msg = None
                if e.args[0] not in BUSY_ERRORS:
                    raise
            if msg == b"":  # Connection closed by host
                raise OSError(-1, "Connection closed by host")
            if msg is not None:  # data received
                msg_size = len(msg)
                buffer[size : size + msg_size] = msg
                size += msg_size
                t = utime.ticks_ms()
                self.last_rx = utime.ticks_ms()
            await asyncio.sleep_ms(_SOCKET_POLL_DELAY)
        return data

    async def _send_str(self, s):
        await self._write(struct.pack("!H", len(s)))
        await self._write(s)

    async def _recv_len(self):
        n = 0
        sh = 0
        while 1:
            b = (await self._read(1))[0]
            n |= (b & 0x7F) << sh
            if not b & 0x80:
                return n
            sh += 7

    def set_callback(self, f):
        self.cb = f

    def set_last_will(self, topic, msg, retain=False, qos=0):
        assert 0 <= qos <= 2
        assert topic
        self.lw_topic = topic
        self.lw_msg = msg
        self.lw_qos = qos
        self.lw_retain = retain

    async def connect(self, clean_session=True):
        self.sock = socket.socket()
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock.connect(addr)
        if self.ssl:
            import ussl

            self.sock = ussl.wrap_socket(self.sock, **self.ssl_params)
        premsg = bytearray(b"\x10\0\0\0\0\0")
        msg = bytearray(b"\x04MQTT\x04\0\0\0")  # Protocol 3.1.1

        sz = 10 + 2 + len(self.client_id)
        msg[6] = clean_session << 1
        if self.user is not None:
            sz += 2 + len(self.user) + 2 + len(self.pswd)
            msg[6] |= 0xC0
        if self.keepalive:
            assert self.keepalive < 65536
            msg[7] |= self.keepalive >> 8
            msg[8] |= self.keepalive & 0x00FF
        if self.lw_topic:
            sz += 2 + len(self.lw_topic) + 2 + len(self.lw_msg)
            msg[6] |= 0x4 | (self.lw_qos & 0x1) << 3 | (self.lw_qos & 0x2) << 3
            msg[6] |= self.lw_retain << 5

        i = 1
        while sz > 0x7F:
            premsg[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz

        await self._write(premsg, i + 2)
        await self._write(msg)
        # print(hex(len(msg)), hexlify(msg, ":"))
        await self._send_str(self.client_id)
        if self.lw_topic:
            await self._send_str(self.lw_topic)
            await self._send_str(self.lw_msg)
        if self.user is not None:
            await self._send_str(self.user)
            await self._send_str(self.pswd)
        resp = await self._read(4)
        if resp[3] != 0 or resp[0] != 0x20 or resp[1] != 0x02:
            raise OSError(-1, "Bad CONNACK")  # Bad CONNACK e.g. authentication fail.

    async def disconnect(self):
        if self.sock is not None:
            try:
                with self.lock:
                    await self._write(b"\xe0\0")
                    await asyncio.sleep_ms(100)
            except OSError:
                pass
            self.close()

    def close(self):
        if self.sock is not None:
            self.sock.close()

    async def ping(self):
        with self.lock:
            await self._write(b"\xc0\0")
        await self.wait_msg()

    async def publish(self, topic, msg, retain=False, qos=0):
        with self.lock:
            pkt = bytearray(b"\x30\0\0\0")
            pkt[0] |= qos << 1 | retain
            sz = 2 + len(topic) + len(msg)
            if qos > 0:
                sz += 2
            assert sz < 2097152
            i = 1
            while sz > 0x7F:
                pkt[i] = (sz & 0x7F) | 0x80
                sz >>= 7
                i += 1
            pkt[i] = sz
            # print(hex(len(pkt)), hexlify(pkt, ":"))
            await self._write(pkt, i + 1)
            await self._send_str(topic)
            if qos > 0:
                self.pid += 1
                pid = self.pid
                struct.pack_into("!H", pkt, 0, pid)
                await self._write(pkt, 2)
            await self._write(msg)
        if qos == 1:
            while 1:
                op = await self.wait_msg()
                if op == 0x40:
                    sz = await self._read(1)
                    if sz != b"\x02":
                        raise OSError(-1, "Invalid PUBACK packet")
                    rcv_pid = await self._read(2)
                    rcv_pid = rcv_pid[0] << 8 | rcv_pid[1]
                    if pid == rcv_pid:
                        return
        elif qos == 2:
            raise OSError(-1, "Invalid qos")

    async def subscribe(self, topic, qos=0):
        assert self.cb is not None, "Subscribe callback is not set"
        with self.lock:
            pkt = bytearray(b"\x82\0\0\0")
            self.pid += 1
            struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self.pid)
            # print(hex(len(pkt)), hexlify(pkt, ":"))
            await self._write(pkt)
            await self._send_str(topic)
            await self._write(qos.to_bytes(1, "little"))
        while 1:
            op = await self.wait_msg()
            if op == 0x90:  # SUBACK
                resp = await self._read(4)
                # print(resp)
                if resp[1] != pkt[2] or resp[2] != pkt[3]:
                    raise OSError(-1, "Invalid pid in SUBACK packet")
                elif resp[3] == 0x80:
                    raise OSError(-1, "Invalid SUBACK packet")
                return

    # Wait for a single incoming MQTT message and process it.
    # Subscribed messages are delivered to a callback previously
    # set by .set_callback() method. Other (internal) MQTT
    # messages processed internally.
    async def wait_msg(self):
        with self.lock:
            try:
                res = await self._read(1)
            except OSError as e:
                raise
            self.sock.setblocking(True)
            if res is None:
                return None
            if res == b"":
                raise OSError(-1)
            if res == b"\xd0":  # PINGRESP
                await self._read(1)
                return None

            op = res[0]
            if op & 0xF0 != 0x30:
                return op
            sz = await self._recv_len()
            topic_len = await self._read(2)
            topic_len = (topic_len[0] << 8) | topic_len[1]
            topic = await self._read(topic_len)
            sz -= topic_len + 2
            if op & 6:
                pid = await self._read(2)
                pid = pid[0] << 8 | pid[1]
                sz -= 2
            msg = await self._read(sz)
            self.cb(topic, msg)
            if op & 6 == 2:
                pkt = bytearray(b"\x40\x02\0\0")
                struct.pack_into("!H", pkt, 2, pid)
                await self._write(pkt)
            elif op & 6 == 4:
                assert 0

    # Checks whether a pending message from server is available.
    # If not, returns immediately with None. Otherwise, does
    # the same processing as wait_msg.
    async def check_msg(self):
        self.sock.setblocking(False)
        return await self.wait_msg()
