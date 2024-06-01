import threading
import time
import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc
import pika

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

        # Conexión a RabbitMQ
        self.rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost',
            port=5672,
            virtual_host='/',
            credentials=pika.PlainCredentials('guest', 'guest')
        ))
        self.rabbit_channel = self.rabbit_connection.channel()


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

        # Conexión al grupo de eventos
        self.setup_event_group()

    def setup_event_group(self):
        exchange_name = 'event_group'
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

        # Declarar una cola temporal para este cliente y enlazarla con el exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        def event_callback(ch, method, properties, body):
            print("Evento de descubrimiento recibido:", body.decode())
            # Lógica para manejar eventos de descubrimiento

        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=event_callback, auto_ack=True)
        print("Conectado al grupo de eventos.")
    def get_clients(self):
        response = self.stub.GetClients(chatservice_pb2.Empty())
        return {client.username: client.address for client in response.clients}

    def subscribe_to_event_channel(self):
        exchange_name = 'event_group'
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

        # Declarar una cola temporal para este cliente y enlazarla con el exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        def event_callback(ch, method, properties, body):
            print("Evento de descubrimiento recibido:", body.decode())
            # Lógica para manejar eventos de descubrimiento

        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=event_callback, auto_ack=True)
        print("Conectado al grupo de eventos.")
        self.rabbit_channel.start_consuming()

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

        sortir = False
        nom_grup = input("Posa el nom del grup al que vols crear o connectar-te: ")
        exchange_name = f"exchange_{nom_grup}"
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
        address = nom_grup
        self.stub.RegisterClient(chatservice_pb2.ClientInfo(username=nom_grup, address=address))
        print(f"Connectat al grup {nom_grup}")

        # Crear una cola temporal para este cliente y enlazarla con el exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        def callback(ch, method, properties, body):
            sender = properties.headers['sender']
            if (sender != self.username):
                print(f"Missatge rebut de {sender} al grup {nom_grup}: {body.decode()}")

        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        print(f"Esperant missatges del grup {nom_grup}. Introdueix sortir per sortir.")

        threads = (threading.Thread(target=self.rabbit_channel.start_consuming, daemon=True))
        threads.start()

        while sortir == False:
            message = input("")
            if message == "sortir":
                print("Has sortit del xat")
                sortir = True
                self.rabbit_channel.stop_consuming()
                threads.join()
              #  self.rabbit_connection.close()
            else:
                self.rabbit_channel.basic_publish(exchange=exchange_name,
                                                  routing_key='',
                                                  body=message,
                                                  properties = pika.BasicProperties(
                                                    headers={'sender': self.username}
                                                  )
                )

    def opcio3(self):
        # Enviar solicitud de descubrimiento al grupo de eventos
        exchange_name = 'event_group'
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
        self.rabbit_channel.basic_publish(exchange=exchange_name,
                                          routing_key='',
                                          body=f"Solicitud de descubrimiento de {self.username}")

        # Crear una cola temporal para recibir respuestas
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Función de callback para manejar las respuestas recibidas
        def callback(ch, method, properties, body):
            sender = properties.headers['sender']
            print(f"Respuesta de descubrimiento de {sender}: {body.decode()}")

        # Suscribirse a la cola temporal para recibir respuestas
        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

        # Iniciar la escucha de respuestas en un hilo separado
        threads = threading.Thread(target=self.rabbit_channel.start_consuming, daemon=True)
        threads.start()

        # Esperar un tiempo para que se reciban las respuestas
        time.sleep(10)  # Puedes ajustar este tiempo según sea necesario

        # Detener la escucha y limpiar la conexión
        self.rabbit_channel.stop_consuming()
        threads.join()
       # self.rabbit_connection.close()

    def opcio4(self):
        sortir = False
        queue_name = 'insult_channel'  # Nom de la cua compartida per al canal d'insults
        self.rabbit_channel.queue_declare(queue=queue_name)
        print(f"Connectat al canal d'insults {queue_name}")

        # Funció de callback per manejar els missatges rebuts
        def callback(ch, method, properties, body):
            print(f"Missatge rebut del canal d'insults: {body.decode()}")

        # Subscripció a la cua del grup
        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

        print(f"Esperant missatges del canal d'insults. Escriu 'sortir' per sortir.")

        # Executar el consum de missatges en un fil separat
        threads = threading.Thread(target=self.rabbit_channel.start_consuming, daemon=True)
        threads.start()

        while sortir == False:
            message = input("")
            if message == "sortir":
                print("Has sortit del canal d'insults")
                sortir = True
                self.rabbit_channel.stop_consuming()
                threads.join()
            else:
                self.rabbit_channel.basic_publish(exchange='',
                                                  routing_key=queue_name,
                                                  body=message)

if __name__ == "__main__":
    while True:
        username = input("Introdueix el teu nom: ")
        port = input("Introdueix el port en que vols executar aquest client: ")

        client = Client(username, port)

        # obtenim tots els clients
        all_clients = client.get_clients()

        # Verifiquem si exixteix el nom d'usuari
        if username in all_clients:
            print("Aquest nom ja està en ús. Elegeix un altre nom d'usuari")
        else:
            break
    client.start()
