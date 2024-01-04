# By Abhishek Pradeep
# zID: z5454612
# Python version: 3.11.6

import time
import socket
import threading
import sys
import select
import logging
import re
import json




class Client(threading.Thread):
    sock = None
    name = ''
    #privates = {}
    server = None
    ip = ''
    port = ''

    def __init__(self, ip, port):
        super(Client, self).__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
        hostname = socket.gethostname()
        self.ip = socket.gethostbyname(hostname)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ip, 0))
        self.port = str(self.server.getsockname()[1])
        self.server.listen(10)


    def UDP_video_sender(self, localhost, port, filename):
        buffer = 1024
        print("Entered video sender func")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        localhost = "127.0.0.1" if localhost == "localhost" else localhost
        addr = (localhost, port)

        # Send the filename
        #s.bind(('127.0.0.1', port))
        s.sock.send(filename.encode(), addr)

        # Send the file content
        with open(filename, 'rb') as file:
            data = file.read(buffer)
            while data:
                s.sock.send(data, addr)
                data = file.read(buffer)
        s.close()
        print(f'File {filename} sent successfully')
        
def UDP_video_receiver(self, localhost, port, sender_username):
    print("Entered video reciever func")
    buffer_size = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    localhost = "127.0.0.1" if localhost == "localhost" else localhost
    s.bind((localhost, port))

    print(f"Listening for file transfer on {localhost}:{port}...")

    # Receive the filename
    data, _ = s.sock.recv(buffer_size)
    filename = data.decode().strip()
    new_filename = sender_username + '_' + filename
    print(f"Receiving file: {new_filename}")

    # Receive and write file data
    with open(new_filename, 'wb') as f:
        while True:
            data, _ = s.recvfrom(buffer_size)
            if not data:
                break
            f.write(data)

    print(f"File {new_filename} received successfully.")
    s.close()


    def handle_p2pvideo_command(self, recipient_username, recipient_ip, recipient_port, filename):
        receiver_thread = threading.Thread(target=self.UDP_video_receiver, args=(self.ip, self.port, self.name))
        receiver_thread.start()

        # Start UDP sender thread to send the file to the recipient
        sender_thread = threading.Thread(target=self.UDP_video_sender, args=(recipient_ip, recipient_port, filename))
        sender_thread.start()

        # Wait for both threads to complete
        sender_thread.join()
        receiver_thread.join()

        print(f"File transfer with {user_nam} completed.")



    def handle_server_communication(self):
        while True:
            resp = self.sock.recv(1024).decode('utf-8')
            if resp == 'wrong username':
                print('Invalid username, try again!')
                self.name = input('Enter your username: ')
                pwd = input('Enter your password: ')
                req = 'login ' + self.name + '&' + pwd
                self.sock.send(req.encode('utf-8'))
                
            elif resp == 'wrong password':
                print('Invalid credentials, try again!')
                self.name = input('Enter your username: ')
                pwd = input('Enter your password: ')
                req = 'login ' + self.name + '&' + pwd
                self.sock.send(req.encode('utf-8'))
                
            elif resp == 'timeout':
                print('Timeout, log out!')
                break
            
            elif resp.split(' ')[0] == 'newer':
                print(resp.split(' ')[1] + ' has just logged in!')
                print(">")
                
            elif resp.split(' ')[0] == 'creategroup':
                all_parts = resp.split(' ')[1:]
                all_joined = ' '.join(all_parts)
                grpname, msg = all_joined.split('&')
                gm = msg.split(' ')
                print(f"Group chat created {grpname}")
                
            elif resp.split(' ')[0] == 'joingroup':
                all_parts = resp.split(' ')[1:]
                all_joined = ' '.join(all_parts)
                print(all_joined)
                print('>')
                
            elif resp.split(' ')[0] == 'activeuser':
                #https://www.geeksforgeeks.org/read-json-file-using-python/ learnt how to use json
                data = resp[len('activeuser '):]  # Get the JSON part of the response
                user_data = json.loads(data)  # Decode the JSON string into Python objects
                #print(data)
                if user_data == []:
                    print("No users are currently active.")
                    print(">")
                else: 
                    for user in user_data:
                        print(f"{user['username']} active since {user['login_time']}, port: {user['port']}, ip: {user['ip']}", end=' ')
                        print()
                    print('>')
                
            elif resp.split(' ')[0] == 'message':
                sender = resp.split(' ')[1]
                msg = resp.split(' ')[2:]
                print(time.strftime('%d %m %Y %H:%M:%S')+', ' + sender + ': ' + ' '.join(msg))
                
            elif resp.split(' ')[0] == 'groupmsg':
                msg1 = resp.split(' ')[2:]
                print(msg)
                
            elif resp.split(' ')[0] == 'Invalidreceiver!':
                print('Invalid receiver!\n>')
                
            elif resp.split(' ')[0] == 'Invalidblock!':
                print('Invalid user to block!\n>')
                
            elif resp.split(' ')[0] == 'nologin':
                print('You are not logged in!')
            
            elif resp.split(' ')[0] == 'p2pvideo':
                print("I am inside response")
                reciever_usr = resp.split(' ')[1]
                filename = resp.split(' ')[2]
                recipient_ip = resp.split(' ')[3]
                recipient_port = resp.split(' ')[4]
                match = re.search(r'fd=(\d+)', recipient_port)
                if match:
                    port = int(match.group(1))
                print(recipient_ip)
                print(filename)
                print(port)
                #port=int(recipient_port)
                sender_user = resp.split(' ')[5]
                self.handle_p2pvideo_command(sender_user, recipient_ip, port, filename)
            
                
            elif resp.split(' ')[0] == 'history':
                sender = resp.split(' ')[1]
                msg1 = resp.split(' ')[2:]
                print(sender + '(history): ' + ' '.join(msg1))
                
            elif resp.split(' ')[0] == 'youlogout':
                print('You just logged out!')
                
            elif resp.split(' ')[0] == 'creategroupfail':
                print('Please enter at least one more actual active users.')
                
            elif resp.split(' ')[0] == 'logout':
                username = resp.split(' ')[1]
                print("Bye, " +username+"!")


if __name__ == '__main__':

    #https://betterstack.com/community/guides/logging/how-to-start-logging-with-python/ - Used to learn and update logging         
    msg_logger_logger = logging.getLogger('message_logger')
    message_log_format = '%(message)s'
    msg_logger_logger.setLevel(logging.INFO)
    message_handler = logging.FileHandler('messagelog.txt', mode='a')  # 'a' mode for appending to the log file
    message_handler.setFormatter(logging.Formatter(message_log_format))
    msg_logger_logger.addHandler(message_handler)

    if len(sys.argv) != 3:
        print("Usage: python3 client.py <server ip or localhost > <port number>")
        sys.exit(1)
    elif len(sys.argv) == 3:
        ip = sys.argv[1]
        port = int(sys.argv[2])
        client = Client(ip, port)

        # prompting login
        print("Please login")
        client.name = input('Username: ')
        pwd = input('Password: ')
        req = 'login ' + client.name + '&' + pwd
        client.sock.send(req.encode('utf-8'))
        while True:
            resp = client.sock.recv(1024).decode('utf-8')
            if resp == 'online':
                print('Already online!')
                client.sock.close()
                client.server.close()
                sys.exit(0)
            elif resp == 'wrong username':
                print('Invalid username, try again!')
                client.name = input('Enter your username: ')
                pwd = input('Enter your password: ')
                req = 'login ' + client.name + '&' + pwd
                client.sock.send(req.encode('utf-8'))
            elif resp == 'wrong password':
                print('Invalid Password. Please try again')
                pwd = input('Enter your password: ')
                req = 'login ' + client.name + '&' + pwd
                client.sock.send(req.encode('utf-8'))
            elif resp.split(' ')[0] == 'success':
                client.sock.send((client.name + '@success ' + client.ip + '&' + client.port).encode('utf-8'))
                print('*' * 50)
                print('Welcome to Abhisheks COMP9331 message application!!!')
                print('Welcome to TESSENGER!')
                print('*' * 50)
                print("Enter one of the following commands (/msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /logout, /p2pvideo):")
                break
            elif resp == 'blocked':
                print('Your account is blocked due to multiple login failures. Please try again later')
                client.sock.close()
                client.server.close()
                sys.exit(0)
            elif resp == 'last check':
                print("Invalid Password. Your account has been blocked. Please try again later")
                client.sock.close()
                client.server.close()
                sys.exit(0)
                
        message_counter=0
        client.start()
        while True:
            req = input(">")
            #  get command
            if " " in req:
                cmd = req.split(" ")[0]
            else:
                cmd = req
            if cmd == '/msgto':
                parts = req.split(" ")
                if len(parts) < 3:
                    print("Error: No recipient or message specified.")
                    continue  # This will prompt the ">" again
                else:
                    recipient = parts[1]
                    msg = parts[2:]
                #mycode
                text = " ".join(msg)
                message_counter=message_counter+1
                message_info = f"{message_counter}; {time.strftime('%Y-%m-%d %H:%M:%S')}; {recipient}; {text};"
                msg_logger_logger.info(message_info)
                print(f">Message sent at {time.strftime('%d-%m-%Y %H:%M:%S')}.")
                client.sock.send((client.name + '@message ' + recipient + '&' + ' '.join(msg)).encode('utf-8'))
                
            elif cmd == '/groupmsg':
                parts = req.split(" ")
                if len(parts)<2:
                    print("Error: Please enter group name and message")
                groupname = parts[1]
                msg = parts[2:]
                text = " ".join(msg)
                #print(text)
                client.sock.send((client.name + '@groupmsg ' + groupname+'&'+text).encode('utf-8'))
                
            elif cmd == '/activeuser':
                client.sock.send((client.name + '@activeuser').encode('utf-8'))
                
            elif cmd == '/p2pvideo':
                parts = req.split(" ")
                if len(parts)<3:
                    print("Error: please mention username and filename")
                user_nam = parts[1]
                filename =parts[2]
                client.sock.send((client.name + '@p2pvideo '+user_nam+ '&' +filename).encode('utf-8'))
            
            elif cmd == '/logout':
                client.sock.send((client.name + '@logout').encode('utf-8'))
                
            elif cmd == '/joingroup':
                parts = req.split(" ")
                grpname = parts[1]
                if len(parts)<2 or len(parts)>3:
                    print("Enter valid group name")
                else:
                    client.sock.send((client.name + '@joingroup '+"&"+grpname).encode('utf-8'))
            
            elif cmd == '/creategroup':
                parts = req.split(" ")
                if len(parts) >= 2 and len(parts)<3:
                    print("Please enter at least one more active users.")
                elif len(parts)< 2:
                    print("Error: No group name or member specified")
                else:
                    groupname = parts[1]
                    #print(f"sending cleint nam {groupname}")
                    users = parts[2:]
                    text = " ".join(users)
                    newtext=client.name+ " " + text
                    #print(f"sending cleint nam {text}")
                    client.sock.send((client.name + '@creategroup '+groupname+'&'+newtext).encode('utf-8'))    
            else:
                print('Invalid commands!')