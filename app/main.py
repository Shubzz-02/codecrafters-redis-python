# Uncomment this to pass the first stage
import socket


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    c, addr = server_socket.accept()  # wait for client

    while True:
        data = c.recv(1024).decode("utf-8")
        if "ping" in data:
            c.send("+PONG\r\n".encode())
        else:
            c.send("-ERR unknown command\r\n".encode())


if __name__ == "__main__":
    main()
