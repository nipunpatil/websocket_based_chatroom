import socket
import threading
import os
import sys

class ChatClient:
    def __init__(self, host='127.0.0.1', port=55555):
        self.nickname = input("Choose a nickname: ")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        self.running = True
        self.current_room = 'general'

    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                   
                    sys.stdout.write('\r' + ' ' * 100 + '\r')
                    print(message)
                    sys.stdout.write('> ')
                    sys.stdout.flush()
            except:
                print("Lost connection to server")
                self.running = False
                self.client.close()
                break

    def write(self):
        while self.running:
            try:
                sys.stdout.write('> ')
                sys.stdout.flush()
                message = input()
                
                if message.lower() == '/quit':
                    self.running = False
                    self.client.close()
                    break
                    
                self.client.send(message.encode('utf-8'))
            except:
                self.running = False
                break

    def start(self):
        print("Connected to server! Type /help for available commands.")
        receive_thread = threading.Thread(target=self.receive)
        write_thread = threading.Thread(target=self.write)
        
        receive_thread.start()
        write_thread.start()

if __name__ == '__main__':
    client = ChatClient()
    client.start()