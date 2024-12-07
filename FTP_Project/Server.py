# Mahdi Rahbar && Kiarash Gilanian

import socket
import os
import sys
import threading
import json
import time

class FTPThreadServer(threading.Thread):
    def __init__(self, client_data, local_ip, data_port):
        client, client_address = client_data
        self.client = client
        self.client_address = client_address
        self.server_dir = "C:\\Users\\User\\Desktop\\Server"
        self.cwd = "C:\\Users\\User\\Desktop\\Server"  # Default server path
        self.current_username = None
        self.data_address = (local_ip, data_port)
        threading.Thread.__init__(self)
        # Credentials storage (username-password pairs)
        self.credentials = {"admin": "12345678"}
        self.file_path = os.path.join(self.cwd, "credentials.json")
        self.load_credentials()

    def load_credentials(self):
        """Load credentials from a JSON file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as file:
                self.credentials = json.load(file)

    def save_credentials(self):
        """Save credentials to a JSON file."""
        with open(self.file_path, "w") as file:
            json.dump(self.credentials, file)

    def register_user(self):
        """Handles user registration."""
        while True:
            self.client.send(b"332 Enter a new username to register.\r")
            username = self.client.recv(1024).decode('utf-8').strip()

            # Check if the user wants to go back to the previous step
            if username.upper() == "BACK":
                self.client.send(b"530 Registration process aborted.\r\n")
                return False

            # Check if username already exists in the credentials
            if username in self.credentials:
                self.client.send(b"530 Username already exists. Please choose another one.\r\n")
                continue  # Prompt for the username again

            # If username is valid, proceed to ask for password
            self.client.send(b"332 Enter a password.\r")
            password = self.client.recv(1024).decode('utf-8').strip()

            # Store the new user and password
            self.credentials[username] = password
            self.save_credentials()

            # Create a home directory for the user
            user_home_dir = os.path.join(self.cwd, f"home_{username}")
            if not os.path.exists(user_home_dir):
                os.makedirs(user_home_dir)
            
            user_json = {
                "home": {
                    "path": {
                        user_home_dir: {
                            "Read": True,
                            "Write": True,
                            "Create": True,
                            "Delete": True
                        }
                    }
                }
            }
            with open(os.path.join(self.server_dir, f"home_{username}.json"), 'w') as json_file:
                json.dump(user_json, json_file)

            self.current_username = username

            self.cwd = os.path.join(self.cwd, f"home_{username[5:]}")  # Change cwd to user's home folder
            self.client.send(b"230 User registered successfully. You are logged in.\r\n")
            return True

    def authenticate(self):
        # Handles authentication by verifying username and password.
        self.client.send(b"220 Welcome to FTP server.\r\n")

        while True:
            self.client.send(b"331 Please specify the username to login by 'USER username' or type 'REGISTER' to create an account.\r")
            username = self.client.recv(1024).decode('utf-8').strip()

            if username.upper() == 'REGISTER':
                if self.register_user() == False:
                    continue
                else:
                    return True

            if len(username) < 6:
                self.client.send(b"550 Invalid command. Username must be at least 6 characters including 'USER '.\r\n")
                continue

            # Check if the first 5 characters are not 'USER '
            if username[:5] != 'USER ':
                self.client.send(b"550 Invalid command. For input username, must start with 'USER '.\r\n")
                continue

            # Check if the username (after 'USER ') is not in credentials
            if username[5:] not in self.credentials:
                self.client.send(b"530 Invalid username. Please try again.\r\n")
                continue

            while True:
                self.client.send(b"331 Please specify the password by 'PASS password' or type 'CHANGE' to change your username.\r")
                password = self.client.recv(1024).decode('utf-8').strip()

                # If password is 'CHANGE', break the loop (user can change their password)
                if password == "CHANGE":
                    self.client.send(b"230 You will return to the previous step to change your username.\r\n")
                    break

                # Check if password is less than 6 characters
                if len(password) < 6:
                    self.client.send(b"550 Invalid command. Password must be at least 6 characters including 'PASS '.\r\n")
                    continue

                # Check if the first 5 characters are not 'PASS '
                if password[:5] != 'PASS ':
                    self.client.send(b"550 Invalid command. Password must start with 'PASS '.\r\n")
                    continue

                # Check if the password (after 'PASS ') is correct
                if self.credentials[username[5:]] != password[5:]:
                    self.client.send(b"530 Invalid password. Please try again.\r\n")
                    continue  # Ask for the password again if it's invalid

                self.client.send(b"230 Login successful.\r\n")
                self.cwd = os.path.join(self.cwd, f"home_{username[5:]}")  # Change cwd to user's home folder
                self.current_username = username[5:]
                return True  # Return True once authentication is successful

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
