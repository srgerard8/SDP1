import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc
import redis

class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

    def RegisterClient(self, request, context):
        self.redis_client.hset('clients', request.username, request.address)
        print(f"Client registrat: {request.username} a {request.address}")
        return chatservice_pb2.RegisterResponse(message="Registre exitós")

    def GetClients(self, request, context):
        client_list = []
        clients = self.redis_client.hgetall('clients')
        for username, address in clients.items():
            client_list.append(chatservice_pb2.ClientInfo(username=username, address=address))
        return chatservice_pb2.ClientList(clients=client_list)

    def GetChatAddress(self, request, context):
        chat_address = self.redis_client.hget('clients', request.username)
        if chat_address:
            return chatservice_pb2.ChatAddress(address=chat_address)
        else:
            return chatservice_pb2.ChatAddress(address="Chat not found")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Servidor en execució al port 50052")

    # Registro automático de la dirección IP y puerto del servidor al lanzarse
    redis_client = redis.StrictRedis(host='localhost', port=6379)
    server_address = 'localhost:50052'
    redis_client.hset('clients', 'server', server_address)
    print(f"Server address registered: {server_address}")

    server.wait_for_termination()

if __name__ == '__main__':
    serve()