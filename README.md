# Secure FTP System  

## **Project Overview**  
This project is the **final project for the Computer Networks course at university**, implementing a **Secure FTP (File Transfer Protocol) system** using Python. The system enables **secure file transfers** over **SSL/TLS**, ensuring **encrypted communication**, **user authentication**, and **controlled file access** between a **client and a multi-threaded server**.  

## **Features**  
✅ **SSL/TLS Encryption** for secure file transfer  
✅ **User Authentication & Registration** with credential storage  
✅ File **Upload (STOR)** and **Download (RETR)** support  
✅ **Directory Listing (LIST)** and **Navigation (CWD, PWD, CDUP)**  
✅ File **Sharing (SHAR)** and **Unsharing (UNSH)** with permission levels  
✅ **Multi-Threaded Server** for handling multiple clients  
✅ **Access Control & User-Based Permissions**  

## **Project Structure**  
- **`Client.py`** → Implements the FTP client for interacting with the server.  
- **`Server.py`** → Implements the FTP server, handling user authentication, file operations, and access control.  

## **Setup & Installation**  

### **1. Install Dependencies**  
Ensure you have Python 3 installed. Required libraries include:  
```bash
pip install pyopenssl
```

### **2. Start the Server**  
Run the FTP server and specify ports if needed:  
```bash
python Server.py
```
_Default Control Port: `10021`, Data Port: `10020`_  

### **3. Start the Client**  
Run the FTP client and connect to the server:  
```bash
python Client.py
```
_Default server: `localhost`_  

## **Usage**  
After connecting, use the following FTP commands:  

| **Command**  | **Description**  | **Example**  |
|-------------|----------------|-------------|
| `LIST`      | List files & directories  | `LIST`  |
| `RETR <file>` | Download a file  | `RETR example.txt`  |
| `STOR <client_file> <server_path>` | Upload a file  | `STOR local.txt /remote.txt`  |
| `PWD`       | Show current directory | `PWD` |
| `CWD <dir>` | Change directory | `CWD /documents` |
| `CDUP`      | Move to parent directory | `CDUP` |
| `MKD <dir>` | Create a directory | `MKD new_folder` |
| `RMD <dir>` | Remove a directory | `RMD old_folder` |
| `DELE <file>` | Delete a file | `DELE sample.txt` |
| `SHAR <file>` | Share a file with a user | `SHAR shared.txt` |
| `UNSH <file>` | Unshare a file | `UNSH shared.txt` |
| `SHWM` | View shared files | `SHWM` |
| `QUIT`      | Disconnect from the server | `QUIT` |

## **Security Features**  
🔒 **SSL/TLS Encryption** for secure data transmission  
🔐 **User Authentication** with credential verification  
📂 **File Permission Control** for secure access  

## **Contributors**  
- **Mahdi Rahbar**  
- **Kiarash Gilanian**  
