# By Abhishek Pradeep
# zID: z5454612
# Python version: 3.11.6
import select
import sys
import signal
import os
import threading
import socket
import time


import logging
import json
TIMEOUT_VALUE = 300 # five minutes for time out
BLOCK_DURATION = 10 # As mentioned in specifications

#https://bugs.jython.org/issue1313 to check keyboard contr+c exceptions
def intHandler(signum, frame):
    print("User pressed ctrl-c")
    print("\rServer is shutdown")
    raise KeyboardInterrupt()

#Server is declared as Class and the required functions are defined below
class Server:
    user_loggin_num=0
    number_of_trials=0
    accounts = {}
    online_users = []  
    login_tries = {}  
    login_block = {}  
    active_users = {}  # record active time
    block_duration = 0
    timeout = 0
    user_sockets = {} 
    messages = {}
    client_servers = {}
    port = 0
    
    
    login_times={}
    groups = {}
    group_join_check = {}
    udpportdict={}
    #group_logs = {}  # Stores message logs
    
    def __init__(self, port, number_of_trials, duration, timeout):
        self.block_duration = duration
        self.timeout = timeout
        self.port = port
        self.number_of_trials=number_of_trials
        
        # read credentials
        if not os.path.exists('credentials.txt'):
            print("Credentials file not found. Please put credential file in path")
            print()
            print()
            
            
        with open('credentials.txt', 'r') as cred:
            for line in cred.readlines():
                name, password = line.strip().split(' ')
                self.accounts[name] = password
                self.login_tries[name] = 0
                self.login_block[name] = -1
                self.active_users[name] = -1
                self.groups = {}
                self.group_logs = {}  # Stores message logs
                self.login_times[name]=0
                self.group_join_check = {}
                self.udpportdict={}
        #https://betterstack.com/community/guides/logging/how-to-start-logging-with-python/ - Used to learn and update logging         
        self.login_logger = logging.getLogger('user_login_logger')
        login_log_format = '%(message)s'
        self.login_logger.setLevel(logging.INFO)
        login_handler = logging.FileHandler('userlog.txt', mode='a')  # 'a' mode for appending to the log file
        login_handler.setFormatter(logging.Formatter(login_log_format))
        self.login_logger.addHandler(login_handler)


    # whether is on line
    def online(self, name):
        for item in self.online_users:
            user = item[0]
            if name == user:
                return True
        return False
    
    # If the server does not receive any commands from a user for a period of timeout seconds
    # log out
    def offline_detector(self):
        while True:
            for item in self.online_users:
                user = item[0]
                if self.active_users[user] != -1 and time.time() - self.active_users[user] > self.timeout:
                    sock, addr = self.user_sockets[user]
                    try:
                        print(f"{user} has time out!")
                        sock.sendto('timeout'.encode('utf-8'), addr)
                    except ConnectionResetError:
                        print(f"Connection with {user} has been reset.")
                    finally:
                        self.active_users[user] = -1
                        self.online_users.remove(item)
                        self.user_sockets[user] = None
                    

    # start the server
    def start(self, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', port))
        server.listen(10)
        # log out timeout user
        t1 = threading.Thread(target=self.offline_detector)
        t1.start()
        # listen for user connecting
        while True:
            r, w, e = select.select([server, ], [], [], 1)
            for server in r:
                conn, addr = server.accept()
                t = threading.Thread(target=self.process, args=(conn, addr))
                t.start()


    def create_group(self, group_name, members):
            if group_name in self.groups:
                return f"A group chat (Name: {group_name}) already exists."
            if not group_name.isalnum():
                return "Invalid group name."
            for m in members:
                if group_name not in self.groups:
                    self.groups[group_name] = []
                self.groups[group_name].append(m)
                
            self.group_join_check[group_name] = {member: 0 for member in members}
            self.group_join_check[group_name][members[0]] = 1
            #self.group_logs[group_name] = []
            #with open(f"{group_name}_messageLog.txt", "w") as file:
            #   pass  # Initialize log file
            print("Return message :")
            print(f"Group chat room has been created, room name: {group_name}, users in this room: {' '.join(members)}")
            return f"{group_name}&{' '.join(members)}"


    def join_group(self, gpnam, user):
        #print(user)
        #print(gpnam)
        if gpnam not in self.groups:
            print(f"Error: Group '{gpnam}' does not exist.")
            return f"Error: Group '{gpnam}' does not exist."
            
        
        if user not in self.groups[gpnam]:
            self.group_join_check[gpnam][user] = 1
            self.groups[gpnam] = user
            
            print("Return message :")
            print(f"Join group chat room successfully, room name: {gpnam}")
            return f"User '{user}' successfully joined the group '{gpnam}'."
        else:
            print("Return message :")
            print(f"User '{user}' has already joined the group '{gpnam}")
            return f"User '{user}' has already joined the group '{gpnam}'."
        
        
    
        #self.group_join_check[gpnam] = {member: 0 for member in members}
        #self.group_join_check[group_name][members[0]] = 1

    def group_message(self,gpnam, msg,user):
        if gpnam not in self.groups:
            return "The group chat does not exist."
        if user not in self.groups[gpnam] or self.group_join_check[gpnam].get(user, 0) == 0:
            return f"{user} sent a message to a group chat, but {user} hasn't been joined to the group chat."
        for member in self.groups[gpnam]:
            #print(member)
            if member == user and self.group_join_check[gpnam][member] == 1:
                res=self.send_message(user,gpnam)
                #print(res)
                return res

    def send_message(self, usr, gpnam):
        useres=[]
        
        for member in self.groups[gpnam]:
            print(member)
            if member!=usr:
                
                useres.append(member)
        print(useres)
        return useres
    
        # shows that user is online 
    def who_logged_in(self, name):
        for item in self.online_users:
            user = item[0]
            self.user_sockets[user][0].send(('NewUserCheck ' + name).encode('utf-8'))

    # list online users
    def list_online_users(self, currentuser):
        names = []
        for item in self.online_users:
            user = item[0]
            if user != currentuser:
                names.append(user)
        return names

    # process request from client
    def process(self, client, address):
        #print(address)
        while True:
            try:
                req = client.recv(1024).decode('utf-8')
                if req:
                    if " " in req:
                        action = req.split(' ')[0]
                        data = ' '.join(req.split(' ')[1:])
                        #print(data)
                    else:
                        action = req
                    if action == 'login':
                        #user_loggin_num=user_loggin_num+1
                        #print(user_loggin_num)
                        name, password = data.split('&')
                        #print(name,password)
                        if name in self.accounts:

                            # block duration
                            if self.login_block[name] != -1 and time.time() - \
                                self.login_block[name] < self.block_duration:
                                client.send('blocked'.encode('utf-8'))
                            else:
                                self.login_block[name] = -1  # recover block status
                                if password == self.accounts[name]:
                                    self.user_loggin_num += 1
                                    #print(self.user_loggin_num)
                                    self.login_times[name]=time.strftime('%Y-%m-%d %H:%M:%S')
                                    login_info = f"{self.user_loggin_num}; {time.strftime('%Y-%m-%d %H:%M:%S')}; {name}; {address[0]}; {address[1]}"
                                    self.login_logger.info(login_info)
                                    
                                    if self.online(name):  # already login
                                        client.send('online'.encode('utf-8'))
                                    else:
                                        # broadcast presence
                                        self.who_logged_in(name)
                                        self.online_users.append((name, time.time()))
                                        self.active_users[name] = time.time()
                                        self.user_sockets[name] = (client, address)
                                        self.login_tries[name] = 0
                                        client.send('success '.encode('utf-8'))
                                else:
                                    self.login_tries[name] += 1  # add tries
                                    if self.login_tries[name] > self.number_of_trials:
                                        # print('block')
                                        client.sendto('blocked'.encode('utf-8'), address)
                                        self.login_block[name] = time.time()
                                        # client.close()
                                        # break
                                    else:
                                        if self.login_tries[name] == self.number_of_trials:
                                            client.sendto('last check'.encode('utf-8'), address)
                                        else:
                                            client.sendto('wrong password'.encode('utf-8'), address)
                        else:
                            client.sendto('wrong username'.encode('utf-8'), address)
                    else:
                        username = action.split('@')[0]
                        action = action.split('@')[1]
                        if self.online(username):
                            # receive command, update active time
                            self.active_users[username] = time.time()
                            if action == 'message':
                                receipt, msg = data.split('&')
                                if receipt == username or receipt not in self.accounts:
                                    client.send('Invalidreceiver!'.encode('utf-8'))
                                else:
                                    if self.online(receipt):
                                        self.user_sockets[receipt][0].send(('message ' + username + ' ' + msg).encode('utf-8'))
                                    else:
                                        if receipt in self.messages:
                                            self.messages[receipt].append((username, msg))
                                        else:
                                            self.messages[receipt] = [(username, msg)]
                            
                            elif action == 'p2pvideo':
                                usr, filename = data.split('&')
                                #print(usr)
                                #print(filename)
                                reciever_udport= self.udpportdict[usr]
                                sender_udport= self.udpportdict[username]
                                #filename, udpport=total.spilt(" ")
                                #self.udpportdict[username]=udpport
                                online_usernames = [item[0] for item in self.online_users]
                                if usr not in online_usernames:
                                    print("User is not active so cannot send the file ")
                                    client.send(f'{usr} is offline'.encode('utf-8'))
                                else:
                                    #print("Entered the loop")
                                    recipient_ip = self.user_sockets[usr][1][0]
                                    #recipient_port = self.user_sockets[usr][1][1]
                                    #sender_port = self.user_sockets[username][1][1]
                                    
                                    #print(recipient_ip)
                                    #print(reciever_udport)
                                    #print(self.user_sockets[usr][0])
                                    response = f'{usr} {filename} {recipient_ip} {reciever_udport} {username} {sender_udport}'
                                    #print(response)
                                    self.user_sockets[usr][0].send(('p2pvideo ' + response).encode('utf-8'))
                                
                                         
                            elif action == 'groupmsg':
                                group_counter=0
                                #https://betterstack.com/community/guides/logging/how-to-start-logging-with-python/ - Used to learn and update logging         
                                grp_msg_logger_logger = logging.getLogger('gr_message_logger')
                                message_log_format = '%(message)s'
                                grp_msg_logger_logger.setLevel(logging.INFO)
                                
                                
                                
                                print(f"{username} issued a message in group chat")
                                grpname, msg = data.split('&')
                                #print(msg)
                                #print(grpname)
                                file_name=str(grpname) +'_messagelog.txt'
                                grpmessage_handler = logging.FileHandler(file_name, mode='a')  # 'a' mode for appending to the log file
                                grpmessage_handler.setFormatter(logging.Formatter(message_log_format))
                                grp_msg_logger_logger.addHandler(grpmessage_handler)
                                
                                message_group_response=self.group_message(grpname, msg,username)
                                group_counter=group_counter+1
                                text=grpname+'&'+msg

                                print(message_group_response)
                                if isinstance(message_group_response, list):
                                    print("enter the loop")
                                    for receipt in message_group_response:
                                        if receipt != username:
                                            message_info = f"{group_counter}; {time.strftime('%Y-%m-%d %H:%M:%S')}; {receipt}; {msg};"
                                            grp_msg_logger_logger.info(message_info)
                                            self.user_sockets[receipt][0].send(('groupmsg ' + username + ' ' + text).encode('utf-8'))
                                else:
                                    message_group1_response='Error: Group chat is empty'
                                    client.send(('groupmsg ' + message_group1_response).encode('utf-8'))
                                  
                            elif action == 'joingroup': 
                                print(f"{username} issued /joingroup command")
                                grpname=data.split('&')[1]
                                join_group_response = self.join_group(grpname, username)
                                client.send(('joingroup ' + join_group_response).encode('utf-8'))
                                    
                            elif action == 'creategroup':
                                check_flag=True
                                print(f"{username} issued /creategroup command")
                                grpname, grpmemebrs = data.split('&')
                                #print(grpname)
                                #print(grpmemebrs)
                                grpmemberlist=grpmemebrs.split(" ")
                                #grpmemberlist.append(username)
                                online_usernames = [item[0] for item in self.online_users]
                                for m in grpmemberlist:
                                    if m not in online_usernames:
                                        #print(m)
                                        check_flag=False
                                        break
                                            
                                if check_flag:
                                    #print(grpmemberlist)
                                    create_group_response = self.create_group(grpname, grpmemberlist)
                                    if grpname in self.groups:
                                        self.group_join_check[grpname] = {member: 0 for member in self.groups[grpname]}
                                        self.group_join_check[grpname][username] = 1 #setting the person who created the group as 1
                                    else:
                                        print(f"Error: Group '{grpname}' does not exist or has not been created yet.")
                                    client.send(('creategroup ' + create_group_response).encode('utf-8'))
                                else:
                                    client.send(('creategroupfail ').encode('utf-8'))
                                
                            elif action == 'activeuser':
                                user_data = []
                                print(f"{username} issued /activeuser command")
                                for item in self.online_users:
                                    un = item[0]
                                    #https://www.geeksforgeeks.org/read-json-file-using-python/ learnt how to use json
                                    if un != username:
                                        login_time = self.login_times[un]
                                        sock, addr = self.user_sockets[un]
                                        ip,port =addr
                                        #print(ip)
                                        #print(port)
                                        user_data.append({
                                        "username": un, 
                                        "login_time": str(login_time),
                                        "ip": ip,
                                        "port": port
                                    })

                                names_times = json.dumps(user_data)  # Convert the list of dictionaries to a JSON string
                                print("Return Messages:")
                                if user_data == []:
                                    print(f"No users are currently active other than {username}")
                                    print(">")
                                else:
                                    for user in user_data:
                                        print(f"{user['username']} active since {user['login_time']}, port: {user['port']}, ip: {user['ip']}", end=' ')
                                    print()  # Newline after printing all users
                                    client.send(('activeuser ' + names_times).encode('utf-8'))
                            elif action == 'logout':
                                for item in self.online_users:
                                    if item[0] == username:
                                        self.online_users.remove(item)
                                        self.login_times[username]=0 # to remove time when u logout
                                        client.send('youlogout'.encode('utf-8'))
                                        
                                        for item in self.online_users:
                                            user = item[0]
                                            self.user_sockets[user][0].send(('logout ' + username).encode('utf-8'))
                                        break
                                # client.close()
                            elif action == 'success':
                                ip, prts = data.split('&')
                                port,udpport=prts.split(" ")
                                self.client_servers[username] = (ip, port)
                                self.udpportdict[username]=int(udpport)

                        else:
                            client.send('NotloggedIn'.encode('utf-8'))
            except ConnectionResetError:
                     print(f"Connection with client has been reset.")
                     break   


if __name__ == '__main__':
    
    if len(sys.argv) != 3:
        print("Command Line Format: python3 server.py <port number> <number_of_trials>")
        sys.exit(1)
    
    
    number_of_trials=0
    if len(sys.argv) == 3:
        try: 
            port = int(sys.argv[1])
            block_duration = BLOCK_DURATION
            timeout = TIMEOUT_VALUE
            signal.signal(signal.SIGINT, intHandler)
            number_of_trials=int(sys.argv[2])
            if 1 <= number_of_trials <= 5:
                server = Server(port, number_of_trials, block_duration, timeout)
                print("Server has started!")
                server.start(port)
            else:
                print(f"Invalid number of allowed failed consecutive attempt: {number_of_trials}. The valid value of argument number is an integer between 1 and 5")
        except ValueError:
            print(f"Invalid number of allowed failed consecutive attempt: {number_of_trials}. The valid value of argument number is an integer between 1 and 5")
