# Readme Sistemes Distribuïts Pràctica 1
## Visió General del Projecte
**Equip**: Gerard Altadill i Pol Regy.

El nostre projecte es basa en un sistema de xats que permet als usuaris connectar-se a un servidor per comunicar-se entre ells. Els usuaris poden enviar missatges a tots els altres usuaris connectats o optar per missatges privats a un destinatari específic. També tenen la possibilitat de connectar-se i desconnectar-se del servidor en qualsevol moment. 

Els xats privats s'implementen mitjançant el middleware gRPC. Mentre que pels xats de grup s'utilitza un sistema d'exchanges de RabbitMQ. Adicionalment també s'usa el sistema de cues de rabbitMQ per implementar un canal d'insult que es basarà en unsultar a un usuari aleatori connectat a la plataforma.

## Funcionament del programa i passos per executa'l

Abans de tot, cal tenir instal·lat el docker, el redis, el rabbitMQ, els paquets python3, el pip, el pika i el gRPC. 

En primer lloc, executem l'start-server.bat i l'start-client.bat. L'start-server.bat iniciarà el servidor de noms de redis utilitzant el port 6379 juntament amb el servidor del docker de rabbitMQ al port 5672. Aquest script només es podrà executar una vegada ja que només podem tenir permés obrir un servidor. L'start-client.bat únicament iniciarà un client, aquest script es pot utilitzar tantes vegades com es vulgui per obrir els clients que siguin precissos.

IMPORTANT: Dins d'aquests dos fitxers .bat, s'haurà d'introduïr el camí absolut de la ubicació dels fitxers .py i el .proto, és a dir, el camí absolut de la carpeta on es troba aquest projecte.

Un cop tenim el servidor i els clients oberts, podrem començar a utilitzar el nostre sistema de xat. En el servidor no haurem de tocar res ja que estarà tot inicialitzat, només verificarem que no hi hagi cap inconvenient. Els usuaris podran connectar-se al servidor introduint el seu nom d'usuari i el seu port. Un cop introduïdes les dades el servidor connectarà amb el redis per desar les seves credencials i a continuació, a l'usuari se li apareixerà un menú amb les següents opcions:

1. Connectar-se al xat privat
2. Connectar-se al xat de grup
3. Subscriure's al xat de grup
4. Descobreix xats
5. Accedeix al canal d'insults
6. Sortir

Si volguessim xatejar amb un client en privat, haurem de seleccionar l'opció 1. A continuació, ens demanarà el nom de l'usuari amb qui volem xatejar i ens connectarà amb ell. Un cop finalitzem la conversa, escriurem la paraula `sortir` per tornar al menú principal i elegir una altra opció.

Si volguessim xatejar amb un grup de persones, haurem de seleccionar l'opció 2. A continuació, ens demanarà el nom del grup al qual ens volem subscriure i ens connectarà amb ell. Un cop finalitzem la conversa, haurem de seguir el mateix procediment que en el xat privat per tornar al menú principal.

Si ens volguessim subcriure a un xat de grup, haurem de seleccionar l'opció 3. Aquesta ens demanarà el nom del grup al que ens volem subscriure i a continuació, se'ns apareixerà tots els missatges que s'han enviat d'aquell grup, fent-lo així, un sistema de missatges persistens.

Si volem enviar un esdeveniment de discover, haurem de seleccionar l'opció 4. Aquesta enviarà automàticament un missatge en forma d'esdeveniment o notificació als demés usuaris connectats al sistema. Automàticament, es respondrà a aquesta sol·licitud de discover.

Per accedir al canal d'insults, seleccionarem l'opció 5 i esperar a rebre un insult provenint d'un altre usuari. Nosaltres tindrem la oportinitat d'insultar també a un usuari aletori. Un cop volguem finalitzar els insults, haurem de seguir el mateix procediment que en el xat privat per tornar al menú principal.

Si volguessim sortir hauriem de seleccionar l'opció 6 i el client es desconnectarà del servidor.





