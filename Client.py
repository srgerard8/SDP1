#!/usr/bin/env python3
import multiprocessing
import threading

import grpc

import chatservice_pb2
import chatservice_pb2_grpc  # Importa tu archivo .proto generado

nom = ""


class Client:

    def __init__(self, nom2):
        self.nom = nom2
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = chatservice_pb2_grpc.ChatServiceStub(self.channel)

    def receive_messages(self, request):
        try:
            for response in self.stub.ReceiveMessage(
                    chatservice_pb2.MessageRequest(request)):
                print(f"Mensaje recibido: De {response.sender}: {response.message}")
        except grpc.RpcError as e:
            print(f"Error al recibir mensajes: {e}")

    def getStub(self):
        return self.stub

    def demanar_dades(self):
        global nom
        print("Benvingut al servei de xats")
        nom = input("Introdueix el teu nom: ")
        self.stub.Connect(chatservice_pb2.ConnectRequest(username=nom))

    def mostrar_menu(self):
        print("Benvingut al servei de xats, " + nom)
        print("1. Connecta el xat")
        print("2. Subscriu-te al xat de grup")
        print("3. Descobreix xats")
        print("4. Accedeix al canal d'insults")
        print("5. Mostrar missatges rebuts")
        print("6. Sortir")

    def opcio1(self):
        print("1")
        global nom
        message = input("Introdueix el missatge: ")
        receiver = input("A qui li vols enviar el missatge?  ")
        nom2 = nom
        response = self.stub.SendMessage(
            chatservice_pb2.MessageRequest(sender=nom2, receiver=receiver, message=message))
        #print(response.message)

    def opcio2(self):
        print("2")

    def opcio3(self):
        print("3")

    def opcio4(self):
        print("4")

    def opcio5(self, client):
        print("5")
        receive_thread = threading.Thread(target=client.receive_messages, daemon=True)
        receive_thread.start()

        while True:
            receiver = input("Introduce el destinatario del mensaje: ")
            message = input("Introduce el mensaje: ")
            client.send_message(receiver, message)

    def start(self):
        global nom
        self.demanar_dades()

        while True:
            self.mostrar_menu()
            opcio = input("Elegeix una opció: ")

            if opcio == "1":
                print("Has elegit Connecta el xat")
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
                print("Has elegit Mostrar missatges rebuts")
                self.opcio5(client)
            elif opcio == "6":
                print("Sortint...")
                break
            else:
                print("Opció no valida. Si us plau, elegeix una opció")


if __name__ == "__main__":
    client = Client(nom)
    client.start()
    # Crea los procesos para cada cliente
#    proceso_cliente1 = threading.Thread(target=main())
#    proceso_cliente2 = threading.Thread(target=main())

# Inicia los procesos
#    proceso_cliente1.start()
#    proceso_cliente2.start()

# Espera a que los procesos terminen
#    proceso_cliente1.join()
#    proceso_cliente2.join()
