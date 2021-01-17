<img src="https://i.ibb.co/vL7D45R/DommeV3.png" alt="drawing" width="100"/>

# InformatiCup-2021 Handbuch
Dieses Handbuch beschreibt die Installation, sowie die Benutzung der Software inklusive der Erweiterungsparameter show und badManner.  
## Setup
Docker sollte auf der Maschine vorinstalliert sein.
Für die Erstellung des Docker muss nur noch 'docker build' aufgerufen werden, z. B. 'docker build --tag dommeai .'.
## Benutzung
Für die Benutzung muss nur im Docker-Dashboard der entsprechende Docker gestartet werden oder über die Konsole mit 
dem Aufruf 'docker run' (in unserem Beispiel also 'docker run dommeai') dieser gestartet werden.
Für die erfolgreiche Verbindung mit dem Server wird ein Apikey vorausgesetzt, der nicht mit bereitgestellt wird. 
Dieser soll in einer "apikey.txt" in diesem Verzeichnis gespeichert sein.
### Erweiterungen
Wenn show=True, dann wird pro Runde eine *.jpg im Docker gespeichert. 
Diese werden pro Spiel in einem Ordner im Docker gesammelt. Der Ordner wird jeweils als erste Deadline erstellt 
und kann somit als Startzeit gesehen werden.
Um diesen Ordner aus dem Docker zu bekommen, muss der folgende Aufruf in der Konsole getätigt werden: 
"docker cp <container-ID>:/app/<game-ID> .".
Die Container-ID kann über die Zeile "docker ps -a" ausgelesen werden und die game-ID über "dir" wenn man sich 
im Container befindet.
Dies kopiert den Ordner mit allen Bildern in das aktuelle Verzeichnis.

Wenn badManner=True gesetzt wurde, wird eine zufällige 'toxische' Nachricht in der lokalen Konsole 
am Ende eines Spiels gedruckt.

Voreingestellt sind die Erweiterungen mit show=False, ergo ein GUI wird nicht gezeigt um Ressourcen zu schonen und 
badManner=True. Um diese Parameter zu ändern, muss im Code in PlaySpe_ed.py im Aufruf in der letzten Zeile diese 
entsprechend verändert und erst dann der Docker erstellt werden.
## Abhängigkeiten
Es hat sich eine Aufteilung in vier Klassen ergeben, in derem Zentrum der Agent steht, der mit 
den anderen Klassen kommuniziert. In der Klasse PlaySpe_ed wird durch die Methode play() der
Agent initialisiert.

In der Klasse AgentUtils befinden sich alle unabhängigen Hilfsmethoden und 
in Spe_edGUI die Methode zum Erstellen des GUIs.
![UML-Klassendiagramm der DommeAI](https://i.ibb.co/J2BKm3q/Domme-AI-UML.png)