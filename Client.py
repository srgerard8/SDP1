import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc

class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def __init__(self, client):
        self.client = client

    def SendMessage(self, request, context):
        sender = request.sender
        message = request.message
        print(f"Missatge rebut de {sender}: {message}")
        return chatservice_pb2.MessageResponse(message="Missatge enviat correctament")


class Client:

    def __init__(self, username, port):
        self.username = username
        self.port = port
        self.server = None
        self.channel = grpc.insecure_channel('localhost:50052')
        self.stub = chatservice_pb2_grpc.ChatServiceStub(self.channel)

    def mostrar_menu(self):
        print("Benvingut al servei de xats, " + self.username)
        print("1. Connecta al xat")
        print("2. Subscriu-te al xat de grup")
        print("3. Descobreix xats")
        print("4. Accedeix al canal d'insults")
        print("5. Sortir")

    def register(self):
        address = f'localhost:{self.port}'
        self.stub.RegisterClient(chatservice_pb2.ClientInfo(username=self.username, address=address))

    def get_clients(self):
        response = self.stub.GetClients(chatservice_pb2.Empty())
        return {client.username: client.address for client in response.clients}

    def send_message(self, receiver, message):
        clients = self.get_clients()
        if receiver in clients:
            receiver_address = clients[receiver]
            channel = grpc.insecure_channel(receiver_address)
            stub = chatservice_pb2_grpc.ChatServiceStub(channel)
            response = stub.SendMessage(chatservice_pb2.MessageRequest(sender=self.username, receiver=receiver, message=message))
            print(f"{response.message}")
        else:
            print(f"Client {receiver} no trobat")

    def serve(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(self), server)
        server.add_insecure_port(f'[::]:{self.port}')
        server.start()
        self.server = server
        print(f"Client servidor gRPC en execució al port {self.port}")

    def start(self):
        self.register()
        self.serve()
        while True:
            self.mostrar_menu()
            opcio = input("Elegeix una opció: ")

            if opcio == "1":
                print("Has elegit Connecta al xat")
                self.opcio1()
            elif opcio == "2":
                print("Has elegit Subscriu-te al xat de grup")
                self.opcio2()
            elif opcio == "3":
                print("Has elegit Descobreix xats")
                self.opcio3()
            elif opcio == "4":
                print("Has elegit Accedeix al canal d'insults")
                self.opcio4()
            elif opcio == "5":
                print("Sortint...")
                break
            else:
                print("Opció no valida. Si us plau, elegeix una opció")

    def opcio1(self):
        sortir = False
        receiver = input("Introdueix el destinatari amb qui et vols connectar el xat: ")
        print("A continuació, et connectaràs el servei de xat privat. Si vols sortir, introdueix 'sortir'")
        while sortir == False:
            message = input("")
            if message == "sortir":
                print("Has sortit del xat")
                sortir = True
            else:
                self.send_message(receiver, message)

    def opcio2(self):
        print("2")

    def opcio3(self):
        print("3")

    def opcio4(self):
        print("4")


if __name__ == "__main__":
    username = input("Introdueix el teu nom: ")
    port = input("Introdueix el port en que vols executar aquest client: ")
    client = Client(username, port)
    client.start()

