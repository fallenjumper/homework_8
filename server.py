from http import HTTPStatus
import socket
from config import host, port, amount_clients, timeout_connection
import threading
import logging

logging.basicConfig(level=logging.INFO)
ServerSocket = socket.socket()

try:
    ServerSocket.bind((host, port))
except Exception as e:
    print(f"When try bind port raised exception: {e} ")

ServerSocket.listen(amount_clients)
print(f"SocketServer started on {host}:{port} for {amount_clients} clients ")


def client_handler(_conn, _client):
    # conf logger
    logger = logging.getLogger(_client)
    logger.info("Connected new client")
    # set session timeout
    _conn.settimeout(timeout_connection)

    # get data
    while True:
        try:
            data_raw = _conn.recv(1024)
            logger.info(f"Received data {data_raw}")
        except ConnectionResetError:
            logger.warning("Received close singal.")
            break
        except socket.timeout:
            logger.error("Timeout connection without any data")
            break

        # close conn on empty data
        if not data_raw:
            logger.info("Received empty data.")
            break

        # format and parse data
        data = data_raw.decode('utf-8').split("\r\n")
        method = data[0].split(" ")[0]
        path = data[0].split(" ")[1]
        res_status = f"{HTTPStatus(200).value} {HTTPStatus(200).phrase}"

        # get status
        if "?status=" in path:
            try:
                recv_status = int(path.split("?status=")[1])
                res_status = f"{HTTPStatus(recv_status).value} {HTTPStatus(recv_status).phrase}"
            except ValueError:
                logger.error(f"Received incorrect status code. Returned 200 OK.")

        # get headers from data (ignore first elem with method and path)
        headers = [i for i in data[1:]]

        # construct reply
        tuple_src = (_client.split(':')[0], int(_client.split(':')[1]))
        reply = f"HTTP/1.1 {res_status}\r\n" \
                f"{(chr(13) + chr(10)).join(headers)}" \
                f"Request Method: {method}\r\n" \
                f"Request Source: {tuple_src}\r\n" \
                f"Response Status: {res_status}\r\n" \
                f"{(chr(13) + chr(10)).join(headers)}"

        # send data
        _conn.send(str.encode(reply))
        logger.info(f"Sent reply {str.encode(reply)}")

    logger.info("Closed connection")
    _conn.close()


while True:
    conn, address = ServerSocket.accept()
    client = f"{address[0]}:{address[1]}"
    threading.Thread(target=client_handler, args=(conn, client)).start()
ServerSocket.close()
