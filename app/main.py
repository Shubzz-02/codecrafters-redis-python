# Uncomment this to pass the first stage
import socket
from threading import Thread


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)

    while True:
        client_sock = server_socket.accept()[0]
        thread = Thread(target=handle_client, args=(client_sock,))
        thread.start()


def handle_client(client_sock):
    while True:
        data = client_sock.recv(1024).decode("utf-8")

        if 'ping' in data:
            resp = '+PONG\r\n'
            client_sock.sendall(resp.encode("utf-8"))


if __name__ == "__main__":
    main()
