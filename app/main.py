import socket
from app.RedisProtocolParser import parse_protocol
from app.CustomDictionary import TTLDictionary
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

    @staticmethod
    def generate_random_string(length):
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string


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
    # master_socket.sendall(f'REPLCONF listening-port {server_config.port_number}\r\n'.encode("utf-8"))
    # master_socket.sendall(f'REPLCONF capa eof\r\n'.encode("utf-8"))
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
        response = process_command(parsed_data, server_config)
        client_sock.sendall(response.encode("utf-8"))


def process_command(parsed_data, server_config):
    command = parsed_data[0].lower()
    if command == 'ping':
        return '+PONG\r\n'
    elif command == 'echo':
        return f'${len(parsed_data[1])}\r\n{parsed_data[1]}\r\n'
    elif command == 'set':
        return handle_set_command(parsed_data)
    elif command == 'get':
        return handle_get_command(parsed_data)
    elif command == 'info':
        return handle_info_command(server_config)
    else:
        return '+skip\r\n'


def handle_set_command(parsed_data):
    arr_len = len(parsed_data)
    if arr_len < 3:
        return '-ERR wrong number of arguments for \'set\' command\r\n'
    elif arr_len == 3:
        expiration_dictionary.set(parsed_data[1], parsed_data[2], None)
        return '+OK\r\n'
    elif arr_len == 5:
        expiration_dictionary.set(parsed_data[1], parsed_data[2], parsed_data[4])
        return '+OK\r\n'


def handle_get_command(parsed_data):
    value = expiration_dictionary.get(parsed_data[1])
    if value:
        return f'${len(value)}\r\n{value}\r\n'
    else:
        return '$-1\r\n'


def handle_info_command(server_config):
    data = f'role:{server_config.replica}\nmaster_replid:{server_config.master_replid}\nmaster_repl_offset:{server_config.master_repl_offset}\n'
    return f'${len(data)}\r\n{data}\r\n'
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
