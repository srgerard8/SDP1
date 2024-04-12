#!/usr/bin/env python3

nom = ""

def demanar_dades():
    global nom
    print("Benvingut al servei de xats")
    nom = input("Introdueix el teu nom: ")


def mostrar_menu():
    print("Benvingut al servei de xats, " + nom)
    print("1. Connecta el xat")
    print("2. Subscriu-te al xat de grup")
    print("3. Descobreix xats")
    print("4. Accedeix al canal d'insults")
    print("5. Sortir")


def opcio1():
    print("1")


def opcio2():
    print("2")


def opcio3():
    print("3")


def opcio4():
    print("4")


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
            print("Sortint...")
            break
        else:
            print("Opció no valida. Si us plau, elegeix una opció")


if __name__ == "__main__":
    main()
