import socket
import threading
import json
import os
from datetime import datetime

class ChatServer:
    def __init__(self, host='127.0.0.1', port=55555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = {}  # {client_socket: {'nickname': nickname, 'room': room}}
        self.rooms = {'general': set()}  # Default room
        self.commands = {
            '/help': self.help_command,
            '/private': self.private_message,
            '/list': self.list_users,
            '/join': self.join_room,
            '/rooms': self.list_rooms
        }

    def broadcast(self, message, room='general', exclude=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        for client in self.clients:
            if client != exclude and self.clients[client]['room'] == room:
                try:
                    client.send(formatted_message.encode('utf-8'))
                except:
                    self.remove_client(client)

    def private_message(self, client, args):
        if len(args) < 2:
            client.send("Usage: /private <nickname> <message>".encode('utf-8'))
            return
            
        target_nick = args[0]
        message = ' '.join(args[1:])
        sender_nick = self.clients[client]['nickname']
        
        target_client = None
        for c in self.clients:
            if self.clients[c]['nickname'] == target_nick:
                target_client = c
                break
                
        if target_client:
            timestamp = datetime.now().strftime("%H:%M:%S")
            target_client.send(f"[{timestamp}] (Private from {sender_nick}): {message}".encode('utf-8'))
            client.send(f"[{timestamp}] (Private to {target_nick}): {message}".encode('utf-8'))
        else:
            client.send(f"User {target_nick} not found.".encode('utf-8'))

    def help_command(self, client, args):
        help_text = """
Available commands:
/help - Show this help message
/private <nickname> <message> - Send private message
/list - List all users in current room
/join <room> - Join or create a room
/rooms - List all active rooms
        """
        client.send(help_text.encode('utf-8'))

    def list_users(self, client, args):
        room = self.clients[client]['room']
        users = [self.clients[c]['nickname'] for c in self.clients 
                if self.clients[c]['room'] == room]
        client.send(f"Users in {room}: {', '.join(users)}".encode('utf-8'))

    def join_room(self, client, args):
        if not args:
            client.send("Usage: /join <room>".encode('utf-8'))
            return
            
        room = args[0]
        old_room = self.clients[client]['room']
        
        if room not in self.rooms:
            self.rooms[room] = set()
            
        self.rooms[old_room].discard(client)
        self.rooms[room].add(client)
        self.clients[client]['room'] = room
        
        self.broadcast(f"{self.clients[client]['nickname']} left the room", old_room)
        self.broadcast(f"{self.clients[client]['nickname']} joined the room", room)

    def list_rooms(self, client, args):
        room_list = [f"{room} ({len(members)} users)" 
                    for room, members in self.rooms.items()]
        client.send(f"Active rooms: {', '.join(room_list)}".encode('utf-8'))

    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                if not message:
                    self.remove_client(client)
                    break
                    
                if message.startswith('/'):
                    parts = message.split()
                    command = parts[0].lower()
                    args = parts[1:] if len(parts) > 1 else []
                    
                    if command in self.commands:
                        self.commands[command](client, args)
                    else:
                        client.send("Unknown command. Type /help for available commands.".encode('utf-8'))
                else:
                    room = self.clients[client]['room']
                    nickname = self.clients[client]['nickname']
                    self.broadcast(f"{nickname}: {message}", room)
            except:
                self.remove_client(client)
                break

    def remove_client(self, client):
        if client in self.clients:
            nickname = self.clients[client]['nickname']
            room = self.clients[client]['room']
            self.rooms[room].discard(client)
            del self.clients[client]
            client.close()
            self.broadcast(f'{nickname} left the chat!', room)

    def start(self):
        print("Server is running...")
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}")

            client.send('NICK'.encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            
            self.clients[client] = {
                'nickname': nickname,
                'room': 'general'
            }
            self.rooms['general'].add(client)

            print(f'Nickname of the client is {nickname}!')
            self.broadcast(f'{nickname} joined the chat!')
            client.send('Connected to the server! Type /help for available commands.'.encode('utf-8'))

            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()

if __name__ == '__main__':
    server = ChatServer()
    server.start()