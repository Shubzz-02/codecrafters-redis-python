# Uncomment this to pass the first stage
import socket
from app.RedisProtocolParser import parse_protocol
from CustomDictionary import TTLDictionary
from threading import Thread

ttl_dict = TTLDictionary()


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
        else:
            resp = '+skkep\r\n'
            client_sock.sendall(resp.encode("utf-8"))


if __name__ == "__main__":
    main()
