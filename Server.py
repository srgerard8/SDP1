import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc

class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = {}

    def RegisterClient(self, request, context):
        self.clients[request.username] = request.address
        print(f"Client registrat: {request.username} a {request.address}")
        return chatservice_pb2.RegisterResponse(message="Registre exitós")

    def GetClients(self, request, context):
        client_list = [chatservice_pb2.ClientInfo(username=username, address=address) for username, address in self.clients.items()]
        return chatservice_pb2.ClientList(clients=client_list)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Servidor en execució al port 50052")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()