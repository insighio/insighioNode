import socket
import logging


def udp_send(remote_host, remote_port, msg):
    """ Send UDP packet to remote host/port
            Returns ....
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.sendto(msg, (remote_host, remote_port))
    s.close()
    logging.debug('Data sent...exiting')
