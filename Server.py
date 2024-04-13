import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc
from collections import defaultdict


class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = defaultdict(list)  # Almacena las conexiones de los clientes

    def SendMessage(self, request, context):
        sender = context.peer()  # Obtiene la dirección del remitente
        receiver = request.receiver
        message = request.message
        print(f"Mensaje enviado de {sender} a {receiver}: {message}")

        # Encuentra al cliente destinatario y envía el mensaje
        if receiver in self.clients:
            for client in self.clients[receiver]:
                client.SendMessage(chatservice_pb2.MessageRequest(sender=sender, receiver=receiver, message=message))
            return chatservice_pb2.MessageResponse(message="Mensaje enviado al destinatario")
        else:
            return chatservice_pb2.MessageResponse(message=f"No se pudo entregar el mensaje a {receiver}")

    def ReceiveMessage(self, request, context):
        sender = request.sender
        message = request.message
        print(f"Mensaje recibido de {sender}: {message}")
        return chatservice_pb2.MessageResponse(message="Mensaje recibido")

    def Connect(self, request, context):
        username = request.username
        self.clients[username].append(context)
        print(f"Cliente {username} conectado")
        return chatservice_pb2.ConnectResponse(message=f"Bienvenido al servidor, {username}")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC en ejecución en el puerto 50051")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
