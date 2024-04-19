# Uncomment this to pass the first stage
import socket
from app.RedisProtocolParser import parse_protocol
from app.CustomDictionary import TTLDictionary
from threading import Thread
import sys
import random
import string


def main():
    server_socket = socket.create_server(("localhost", port_number), reuse_port=True)

    while True:
        client_sock = server_socket.accept()[0]
        thread = Thread(target=handle_client, args=(client_sock,))
        thread.start()


def handle_client(client_sock):
    while True:
        data = client_sock.recv(1024).decode("utf-8")
        parsed_data, remaining_data = parse_protocol(data)
        if parsed_data[0].lower() == 'ping':
            resp = '+PONG\r\n'
            client_sock.sendall(resp.encode("utf-8"))
        elif parsed_data[0].lower() == 'echo':
            resp = f'${len(parsed_data[1])}\r\n{parsed_data[1]}\r\n'
            client_sock.sendall(resp.encode("utf-8"))
        elif parsed_data[0].lower() == 'set':
            arr_len = len(parsed_data)
            if arr_len < 3:
                resp = '-ERR wrong number of arguments for \'set\' command\r\n'
                client_sock.sendall(resp.encode("utf-8"))
                continue
            elif arr_len == 3:
                ttl_dict.set(parsed_data[1], parsed_data[2], None)
                resp = '+OK\r\n'
                client_sock.sendall(resp.encode("utf-8"))
            elif arr_len == 5:
                ttl_dict.set(parsed_data[1], parsed_data[2], parsed_data[4])
                resp = '+OK\r\n'
                client_sock.sendall(resp.encode("utf-8"))
        elif parsed_data[0].lower() == 'get':
            value = ttl_dict.get(parsed_data[1])
            if value:
                resp = f'${len(value)}\r\n{value}\r\n'
            else:
                resp = '$-1\r\n'
            client_sock.sendall(resp.encode("utf-8"))
        elif parsed_data[0].lower() == 'info':
            data = f'role:{replica}\nmaster_replid:{master_replid}\nmaster_repl_offset:{master_repl_offset}\n'
            resp = f'${len(data)}\r\n{data}\r\n'
            client_sock.sendall(resp.encode("utf-8"))
            # info_replica = f'role:{replica}'
            # info_replid = f'master_replid:{master_replid}'
            # info_offset = f'master_repl_offset:{master_repl_offset}'
            # info = [f'${len(info_replica)}\r\n{info_replica}\r\n', f'${len(info_replid)}\r\n{info_replid}\r\n',
            #         f'${len(info_offset)}\r\n{info_offset}\r\n']
            # resp = f'*{len(info)}\r\n'
            # for i in info:
            #     resp += i
        else:
            resp = '+skkep\r\n'
            client_sock.sendall(resp.encode("utf-8"))


def generate_random_string(length):
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits

    # Generate a random string
    random_string = ''.join(random.choice(characters) for _ in range(length))

    return random_string


ttl_dict = TTLDictionary()
port_number = 6379
replica = 'master'
master_replid = generate_random_string(40)
master_repl_offset = 0

if __name__ == "__main__":
    if '--port' in sys.argv or '-p' in sys.argv:
        port_index = sys.argv.index('--port')
        port_number = int(sys.argv[port_index + 1])
    if '--replicaof' in sys.argv:
        replica_index = sys.argv.index('--replicaof')
        replica = 'slave'
    main()
