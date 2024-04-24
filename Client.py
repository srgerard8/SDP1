#!/usr/bin/env python3
import multiprocessing
import threading

import grpc

import chatservice_pb2
import chatservice_pb2_grpc # Importa tu archivo .proto generado

nom = ""
channel = grpc.insecure_channel('localhost:50051')
stub = chatservice_pb2_grpc.ChatServiceStub(channel)

def getStub():
    return stub

def demanar_dades():
    global nom
    print("Benvingut al servei de xats")
    nom = input("Introdueix el teu nom: ")
    stub.Connect(chatservice_pb2.ConnectRequest(username=nom))

def mostrar_menu():
    print("Benvingut al servei de xats, " + nom)
    print("1. Connecta el xat")
    print("2. Subscriu-te al xat de grup")
    print("3. Descobreix xats")
    print("4. Accedeix al canal d'insults")
    print("5. Mostrar missatges rebuts")
    print("6. Sortir")



def opcio1():
    print("1")
    global nom
    message = input("Introdueix el missatge: ")
    receiver = input("A qui li vols enviar el missatge?  ")
    nom2 = nom
    response = stub.SendMessage(chatservice_pb2.MessageRequest(sender=nom2, receiver=receiver, message=message))
    print(response.message)

def opcio2():
    print("2")


def opcio3():
    print("3")


def opcio4():
    print("4")

def opcio5():
    print("5")
    receptor = input("Introdueix de qui vols llegir els missatges: ")
    response = stub.ReceiveMessage(chatservice_pb2.MessageRequest(sender=nom, receiver=receptor, message="ola"))
    print(response.message)

def main():
    demanar_dades()
    while True:
        mostrar_menu()
        opcio = input("Elegeix una opció: ")

        if opcio == "1":
            print("Has elegit Connecta el xat")
            opcio1()
        elif opcio == "2":
            print("Has elegit Subscriu-te al xat de grup")
            opcio2()
        elif opcio == "3":
            print("Has elegit Descobreix xats")
            opcio3()
        elif opcio == "4":
            print("Has elegit Accedeix al canal d'insults")
            opcio4()
        elif opcio == "5":
            print("Has elegit Mostrar missatges rebuts")
            opcio5()
        elif opcio == "6":
            print("Sortint...")
            break
        else:
            print("Opció no valida. Si us plau, elegeix una opció")


if __name__ == "__main__":
    main()
    # Crea los procesos para cada cliente
#    proceso_cliente1 = threading.Thread(target=main())
#    proceso_cliente2 = threading.Thread(target=main())

    # Inicia los procesos
#    proceso_cliente1.start()
#    proceso_cliente2.start()

    # Espera a que los procesos terminen
#    proceso_cliente1.join()
#    proceso_cliente2.join()
