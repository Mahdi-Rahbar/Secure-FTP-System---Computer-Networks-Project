# Mahdi Rahbar - Kiarash gilanian

import socket
import os
import sys


class FTPclient:
    def __init__(self, address, port, data_port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = int(port)
        self.data_port = int(data_port)
        self.is_authenticated = False

    # Establishes a connection to the server using the specified address and port.
    def create_connection(self):
        print('Starting connection to', self.address, ':', self.port)

        try:
            server_address = (self.address, self.port)
            self.client_socket.connect(server_address)
            print('Connected to', self.address, ':', self.port)
        except KeyboardInterrupt:
            self.close_client()
        except Exception as e:
            print('Connection to', self.address, ':', self.port, 'failed:', str(e))
            self.close_client()

    # Establishes a data connection to the server using the specified address and data port.
    def connect_datasock(self):
        self.datasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.datasock.connect((self.address, self.data_port))

    # Closes the socket connection and terminates the FTP client.
    def close_client(self):
        print('Closing socket connection...')
        try:
            self.client_socket.close()
        except:
            pass
        print('FTP client terminating...')
        sys.exit()

    # Manages the client lifecycle, including connection, authentication, and executing commands in a loop.
    def start(self):
        try:
            self.create_connection()
        except Exception as e:
            print('Error during connection:', str(e))
            self.close_client()

        if not self.is_authenticated:
            self.authenticate()

        while True:
            try:
                command = input("Enter your command: ")
                if not command:
                    print('Need a command.')
                    continue
            except KeyboardInterrupt:
                self.close_client()

            cmd = command[:4].strip().upper()
            path = command[4:].strip()

            try:
                if cmd == 'STOR':

                    self.STOR(path, command)
                else:
                    self.client_socket.send(command.encode('utf-8'))
                    data = self.client_socket.recv(1024).decode('utf-8')
                    print(data)

                    if cmd == 'QUIT':
                        self.close_client()
                    elif cmd in ('LIST', 'RETR'):
                        if data and data[:3] == '125':
                            func = getattr(self, cmd)
                            func(path)
                            data = self.client_socket.recv(1024).decode('utf-8')
                            print(data)
            except Exception as e:
                print('Error:', str(e))
                self.close_client()

    # Handles user authentication by managing login, registration, and password validation.
    def authenticate(self):
        wel_response = self.client_socket.recv(1024).decode('utf-8')
        print(wel_response)
        while not self.is_authenticated:

            response = self.client_socket.recv(1024).decode('utf-8')
            print(response)

            user_input = input("Enter 'USER username' to login or 'REGISTER' to create an account: ").strip()
            while not user_input:
                print("Input cannot be empty. Please try again.")
                user_input = input("Enter 'USER username' to login or 'REGISTER' to create an account: ").strip()
            self.client_socket.send(user_input.encode('utf-8'))

            if user_input.upper() == 'REGISTER':
                self.register_user()
                continue

            if user_input[:5] == 'USER ' and len(user_input) >= 6:
                while True:

                    password_prompt = self.client_socket.recv(1024).decode('utf-8')
                    print(password_prompt)

                    if "Invalid username" in password_prompt:
                        break

                    password_input = input("Enter 'PASS password' or 'CHANGE' to change username: ").strip()
                    while not password_input:
                        print("Input cannot be empty. Please try again.")
                        password_input = input("Enter 'PASS password' or 'CHANGE' to change username: ").strip()

                    self.client_socket.send(password_input.encode('utf-8'))

                    if password_input == "CHANGE":
                        change_message = self.client_socket.recv(1024).decode('utf-8')
                        print(change_message)
                        break

                    password_response = self.client_socket.recv(1024).decode('utf-8')
                    print(password_response)

                    if "successful" in password_response:
                        self.is_authenticated = True
                        break
            else:
                invalid_user_message = self.client_socket.recv(1024).decode('utf-8')
                print(invalid_user_message)

    # Manages user registration by collecting a new username and password, and verifying availability.
    def register_user(self):
        while True:

            register_prompt = self.client_socket.recv(1024).decode('utf-8')
            print(register_prompt)

            username = input("Enter a new username to register or type 'BACK' for go to prev step: ").strip()
            while not username:
                print("Input cannot be empty. Please try again.")
                username = input("Enter a new username to register or type 'BACK' for go to prev step: ").strip()

            self.client_socket.send(username.encode('utf-8'))

            if username.upper() == "BACK":
                back_message = self.client_socket.recv(1024).decode('utf-8')
                print(back_message)
                break

            registration_response = self.client_socket.recv(1024).decode('utf-8')
            print(registration_response)

            if "choose another one" in registration_response:
                continue

            password = input("Enter a password for your account: ").strip()
            while not password:
                print("Input cannot be empty. Please try again.")
                password = input("Enter a password for your account: ").strip()

            self.client_socket.send(password.encode('utf-8'))

            final_response = self.client_socket.recv(1024).decode('utf-8')
            print(final_response)

            if "successfully" in final_response.lower():
                self.is_authenticated = True
                break

    # Retrieves and displays the directory listing from the server using the specified path.
    def LIST(self, path):
        try:
            self.connect_datasock()

            while True:
                dirlist = self.datasock.recv(1024).decode('utf-8')
                if not dirlist:
                    break
                sys.stdout.write(dirlist)
                sys.stdout.flush()
        except Exception as e:
            print('Error during LIST:', str(e))
        finally:
            self.datasock.close()

    # Downloads a file from the server and saves it to the current directory using the specified path.
    def RETR(self, path):
        print(f"Retrieving {path} from the server...")
        try:
            self.connect_datasock()

            filename = os.path.basename(path)
            with open(filename, 'wb') as f:
                while True:
                    data = self.datasock.recv(1024)
                    if not data:
                        break
                    f.write(data)
        except Exception as e:
            print('Error during RETR:', str(e))
        finally:
            self.datasock.close()

    # Uploads a local file to the server using the STOR command.
    def STOR(self, path, command):
        print(f"Processing paths: {path}")

        try:

            parts = path.split(' ', 1)
            client_path, server_path = parts

            if not os.path.isfile(client_path):
                print(f"Error: File '{client_path}' does not exist.")
                return

            self.client_socket.send(command.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(response)

            if response and response[:3] == '125':
                print("150 Preparing to transfer file.")
                self.connect_datasock()
                with open(client_path, 'rb') as f:
                    while True:
                        data = f.read(1024)
                        if not data:
                            break
                        self.datasock.send(data)
                self.datasock.close()
                end_response = self.client_socket.recv(1024).decode('utf-8')
                print(end_response)
            else:
                print("Error:", response)

        except Exception as e:
            print("Error during STOR:", str(e))

    # Shares a file or directory with another user.
    def SHARE(self, command):
        print(f"Sharing: {command}")
        try:
            self.client_socket.send(f"SHARE {command}\r\n".encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(response)
        except Exception as e:
            print("Error during SHARE:", str(e))

    # Removes sharing permissions for a file or directory.
    def UNSHARE(self, command):
        print(f"Unsharing: {command}")
        try:
            self.client_socket.send(f"UNSHARE {command}\r\n".encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(response)
        except Exception as e:
            print("Error during UNSHARE:", str(e))

    # Displays shared files and directories.
    def SHWM(self):
        print("Displaying shared files and directories...")
        try:
            self.client_socket.send(b"SHWM\r\n")
            response = self.client_sockets.recv(1024).decode('utf-8')
            print(response)
        except Exception as e:
            print("Error during SHWM:", str(e))



def main():
    address = input("Destination address - if left empty, default address is localhost: ")
    if not address:
        address = 'localhost'

    port = input("Port - if left empty, default port is 10021: ")
    if not port:
        port = 10021

    data_port = input("Data port - if left empty, default port is 10020: ")
    if not data_port:
        data_port = 10020

    ftpClient = FTPclient(address, port, data_port)
    ftpClient.start()


if __name__ == "__main__":
    main()
