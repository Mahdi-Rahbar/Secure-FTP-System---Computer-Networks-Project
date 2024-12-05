# Mahdi Rahbar - Kiarash gilanian

import socket
import os
import sys


class FTPclient:
    def __init__(self, address, port, data_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = int(port)
        self.data_port = int(data_port)

    # Establishes a connection to the server using the specified address and port.
    def create_connection(self):

        print('Starting connection to', self.address, ':', self.port)

        try:
            server_address = (self.address, self.port)
            self.sock.connect(server_address)
            print('Connected to', self.address, ':', self.port)
        except KeyboardInterrupt:
            self.close_client()
        except Exception as e:
            print('Connection to', self.address, ':', self.port, 'failed:', str(e))
            self.close_client()


    def connect_datasock(self):
        self.datasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.datasock.connect((self.address, self.data_port))

    # Manages user authentication and registration by handling server communication and user input.
    def authenticate(self):

        try:

            response = self.sock.recv(1024).decode('utf-8')
            print(response)

            if "220" not in response:
                print("Unexpected server response:", response)
                return False

            response = self.sock.recv(1024).decode('utf-8')
            print(response)

            if "331" in response or "332" in response:
                while True:
                    user_input = input("Enter your command: ").strip()
                    self.sock.send(user_input.encode('utf-8'))

                    response = self.sock.recv(1024).decode('utf-8')
                    print(response)

                    if user_input.upper().startswith("REGISTER"):
                        if "332" in response:
                            username = input("Enter a new username: ").strip()
                            self.sock.send(username.encode('utf-8'))

                            response = self.sock.recv(1024).decode('utf-8')
                            print(response)
                            if "332" in response:
                                password = input("Enter a new password: ").strip()
                                self.sock.send(password.encode('utf-8'))

                                response = self.sock.recv(1024).decode('utf-8')
                                print(response)
                                if "230" in response:
                                    print("Registration successful.")
                                    return True
                                else:
                                    print("Registration failed. Try again.")
                                    return False

                    elif user_input.upper().startswith("USER"):

                        if "331" in response:
                            while True:
                                password = input("Enter your password in 'PASS password' format: ").strip()
                                self.sock.send(password.encode('utf-8'))

                                if password.upper().startswith("PASS"):
                                    response = self.sock.recv(1024).decode('utf-8')
                                    print(response)
                                    if "230" in response:
                                        return True
                                    else:
                                        print("Login failed. Invalid credentials. Please try again.")

                                        break
                                else:
                                    print("The command you entered is invalid. Please try again.")
                                    continue

                    else:
                        print("The command you entered is invalid. Please try again.")
                        continue  
            else:
                print("Authentication process finished or failed.")
                return False

        except Exception as e:
            print("Error during authentication:", str(e))