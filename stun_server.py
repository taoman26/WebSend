"""最小構成のSTUNサーバー（RFC 5389のBinding Requestのみ対応）。

目的はインターネットのSTUN（stun.l.google.comなど）に頼らず、LAN内で完結させること。
一部のブラウザ（Chrome系）はWebRTCのhost candidateにmDNSの匿名ホスト名
（xxxxxxxx-....local）を使うため、mDNS解決に対応していないブラウザ
（Haiku OSのWebPositiveなど）からは実IPアドレスがわからず接続できない。
STUNのBinding Responseで「観測した送信元IP:port」を返すことで、
mDNSに隠されない実IPアドレスのcandidate（srflx）を生成させる。
"""
import asyncio
import socket
import struct

STUN_MAGIC_COOKIE = 0x2112A442
BINDING_REQUEST = 0x0001
BINDING_SUCCESS_RESPONSE = 0x0101
MAPPED_ADDRESS = 0x0001  # RFC 3489（古いSTUNクライアント向けの互換用）
XOR_MAPPED_ADDRESS = 0x0020  # RFC 5389


def build_binding_response(transaction_id: bytes, ip: str, port: int) -> bytes:
    magic_bytes = struct.pack("!I", STUN_MAGIC_COOKIE)
    ip_bytes = socket.inet_aton(ip)

    # XOR-MAPPED-ADDRESS（RFC 5389、モダンなWebRTC実装が読む）
    x_port = port ^ (STUN_MAGIC_COOKIE >> 16)
    x_ip = bytes(a ^ b for a, b in zip(ip_bytes, magic_bytes))
    xor_attr_value = struct.pack("!BBH", 0, 0x01, x_port) + x_ip
    xor_attr = struct.pack("!HH", XOR_MAPPED_ADDRESS, len(xor_attr_value)) + xor_attr_value

    # MAPPED-ADDRESS（RFC 3489、古い/簡易なSTUNクライアント向けの互換用にXORなしでも同梱しておく）
    plain_attr_value = struct.pack("!BBH", 0, 0x01, port) + ip_bytes
    plain_attr = struct.pack("!HH", MAPPED_ADDRESS, len(plain_attr_value)) + plain_attr_value

    attrs = xor_attr + plain_attr
    header = struct.pack("!HHI", BINDING_SUCCESS_RESPONSE, len(attrs), STUN_MAGIC_COOKIE) + transaction_id
    return header + attrs


class StunServerProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        if len(data) < 20:
            return
        msg_type, _msg_len = struct.unpack("!HH", data[0:4])
        magic_cookie = struct.unpack("!I", data[4:8])[0]
        if msg_type != BINDING_REQUEST or magic_cookie != STUN_MAGIC_COOKIE:
            return
        transaction_id = data[8:20]
        ip, port = addr[0], addr[1]
        try:
            response = build_binding_response(transaction_id, ip, port)
        except OSError:
            return  # IPv6等、inet_atonで扱えないアドレスは無視
        self.transport.sendto(response, addr)


async def start_stun_server(host: str = "0.0.0.0", port: int = 3478):
    loop = asyncio.get_running_loop()
    transport, _protocol = await loop.create_datagram_endpoint(
        StunServerProtocol, local_addr=(host, port)
    )
    return transport
