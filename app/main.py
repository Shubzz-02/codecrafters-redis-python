# Uncomment this to pass the first stage
import socket
from app.RedisProtocolParser import parse_protocol
from threading import Thread

simple_map = {}


def main():
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)

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
            simple_map[parsed_data[1]] = parsed_data[2]
            resp = '+OK\r\n'
            client_sock.sendall(resp.encode("utf-8"))
        elif parsed_data[0].lower() == 'get':
            value = simple_map.get(parsed_data[1])
            if value:
                resp = f'${len(value)}\r\n{value}\r\n'
            else:
                resp = '$-1\r\n'
            client_sock.sendall(resp.encode("utf-8"))
        else:
            resp = '+skkep\r\n'
            client_sock.sendall(resp.encode("utf-8"))


if __name__ == "__main__":
    main()
