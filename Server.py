import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc
from collections import defaultdict

class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = defaultdict(list)

    def SendMessage(self, request, context):
        sender = context.peer()
        receiver = request.receiver
        message = request.message
        print(f"Missatge enviat de {sender} a {receiver}: {message}")

        if receiver in self.clients:
            for client in self.clients[receiver]:
                channel = grpc.insecure_channel(client.peer())
                client_stub = chatservice_pb2_grpc.ChatServiceStub(channel)
                client_stub.ReceiveMessage(chatservice_pb2.MessageRequest(sender=sender, receiver=receiver, message=message))
                #client.SendMessage(chatservice_pb2.MessageRequest(sender=sender, receiver=receiver, message=message))
            return chatservice_pb2.MessageResponse(message="Missatge enviat al destinatari")
        else:
            return chatservice_pb2.MessageResponse(message=f"No s'ha pogut entregar el missatge {receiver}")

    def ReceiveMessage(self, request, context):
        sender = request.sender
        message = request.message
        print(f"Missatge rebut de {sender}: {message}")
        return chatservice_pb2.MessageResponse(message="Missatge rebut")

    def Connect(self, request, context):
        username = request.username
        self.clients[username].append(context)
        print(f"Client {username} conectat al servidor")
        return chatservice_pb2.ConnectResponse(message=f"Bienvengut al servidor, {username}")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC en ejecución en el puerto 50051")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
