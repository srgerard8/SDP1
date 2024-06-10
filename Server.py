import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc
import redis

class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        # Es crea una connexió amb el servidor de Redis
        self.redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

    # Métode per registar un client al servidor de noms
    def RegisterClient(self, request, context):
        # Es guarda el client amb el seu nom i adreça
        self.redis_client.hset('clients', request.username, request.address)
        # Missatge de verificació de que s'ha registrat el client correctament
        print(f"Client registrat: {request.username} a {request.address}")
        return chatservice_pb2.RegisterResponse(message="Registre d'usaris exitós")


    # Métode per obtenir la llista de clients registrats
    def GetClients(self, request, context):
        # Creem la llista de clients buida
        client_list = []
        # Obtenim tots els clients de la taula de hash
        clients = self.redis_client.hgetall('clients')
        # Per cada client, afegim el seu nom i adreça a la llista de clients
        for username, address in clients.items():
            client_list.append(chatservice_pb2.ClientInfo(username=username, address=address))
        return chatservice_pb2.ClientList(clients=client_list)

# Métode per crear el servidor
def serve():
    # Creem el servidor
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Afegim el servei de xat al servidor
    chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    # Iniciem el servidor al port 50052
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Servidor en execució al port 50052")

    # Es crea una connexió amb el servidor de Redis
    redis_client = redis.StrictRedis(host='localhost', port=6379)
    # Es fa un delete de la taula de hash per borrar tota la execució anterior per a que no hi hagi conflictes
    redis_client.delete('clients')
    # Es guarda la adreça del servidor al servidor de noms
    server_address = 'localhost:50052'
    # Creem la única taula de hash que hi haurà al servidor de noms
    redis_client.hset('clients', 'server', server_address)
    print(f"Adreça del servidor registrada: {server_address}")

    server.wait_for_termination()

if __name__ == '__main__':
    serve()