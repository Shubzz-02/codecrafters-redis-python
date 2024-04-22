import base64
import socket
import time

from app.utils.RedisProtocolParser import parse_protocol
from app.CustomDictionary import TTLDictionary
from app.utils.RESPMessageBuilder import resp_builder
from threading import Thread
import sys
import random
import string


class ServerConfig:
    def __init__(self):
        self.port_number = 6379
        self.replica = 'master'
        self.master_replid = self.generate_random_string(40)
        self.master_repl_offset = 0
        self.master_host = 'localhost'
        self.master_port = 6379
        self.slave_hosts = {}

    @staticmethod
    def generate_random_string(length):
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string

    # implement to string function
    def __str__(self):
        return f'port_number:{self.port_number}\nreplica:{self.replica}\nmaster_replid:{self.master_replid}\nmaster_repl_offset:{self.master_repl_offset}\nmaster_host:{self.master_host}\nmaster_port:{self.master_port}\nslave_hosts:{self.slave_hosts}'


expiration_dictionary = TTLDictionary()
config = ServerConfig()


def main(server_config):
    server_socket = socket.create_server(("localhost", server_config.port_number), reuse_port=True)
    if server_config.replica == 'slave':
        connect_to_master_server(server_config)
    while True:
        client_sock = server_socket.accept()[0]
        thread = Thread(target=handle_client, args=(client_sock, server_config))
        thread.start()


# create a function to connect to a specified server ip and port using socket.create_connection() and receive the
# response and print
def connect_to_master_server(server_config):
    master_socket = socket.create_connection((server_config.master_host, server_config.master_port))
    master_socket.sendall(f'*1\r\n$4\r\nping\r\n'.encode("utf-8"))
    response = master_socket.recv(1024).decode("utf-8")
    if response != '+PONG\r\n':
        print('Master server is not responding')
        exit(1)
    else:
        print('Successfully connected to master server')
        master_socket.sendall(
            f'*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n${len(str(server_config.port_number))}\r\n{server_config.port_number}\r\n'
            .encode("utf-8"))
        response = master_socket.recv(1024).decode("utf-8")
        master_socket.sendall(f'*3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n'.encode("utf-8"))
        response = master_socket.recv(1024).decode("utf-8")
        master_socket.sendall("*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n".encode("utf-8"))
        response = master_socket.recv(1024).decode("utf-8")
    # master_socket.sendall(f'REPLCONF capa psync2\r\n'.encode("utf-8"))
    # master_socket.sendall(f'PSYNC {server_config.master_replid} {server_config.master_repl_offset}\r\n'.encode("utf-8"))
    # response = master_socket.recv(1024).decode("utf-8")
    # if response.startswith('+FULLRESYNC'):
    #     response = response.split('\r\n')
    #     server_config.master_replid = response[1]
    #     server_config.master_repl_offset = int(response[2])
    # master_socket.close()


def handle_client(client_sock, server_config):
    while True:
        data = client_sock.recv(1024).decode("utf-8")
        if not data:
            continue
        parsed_data, remaining_data = parse_protocol(data)
        process_command(parsed_data, server_config, client_sock)
        # client_sock.sendall(response.encode("utf-8"))


def process_command(parsed_data, server_config, client_sock):
    command = parsed_data[0].lower()
    if command == 'ping':
        client_sock.sendall(resp_builder('+', 'PONG').encode("utf-8"))
    elif command == 'echo':
        client_sock.sendall(resp_builder('$', parsed_data[1]).encode("utf-8"))
    elif command == 'set':
        client_sock.sendall(handle_set_command(parsed_data).encode("utf-8"))
    elif command == 'get':
        client_sock.sendall(handle_get_command(parsed_data).encode("utf-8"))
    elif command == 'info':
        client_sock.sendall(handle_info_command(server_config).encode("utf-8"))
    elif command == 'replconf':
        client_sock.sendall(handle_replica_command(parsed_data, server_config, client_sock).encode("utf-8"))
    elif command == 'psync':
        # client_sock.sendall(handle_psync_command(parsed_data, server_config).encode("utf-8"))
        # time.sleep(3)
        client_sock.sendall(send_rdb_file().encode("utf-8"))
    else:
        return resp_builder('+', 'skip')


def handle_psync_command(parsed_data, server_config):
    if parsed_data[1] == '?':
        return resp_builder('+',
                            f'FULLRESYNC {server_config.master_replid} {server_config.master_repl_offset}')
    else:
        return resp_builder('+', 'skip')


def send_rdb_file():
    rdb_file = base64.b64decode(
        "UkVESVMwMDEx+glyZWRpcy12ZXIFNy4yLjD6CnJlZGlzLWJpdHPAQPoFY3RpbWXCbQi8ZfoIdXNlZC1tZW3CsMQQAPoIYW9mLWJhc2XAAP/wbjv+wP9aog=="
    )
    return resp_builder('$', rdb_file).removesuffix('\r\n')


def handle_replica_command(parsed_data, server_config, client_sock):
    if parsed_data[1] == 'listening-port':
        server_config.slave_hosts[client_sock.getpeername()[0]] = parsed_data[2]
        print(server_config)
        return resp_builder('+', 'OK')
    elif parsed_data[1] == 'capa':
        return resp_builder('+', 'OK')
    elif parsed_data[1] == 'eof':
        return resp_builder('+', 'OK')
    elif parsed_data[1] == 'psync':
        return resp_builder('+', 'OK')
    elif parsed_data[1] == 'ack':
        return resp_builder('+', 'OK')
    elif parsed_data[1] == 'getack':
        return resp_builder('+', 'OK')
    else:
        return resp_builder('+', 'skip')


def handle_set_command(parsed_data):
    arr_len = len(parsed_data)
    if arr_len == 3:
        expiration_dictionary.set(parsed_data[1], parsed_data[2], None)
        return resp_builder('+', 'OK')
    elif arr_len == 5:
        expiration_dictionary.set(parsed_data[1], parsed_data[2], parsed_data[4])
        return resp_builder('+', 'OK')
    else:
        return resp_builder('-', 'ERR wrong number of arguments for \'set\' command')


def handle_get_command(parsed_data):
    value = expiration_dictionary.get(parsed_data[1])
    if value:
        return resp_builder('$', value)
    else:
        return resp_builder('$', None)


def handle_info_command(server_config):
    return resp_builder('$',
                        f'role:{server_config.replica}\nmaster_replid:{server_config.master_replid}\nmaster_repl_offset:{server_config.master_repl_offset}\n')
    # info_replica = f'role:{replica}'
    # info_replid = f'master_replid:{master_replid}'
    # info_offset = f'master_repl_offset:{master_repl_offset}'
    # info = [f'${len(info_replica)}\r\n{info_replica}\r\n', f'${len(info_replid)}\r\n{info_replid}\r\n',
    #         f'${len(info_offset)}\r\n{info_offset}\r\n']
    # resp = f'*{len(info)}\r\n'
    # for i in info:
    #     resp += i


if __name__ == "__main__":
    config = ServerConfig()
    if '--port' in sys.argv or '-p' in sys.argv:
        port_index = sys.argv.index('--port')
        config.port_number = int(sys.argv[port_index + 1])
    if '--replicaof' in sys.argv:
        replica_index = sys.argv.index('--replicaof')
        config.replica = 'slave'
        config.master_host = sys.argv[replica_index + 1]
        config.master_port = int(sys.argv[replica_index + 2])
    main(config)
