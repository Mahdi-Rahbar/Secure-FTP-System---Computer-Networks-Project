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

    def resolve_path(self, path_to_file_or_directory):
        if path_to_file_or_directory.startswith('/'):
            # Absolute path: Join with the server directory
            return os.path.join(self.server_dir, path_to_file_or_directory.lstrip('/'))
        else:
            # Relative path: Prepend '/' and join with the current working directory
            return os.path.join(self.cwd, path_to_file_or_directory)
        
    def hide_abs_path(self, path_to):
        relative_path = path_to[len(self.server_dir):]

        # Ensure the path starts with a '/'
        if not relative_path.startswith('/'):
            relative_path = '/' + relative_path
        
        return relative_path

    def SHARE(self, cmd):
        """Handles the SHARE command."""
        try:
            # Extract directory or file address
            _, file_or_dir_path = cmd.split(' ', 1)
            
            if not file_or_dir_path:
                self.client.send(b'501 Missing arguments <file_or_directory_name>.\r\n')
                return
            
            # Perform access check before proceeding
            if not self.access_check(f"SHARE {file_or_dir_path}"):
                # access_check already sends an appropriate error message if access is denied
                return

            fname = self.resolve_path(file_or_dir_path)
            if not os.path.exists(fname):
                self.client.send(b'550 File or directory not found.\r\n')
                return

            # Ask for the username to share with
            self.client.send(b"332 Enter the username to share with:\r")
            target_username = self.client.recv(1024).decode('utf-8').strip()

            # Check if the target user exists
            target_json_path = os.path.join(self.server_dir, f"home_{target_username}.json")
            if not os.path.exists(target_json_path):
                self.client.send(b"530 Invalid username. User does not exist.\r\n")
                return

            # Ask for the access level as a 4-bit number
            self.client.send(b"332 Enter the access level as a number (0-15):\r")
            try:
                access_level = int(self.client.recv(1024).decode('utf-8').strip())
            except ValueError:
                self.client.send(b"530 Invalid input. Please enter a number between 0 and 15.\r\n")
                return

            if not (0 <= access_level <= 15):
                self.client.send(b"530 Invalid access level. Number must be between 0 and 15.\r\n")
                return

            # Decode access levels from the 4-bit number
            permissions = {
                "Read": bool(access_level & 8),  # 1000
                "Write": bool(access_level & 4),  # 0100
                "Create": bool(access_level & 2),  # 0010
                "Delete": bool(access_level & 1),  # 0001
            }

            # Update the shared user's JSON file with the new access level
            with open(target_json_path, 'r') as json_file:
                target_data = json.load(json_file)

            # Add the file or directory access for the target user
            if "home" not in target_data:
                target_data["home"] = {"path": {}}
            if "path" not in target_data["home"]:
                target_data["home"]["path"] = {}

            # Add or update permissions for the shared path
            target_data["home"]["path"][fname] = permissions

            with open(target_json_path, 'w') as json_file:
                json.dump(target_data, json_file)

            self.client.send(b"230 File or directory shared successfully with the specified access level.\r\n")
        except Exception as e:
            print(f"ERROR in SHARE command: {e}")
            self.client.send(b"550 An error occurred while processing the SHARE command.\r\n")

    def access_check(self, cmd, cdup=False):
        try:
            command = cmd.split(' ', 1)[0].upper()
            raw_path = cmd.rsplit(' ', 1)[-1].strip()

            # Resolve the raw path to an absolute path
            path = self.resolve_path(raw_path)

            # Ensure the path exists
            if not os.path.exists(path):
                self.client.send(b"550 Path does not exist.\r\n")
                return False
            
            if command == "SHARE":
                # Get the user's home directory prefix
                user_home_prefix = f"home_{self.current_username}"
                
                # Check if the path starts with the user's home directory
                if path.startswith(os.path.join(self.server_dir, user_home_prefix)):
                    return True
                else:
                    print("You cannot share a file or directory outside of your home directory.")
                    return False


            # Load user's access permissions from their JSON file
            user_json_path = os.path.join(self.server_dir, f"home_{self.current_username}.json")
            if not os.path.exists(user_json_path):
                self.client.send(b"550 User configuration not found.\r\n")
                return False

            with open(user_json_path, 'r') as json_file:
                user_data = json.load(json_file)

            # Extract access paths and permissions
            user_access_paths = user_data.get("home", {}).get("path", {})
            parent_dir = os.path.dirname(self.cwd)

            # If checking CDUP, validate Read permission on the parent directory
            if cdup:
                # Check if parent_dir starts with any path in user_access_paths
                for access_path in user_access_paths:
                    if parent_dir.startswith(access_path):
                        access = user_access_paths[access_path]
                        if access.get("Read", True):
                            return True

                self.client.send(b"530 Insufficient permissions to access parent directory.\r\n")
                return False

            # Determine required permissions based on the command
            required_permissions = {
                "LIST": ["Read"],
                "RETR": ["Read"],
                "STOR": ["Write", "Create", "Delete"],
                "DELE": ["Delete"],
                "MKD": ["Write", "Create"],
                "RMD": ["Delete"],
                "CWD": ["Read"],
            }.get(command, [])

            matching_permissions = {"Read": False, "Write": False, "Create": False, "Delete": False}

            for access_path in user_access_paths:
                if path.startswith(access_path):
                    # Union permissions for matching paths
                    access = user_access_paths[access_path]
                    for permission in matching_permissions:
                        matching_permissions[permission] = matching_permissions[permission] or access.get(permission, False)

            # Check if the user has all required permissions
            for permission in required_permissions:
                if not matching_permissions.get(permission, False):
                    self.client.send(b"530 Insufficient permissions.\r\n")
                    return False

            return True

        except Exception as e:
            print(f"ERROR in access_check: {e}")
            self.client.send(b"550 An error occurred while checking permissions.\r\n")
            return False

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
