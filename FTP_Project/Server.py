import socket
import threading

class FTPThreadServer(threading.Thread):
    def __init__(self, client_data, local_ip, data_port):
        client, client_address = client_data
        self.client = client
        self.client_address = client_address
        self.cwd = "C:\\Users\\User\\Desktop\\Server"  # Default server path
        self.data_address = (local_ip, data_port)
        threading.Thread.__init__(self)

    def start_datasock(self):
        try:
            print('Creating data socket on ' + str(self.data_address) + '...')
            self.datasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.datasock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.datasock.bind(self.data_address)
            self.datasock.listen(5)
            print('Data socket is started. Listening to ' + str(self.data_address) + '...')
            self.client.send(b'125 Data connection already open; transfer starting.\r\n')
            return self.datasock.accept()
        except Exception as e:
            print('ERROR: ' + str(self.client_address) + ': ' + str(e))
            self.close_datasock()
            self.client.send(b'425 Cannot open data connection.\r\n')

    def close_datasock(self):
        print('Closing data socket connection...')
        try:
            self.datasock.close()
        except:
            pass

    def run(self):
        try:
            print('Client connected: ' + str(self.client_address) + '\n')

            # Perform authentication or registration
            if not self.authenticate():
                self.client.send(b"530 Authentication failed or registration unsuccessful. Disconnecting.\r\n")
                self.client.close()
                return

            while True:
                cmd = self.client.recv(1024).decode('utf-8').strip()
                if not cmd:
                    break
                print('Commands from ' + str(self.client_address) + ': ' + cmd)
                try:
                    func = getattr(self, cmd[:4].strip().upper())
                    func(cmd)
                except AttributeError as e:
                    print('ERROR: ' + str(self.client_address) + ': Invalid Command.')
                    self.client.send(b'550 Invalid Command\r\n')
        except Exception as e:
            print('ERROR: ' + str(self.client_address) + ': ' + str(e))
            self.QUIT('')

    def QUIT(self, cmd):
        try:
            self.client.send(b'221 Goodbye.\r\n')
        except:
            pass
        finally:
            print('Closing connection from ' + str(self.client_address) + '...')
            self.close_datasock()
            self.client.close()
            quit()


class FTPserver:
    def __init__(self, port, data_port):
        self.address = '0.0.0.0'
        self.port = int(port)
        self.data_port = int(data_port)

    def start_sock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = (self.address, self.port)

        try:
            print('Creating data socket on', self.address, ':', self.port, '...')
            self.sock.bind(server_address)
            self.sock.listen(5)
            print('Server is up. Listening to', self.address, ':', self.port)
        except Exception as e:
            print('Failed to create server on', self.address, ':', self.port, 'because', str(e))
            quit()

    def start(self):
        self.start_sock()

        try:
            while True:
                print('Waiting for a connection')
                thread = FTPThreadServer(self.sock.accept(), self.address, self.data_port)
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print('Closing socket connection')
            self.sock.close()
            quit()


# Main
port = input("Port - if left empty, default port is 10021: ")
if not port:
    port = 10021

data_port = input("Data port - if left empty, default port is 10020: ")
if not data_port:
    data_port = 10020

server = FTPserver(port, data_port)
server.start()
