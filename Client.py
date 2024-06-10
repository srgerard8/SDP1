import threading
import grpc
from concurrent import futures
import chatservice_pb2
import chatservice_pb2_grpc
import pika

class ChatService(chatservice_pb2_grpc.ChatServiceServicer):
    def __init__(self, client):
        self.client = client

    # Mètode de gRPC per a poder enviar missatges
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
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.rabbit_channel = self.connection.channel()
        self.stub = chatservice_pb2_grpc.ChatServiceStub(self.channel)
        self.setup_discovery_listener()

        # Connexió a RabbitMQ
        self.rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost',
            port=5672,
            virtual_host='/',
            credentials=pika.PlainCredentials('guest', 'guest')
        ))
        self.rabbit_channel = self.rabbit_connection.channel()

    # Mètode per mostrar el menú
    def mostrar_menu(self):
        print("Benvingut al servei de xats, " + self.username)
        print("1. Connectar-se a un xat privat")
        print("2. Connectar-se a un xat grupal")
        print("3. Subscriure's a un xat de grup")
        print("4. Descobrir usuaris")
        print("5. Connectar-se al canal d'insults")
        print("6. Sortir")

    # Mètode que crida a la funció del server.py per registrar els clients amb les seves credencials
    def register(self):
        address = f'localhost:{self.port}'
        self.stub.RegisterClient(chatservice_pb2.ClientInfo(username=self.username, address=address))

        # Connexió al grup d'esdeveniments per al discovery
        self.setup_event_group()

    # Mètode per configurar el grup d'esdeveniments
    def setup_event_group(self):
        # El nom de l'exchange és 'event_group'
        exchange_name = 'event_group'
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

        # Declararem una cua temporal per a aquest client i enllaçar-la amb l'exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Funció de callback per a poder rebre els missatges
        def event_callback(ch, method, properties, body):
            print("Esdeveniment de discover rebut:", body.decode())

        # Consumir els missatges de l'exchange
        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=event_callback, auto_ack=True)
        print("Connectat al grup d'esdeveniments.")

    # Mètode per obtenir una llista amb tots els clients
    def get_clients(self):
        # S'utilitza el mètode GetClients de gRPC
        response = self.stub.GetClients(chatservice_pb2.Empty())
        return {client.username: client.address for client in response.clients}

    # Mètode per enviar missatges a un client
    def send_message(self, receiver, message):
        # Obtenim una llista amb tots els clients
        clients = self.get_clients()
        # Comprovem si el client al que volem enviar el missatge està a la llista
        if receiver in clients:
            # Si ho està obtenim la seva adreça i creem un canal gRPC
            receiver_address = clients[receiver]
            channel = grpc.insecure_channel(receiver_address)
            # També creem un stub per a poder cridar a SendMessage
            stub = chatservice_pb2_grpc.ChatServiceStub(channel)
            # Enviem el missatge cridant al mètode de gRPC
            response = stub.SendMessage(chatservice_pb2.MessageRequest(sender=self.username, receiver=receiver, message=message))
            print(f"{response.message}")
        else:
            # Si el client no està a la llista mostrem un missatge d'error
            print(f"Client {receiver} no trobat")

    # Mètode per a crear el servidor intern dins del client per a poder rebre els missatges
    def serve(self):
        # Creem el servidor
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chatservice_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(self), server)
        # L'assignem al port que ha escollit l'usuari al començament
        server.add_insecure_port(f'[::]:{self.port}')
        # Iniciem el servidor al port escollit
        server.start()
        self.server = server
        print(f"Client servidor gRPC en execució al port {self.port}")

    # Métode per a consumir missatges
    def _consume_messages(self, channel):
        # Comprovem si el canal està obert
        try:
            if channel.is_open:
                # Si ho està comencem a consumir missatges
                channel.start_consuming()
        except Exception as e:
            # sino llençem excepció
            print(f"Error durant el consum de missatges: {e}")

    # Mètode per a configurar el listener del discover
    def setup_discovery_listener(self):
        # Crear l'exchange de descobriment
        discovery_exchange = 'discovery_exchange'
        self.rabbit_channel.exchange_declare(exchange=discovery_exchange, exchange_type='fanout')

        # Crear una cua temporal per a aquest client i enllaçar-la amb l'exchange del discover
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=discovery_exchange, queue=queue_name)

        # Funció per a respondre el discover
        def respond_to_discovery(ch, method, properties, body):
            # Si el missatge és una sol·licitud de discover, respon amb el nom d'usuari i el port
            if body.decode() == 'DISCOVERY_REQUEST':
                # Es crea la resposta amb el nom d'usuari i el port
                response = f"{self.username},{self.port}"
                self.rabbit_channel.basic_publish(exchange=discovery_exchange,
                                                  routing_key='',
                                                  body=response,
                                                  properties=pika.BasicProperties(
                                                      headers={'sender': self.username},
                                                      delivery_mode=2  # Fa que el missatge sigui persistent
                                                  ))

        # Consumir els missatges de l'exchange de discover
        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=respond_to_discovery, auto_ack=True)
        threading.Thread(target=self._consume_messages, args=(self.rabbit_channel,), daemon=True).start()

    # Mètode per a iniciar el client
    def start(self):
        # Cridem a register per a poder obtenir les credencials
        self.register()
        # Cridem a serve per a poder crear el servidor intern i poder rebre els missatges
        self.serve()
        while True:
            # Mostrem el menú
            self.mostrar_menu()
            opcio = input("Escull una opció: ")

            # Comprovem quina opció ha escollit l'usuari
            if opcio == "1":
                print("Has escollit connectar-te a un xat privat")
                self.opcio1()
            elif opcio == "2":
                print("Has escollit connectar-te a un xat grupal")
                self.opcio2()
            elif opcio == "3":
                print("Has escollit subscriure't a un xat de grup")
                self.opcio3()
            elif opcio == "4":
                print("Has escollit descobrir usuaris")
                self.opcio4()
            elif opcio == "5":
                self.opcio5()
                print("Has escollit accedir al canal d'insults")
            elif opcio == "6":
                print("Sortint...")
                break
            else:
                print("Opció no vàlida. Si us plau, escull una opció")

    # Opció 1: Connectar-se a un xat privat
    def opcio1(self):
        # Variables per a sortir del bucle
        sortir = False
        # Demanem el destinatari a qui es vol connectar
        receiver = input("Introdueix el destinatari amb qui et vols connectar al xat: ")
        print("A continuació, et connectaràs al servei de xat privat. Si vols sortir, introdueix 'sortir'")
        # Si l'usuari vol sortir, introduirà 'sortir'
        while sortir == False:
            message = input("")
            if message == "sortir":
                print("Has sortit del xat")
                sortir = True
            else:
                self.send_message(receiver, message)

    # Opció 2: Connectar-se a un xat grupal
    def opcio2(self):
        sortir = False
        # Demanar el nom del grup al que es vol connectar
        nom_grup = input("Posa el nom del grup al que vols crear o connectar-te: ")
        # Crear un exchange amb el nom del grup
        exchange_name = f"exchange_{nom_grup}"

        # Assegurar-se que el canal estigui obert abans de continuar
        if not self.rabbit_channel.is_open:
            self.rabbit_channel = self.connection.channel()

        # Crear un exchange amb el nom del grup
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
        # Guardar el nom del grup com a adreça
        address = nom_grup
        # Registrarem el grup al servidor de noms
        self.stub.RegisterClient(chatservice_pb2.ClientInfo(username=nom_grup, address=address))
        print(f"Connectat al grup {nom_grup}")

        # Crear una cua temporal per a aquest client i enllaçar-la amb l'exchange
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=queue_name)


        messages_queue_name = f'messages_queue_{self.username}_{nom_grup}'
        self.rabbit_channel.queue_declare(queue=messages_queue_name, durable=True)

        # Llegir i mostrar missatges emmagatzemats a la cua duradora, i eliminar-los després
        while True:
            method_frame, header_frame, body = self.rabbit_channel.basic_get(messages_queue_name, auto_ack=False)
            if method_frame:
                sender = header_frame.headers['sender']
                message = body.decode()
                if sender != self.username:
                    print(f"Missatge antic de {sender}: {message}")
                self.rabbit_channel.basic_ack(method_frame.delivery_tag)  # Confirmar recepció del missatge
            else:
                break

        # Desvincular la cua persistent mentre l'usuari està connectat
        self.rabbit_channel.queue_unbind(exchange=exchange_name, queue=messages_queue_name)

        # Funció de callback per rebre els missatges
        def callback(ch, method, properties, body):
            sender = properties.headers['sender']
            message = body.decode()
            if sender != self.username:
                print(f"Missatge rebut de {sender}: {message}")

        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        print(f"Esperant missatges del grup {nom_grup}. Introdueix sortir per sortir.")

        self.is_connected = True  # L'usuari està connectat
        thread = threading.Thread(target=self._consume_messages, args=(self.rabbit_channel,), daemon=True)
        thread.start()

        # Bucle per enviar missatges al grup
        while not sortir:
            message = input("")
            if message == "sortir":
                print("Has sortit del xat")
                sortir = True
                self.is_connected = False  # L'usuari es desconnecta
                try:
                    self.rabbit_channel.stop_consuming()
                except Exception as e:
                    print(f"Error al detindre el consum: {e}")
                thread.join()

                # Tornar a vincular la cua persistent quan l'usuari es desconnecta
                self.rabbit_channel.queue_bind(exchange=exchange_name, queue=messages_queue_name)
            else:
                # Enviar el missatge a l'exchange
                self.rabbit_channel.basic_publish(exchange=exchange_name,
                                                  routing_key='',
                                                  body=message,
                                                  properties=pika.BasicProperties(
                                                      headers={'sender': self.username},
                                                      delivery_mode=2  # Fa que el missatge sigui persistent
                                                  ))


    # Opció 3: Subscriure's a un xat de grup
    def opcio3(self):
        nom_grup = input("Posa el nom del grup al que vols subscriure't: ")
        exchange_name = f"exchange_{nom_grup}"
        self.rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

        # Crear una cua temporal per a aquest client i enllaçar-la amb l'exchange
        messages_queue_name = f'messages_queue_{self.username}_{nom_grup}'
        self.rabbit_channel.queue_declare(queue=messages_queue_name, durable=True)
        # Llegir i mostrar missatges emmagatzemats a la cua duradora, i eliminar-los després
        self.rabbit_channel.queue_bind(exchange=exchange_name, queue=messages_queue_name)

        print(f"Subscrit al grup {nom_grup}. Els missatges es guardaran mentre no estiguis connectat.")


    def opcio4(self):
        discovery_exchange = 'discovery_exchange'
        self.rabbit_channel.exchange_declare(exchange=discovery_exchange, exchange_type='fanout')

        # Crear una cua temporal per a aquest client i enllaçar-la amb l'exchange de descobriment
        result = self.rabbit_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.rabbit_channel.queue_bind(exchange=discovery_exchange, queue=queue_name)

        # Funció de callback per processar els missatges de discover
        def discovery_callback(ch, method, properties, body):
            # Processar el missatge de discover rebut
            try:
                username, port = body.decode().split(',')
                if username != self.username:  # Omet el propi nom d'usuari
                    print(f"Usuari actiu: {username}, Port: {port}")
            except ValueError:
                print(f"Error al processar el missatge de descobriment: {body.decode()}")

        self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=discovery_callback, auto_ack=True)

        # Publicar un esdeveniment de discover
        self.rabbit_channel.basic_publish(exchange=discovery_exchange,
                                          routing_key='',
                                          body='DISCOVERY_REQUEST',
                                          properties=pika.BasicProperties(
                                              headers={'sender': self.username},
                                              delivery_mode=2  # Fa que el missatge sigui persistent
                                          ))

        print("Esperant respostes dels usuaris actius...")

        # Esperar un temps per rebre respostes
        try:
            thread = threading.Thread(target=self._consume_messages, args=(self.rabbit_channel,), daemon=True)
            thread.start()
            thread.join(timeout=5)  # Esperar 5 segons per rebre respostes
        except Exception as e:
            print(f"Error durant el consum de missatges: {e}")
        finally:
            if self.rabbit_channel.is_open:
                try:
                    self.rabbit_channel.stop_consuming()
                except Exception as e:
                    print(f"Error al detindre el consum: {e}")

    # Opció 5: Connectar-se al canal d'insults
    def opcio5(self):
        sortir = False
        queue_name = 'insult_channel'  # Nom de la cua compartida per al canal d'insults

        # Funció per reconnectar-se al canal d'insults
        def reconnect():
            # Intentem reconnectar al canal d'insults
            try:
                self.rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
                self.rabbit_channel = self.rabbit_connection.channel()
                self.rabbit_channel.queue_declare(queue=queue_name)
            except Exception as e:
                print(f"Error al reconnectar: {e}")

        # Inicialment intentem connectar
        reconnect()
        print(f"Connectat al canal d'insults {queue_name}")

        # Funció de callback per manejar els missatges rebuts
        def callback(ch, method, properties, body):
            print(f"Missatge: {body.decode()}")

        # Funció per a consumir missatges del canal d'insults
        def start_consuming():
            try:
                self.rabbit_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
                self.rabbit_channel.start_consuming()
            except pika.exceptions.StreamLostError as e:
                print(f"Connexió perduda: {e}")
                reconnect()

        print(f"Esperant missatges del canal d'insults. Escriu 'sortir' per sortir.")

        # Executar el consum de missatges en un fil separat
        threads = threading.Thread(target=start_consuming, daemon=True)
        threads.start()

        # Bucle per enviar missatges al canal d'insults
        while sortir == False:
            message = input("")
            if message == "sortir":
                print("Has sortit del canal d'insults")
                sortir = True
                self.rabbit_channel.stop_consuming()
                threads.join()
            else:
                try:
                    self.rabbit_channel.basic_publish(exchange='',
                                                      routing_key=queue_name,
                                                      body=message)
                except pika.exceptions.StreamLostError as e:
                    print(f"Connexió perduda durant l'enviament del missatge: {e}")
                    reconnect()


if __name__ == "__main__":
    while True:
        username = input("Introdueix el teu nom: ")
        port = input("Introdueix el port en que vols executar aquest client: ")

        client = Client(username, port)

        # obtenim tots els clients
        all_clients = client.get_clients()

        # Verifiquem si exixteix el nom d'usuari
        if username in all_clients:
            print("Aquest nom ja està en ús. Escull un altre nom d'usuari")
        else:
            break
    client.start()
