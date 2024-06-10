import threading
import time
import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc
import pika

# Classe que implementa el servei de xat i que conté el métode per enviar missatges privats entre clients
class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def __init__(self, client):
        self.client = client

    # Métode del gRPC per enviar missatges entre clients
    def SendMessage(self, request, context):
        # Agafem el nom del client que envia el missatge i el cos del missatge
        sender = request.sender
        message = request.message
        # Mostrem el missatge per consola
        print(f"Missatge rebut de {sender}: {message}")
        return chatservice_pb2.MessageResponse(message="Missatge enviat correctament")


class Client:

    def __init__(self, username, port):
        self.username = username
        self.port = port
        self.server = None
        self.channel = grpc.insecure_channel('localhost:50052')
        self.stub = chatservice_pb2_grpc.ChatServiceStub(self.channel)

        # Fem connexió a RabbitMQ amb el port 5672
        self.rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost',
            port=5672,
            virtual_host='/',
            credentials=pika.PlainCredentials('guest', 'guest')
        ))
        self.rabbit_channel = self.rabbit_connection.channel()

    # Métode per mostrar el menú de l'aplicació als clients
    def mostrar_menu(self):
        print("Benvingut al servei de xats, " + self.username)
        print("1. Connecta al xat privat")
        print("2. Connecta al xat de grup")
        print("3. Subscriure's al xat de grup")
        print("4. Descobreix xats")
        print("5. Accedeix al canal d'insults")
        print("6. Sortir")

    # Métode per registrar el client al servidor de noms
    def register(self):
        # Es guarda la adreça del client ip:port
        address = f'localhost:{self.port}'
        # és crida al métode de gRPC per registrar al servidor de noms
        self.stub.RegisterClient(chatservice_pb2.ClientInfo(username=self.username, address=address))

        # Connexió al grup d'esdeveniments per al discover
        self.setup_event_group()

    # Métode per configurar el grup d'esdeveniments (discover)
    def setup_event_group(self):
        exchange_name = 'event_group'
        # Declarem un exchange per al discover
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

        # Creem una cua temporal per a aquest client i la vinculem amb l'exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Funció de callback per rebre els discovers
        def event_callback(ch, method, properties, body):
            print("Discover rebut:", body.decode())

        # Consumim els missatges del grup de discover
        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=event_callback, auto_ack=True)
        print("Conectado al grupo de eventos.")

    # Métode que utilitza una funció de gRPC per obtenir la llista de clients registrats
    def get_clients(self):
        response = self.stub.GetClients(chatservice_pb2.Empty())
        return {client.username: client.address for client in response.clients}

    # Métode per enviar missatges privats entre clients
    def send_message(self, receiver, message):
        # Obtenim la llista de clients
        clients = self.get_clients()
        # Si el receptor està a la llista de clients, enviem el missatge
        if receiver in clients:
            # Agafem la adreça i port del receptor per saber a on hem de dirigir el missatge
            receiver_address = clients[receiver]
            channel = grpc.insecure_channel(receiver_address)
            # Creem un stub per enviar el missatge
            stub = chatservice_pb2_grpc.ChatServiceStub(channel)
            # Enviam el missatge amb el métode de gRPC
            response = stub.SendMessage(chatservice_pb2.MessageRequest(sender=self.username, receiver=receiver, message=message))
            print(f"{response.message}")
        else:
            # Si no trobem el receptor a la llista de clients, mostrem un missatge d'error
            print(f"Client {receiver} no trobat")

    # Métode per iniciar el servidor intern de cada client per a que es puguin rebre els missatges
    def serve(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(self), server)
        # El port del servidor serà el que ha introduït l'usuari al començament
        server.add_insecure_port(f'[::]:{self.port}')
        # S'inicia el servidor
        server.start()
        self.server = server
        print(f"Client servidor gRPC en execució al port {self.port}")

    # Métode per mostrar el menú i gestionar les opcions escollides per l'usuari
    def start(self):
        # Cridem a register per registrar el client al servidor de noms i demanar les credencials
        self.register()
        # Cridem a serve per iniciar el servidor intern de cada client
        self.serve()
        while True:
            # Mostrem el menú
            self.mostrar_menu()
            opcio = input("Elegeix una opció: ")

            # Segons l'opció escollida, cridem a la funció corresponent
            if opcio == "1":
                self.opcio1()
            elif opcio == "2":
                self.opcio2()
            elif opcio == "3":
                self.opcio3()
            elif opcio == "4":
                self.opcio4()
            elif opcio == "5":
                self.opcio5()
            elif opcio == "6":
                print("Sortint...")
                break
            else:
                print("Opció no valida. Si us plau, elegeix una opció")

    # Opció 1: connexió al xat privat
    def opcio1(self):
        # Variable per quan l'usuari vulgui sortir del xat
        sortir = False
        # Demanem el nom del destinatari amb qui es vol connectar el xat
        receiver = input("Introdueix el destinatari amb qui et vols connectar el xat: ")
        print("A continuació, et connectaràs el servei de xat privat. Si vols sortir, introdueix 'sortir'")
        # L'usuari podra introduir missatges fins que vulgui sortir
        while sortir == False:
            message = input("")
            if message == "sortir":
                print("Has sortit del xat")
                sortir = True
            else:
                self.send_message(receiver, message)

    # Opció 2: connexió al xat de grup
    def opcio2(self):
        sortir = False
        # Demanem a l'usuari que posi el nom del grup al que vol connectar-se
        nom_grup = input("Posa el nom del grup al que vols crear o connectar-te: ")
        # Connectem amb aquest exchange en el cas de que ja existeixi i sino es crearà
        exchange_name = f"exchange_{nom_grup}"
        # Cada exchange serà un grup diferent
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
        address = nom_grup
        # Registrem el grup i el seu nom al servidor de noms
        self.stub.RegisterClient(chatservice_pb2.ClientInfo(username=nom_grup, address=address))
        print(f"Connectat al grup {nom_grup}")

        # Creem la cua temporal per a aquest client i la vinculem amb l'exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Cua adicional per desar els missatges
        self.rabbit_channel.queue_declare(queue=f'messages_queue_{nom_grup}')

        # Funció de callback per rebre els missatges
        def callback(ch, method, properties, body):
            # La funció rebrà l'emissor del missatge i el cos del missatge i el mostrarà per consola
            sender = properties.headers['sender']
            message = body.decode()
            if sender != self.username:
                print(f"Missatge rebut de {sender} al grup {nom_grup}: {message}")

        # Consumim els missatges de la cua principal per a poder rebrer els missatges
        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        print(f"Esperant missatges del grup {nom_grup}. Introdueix sortir per sortir.")

        # Executem el consum de missatges en un fil separat
        threads = threading.Thread(target=self.rabbit_channel.start_consuming, daemon=True)
        threads.start()

        # L'usuari podrà introduir missatges fins que vulgui sortir
        while not sortir:
            message = input("")
            if message == "sortir":
                print("Has sortit del xat")
                sortir = True
                self.rabbit_channel.stop_consuming()
                threads.join()
            else:
                # Enviar el mensaje al exchange
                self.rabbit_channel.basic_publish(exchange=exchange_name,
                                                  routing_key='',
                                                  body=message,
                                                  properties=pika.BasicProperties(
                                                      headers={'sender': self.username}
                                                  ))
                # Guardar el mensaje en la cola de mensajes
                self.rabbit_channel.basic_publish(exchange='',
                                                  routing_key=f'messages_queue_{nom_grup}',
                                                  body=message,
                                                  properties=pika.BasicProperties(
                                                      headers={'sender': self.username}
                                                  ))

    # Opció 3: subscriure's al xat de grup
    def opcio3(self):
        sortir = False
        # Demanem a l'usuari que posi el nom del grup al que vol connectar-se
        nom_grup = input("Escriu el nom del grup al que et vols subscriure (o 'sortir' per sortir): ")
        # Si l'usuari vol sortir, sortim de la funció
        if nom_grup.lower() == 'sortir':
            print("Has sortit de l'opció 5.")
            return

        # Delcarem l'exchange per al nom del grup
        exchange_name = f"exchange_{nom_grup}"
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
        address = nom_grup
        # Registrem el grup al servidor de noms
        self.stub.RegisterClient(chatservice_pb2.ClientInfo(username=nom_grup, address=address))
        print(f"Conectat al grup {nom_grup}")

        # Creem una cua temporal per a aquest client i la vinculem amb l'exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True, auto_delete=False)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Cua adicional per a poder emmagatzemar els missatges
        messages_queue_name = f'messages_queue_{nom_grup}'
        self.rabbit_channel.queue_declare(queue=messages_queue_name, auto_delete=False)

        # Comptador de missatges per a poder saber quants missatges hi ha i així poder imprimir només els parells
        message_counter = 0

        # Funció de callback per a poder rebre els missatges emmagatzemats a la cua
        def callback(ch, method, properties, body):
            # Només imprimirem els missatges parells ja que estàn duplicats
            nonlocal message_counter
            sender = properties.headers['sender']
            message = body.decode()
            if sender != self.username:
                if message_counter % 2 == 0:
                    print(f"Missatge rebut de {sender} al grup {nom_grup}: {message}")
                message_counter += 1

        # Consumir missatges de la cua principal
        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

        # Consumir missatges de la cua de missatges emmagatzemats
        self.rabbit_channel.basic_consume(queue=messages_queue_name, on_message_callback=callback, auto_ack=True)

        print(f"Esperant missatges del grup {nom_grup}. Introdueix 'sortir' para sortir.")

        # Executar el consum de missatges en un fil separat
        threads = threading.Thread(target=self.rabbit_channel.start_consuming, daemon=True)
        threads.start()

        # L'usuari podrà introduir missatges fins que vulgui sortir
        while not sortir:
            message = input("")
            if message == "sortir":
                print("Has sortit del xat.")
                sortir = True
                self.rabbit_channel.stop_consuming()
                threads.join()
            else:
                # Enviar el mensaje al exchange
                self.rabbit_channel.basic_publish(exchange=exchange_name,
                                                  routing_key='',
                                                  body=message,
                                                  properties=pika.BasicProperties(
                                                      headers={'sender': self.username}
                                                  ))
                # Guardar el mensaje en la cola de mensajes
                self.rabbit_channel.basic_publish(exchange='',
                                                  routing_key=messages_queue_name,
                                                  body=message,
                                                  properties=pika.BasicProperties(
                                                      headers={'sender': self.username}
                                                  ))

    # Opció 4: descobreix xats
    def opcio4(self):
        # Enviar la solicitut de discover al grup creat anteriorment d'esdeveniments
        exchange_name = 'event_group'
        # Declarem un exchange per al discover
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
        self.rabbit_channel.basic_publish(exchange=exchange_name,
                                          routing_key='',
                                          body=f"Solicitut de discover de {self.username}")

        # Creem una cua temporal per a poder rebre respostes i l'enllaçem amb l'exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Funció de callback per a poder rebre els missatges
        def callback(ch, method, properties, body):
            sender = properties.headers['sender']
            print(f"Resposta de discover de {sender}: {body.decode()}")

        # Ens subscribim a la cua temporal per a poder rebre les respostes
        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

        # Iniciem la escolta de respostes en un fil separat
        threads = threading.Thread(target=self.rabbit_channel.start_consuming, daemon=True)
        threads.start()

        # Esperem un temps de 10 segons per a poder rebre les respostes
        time.sleep(10)

        # Parem la escolta de respostes i tanquem el fil
        self.rabbit_channel.stop_consuming()
        threads.join()

    def opcio5(self):
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

        # L'usuari podrà introduir missatges fins que vulgui sortir
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
    # Demanem credencials del usuari nom i port
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
            # Verifiquem si el port es correcte i no està en ús
            portisnumeric = port.isnumeric()
            if portisnumeric:
                if f'localhost:{port}' in all_clients.values():
                    print("Aquest port ja està en ús. Elegeix un altre port")
                else:
                    break
            else:
                print("El port ha de ser un nombre enter no negatiu")
    client.start()
