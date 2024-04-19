# Uncomment this to pass the first stage
import socket
from app.RedisProtocolParser import parse_protocol
from app.CustomDictionary import TTLDictionary
from threading import Thread
import sys

ttl_dict = TTLDictionary()
port_number = 6379
replica = 'master'


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
            info = f'role:{replica}'
            resp = f'${len(info)}\r\n{info}\r\n'
            client_sock.sendall(resp.encode("utf-8"))
        else:
            resp = '+skkep\r\n'
            client_sock.sendall(resp.encode("utf-8"))


if __name__ == "__main__":
    if '--port' in sys.argv or '-p' in sys.argv:
        port_index = sys.argv.index('--port')
        port_number = int(sys.argv[port_index + 1])
    if '--replicaof' in sys.argv:
        replica_index = sys.argv.index('--replicaof')
        replica = 'slave'
    main()
