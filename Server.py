import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc

class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def SendMessage(self, request, context):
        print(f"Mensaje recibido de : {request.message}")
        return chatservice_pb2.MessageResponse(message="Mensaje recibido")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC en ejecución en el puerto 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
