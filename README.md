# InformatiCup-2021 Handbuch
Dieses Handbuch beschreibt die Installation, sowie die Benutzung der Software inklusive der Erweiterungsparamter show und badManner.  
## Setup
Docker sollte auf der Maschine vorinstalliert sein.
Für die Erstellung des Docker muss nur noch 'docker build' aufgerufen werden, z. B. 'docker build Domme'. 
Voreingestellt sind die Erweiterungen mit show=False, ergo ein GUI wird nicht gezeigt um Ressourcen zu schonen und badManner=True, die besagt, dass eine 'toxische' Nachricht in der lokalen Konsole gedruckt wird. 
Um diese Parameter zu ändern, muss im Code in PlaySpe_ed im Aufruf in der letzten Zeile diese entsprechend verändert und erst dann der Docker erstellt werden.

## Benutzung
Für die Benutzung muss nur im Docker-Dashboard der entsprechende Docker gestartet werden oder über die Konsole mit dem Aufruf 'docker run' (in unserem Beispiel also 'docker run Domme') dieser gestartet werden.
Wenn show=True gesetzt wurde ?
- APIKEY
- Show in Docker möglich?
- BadManner

## Abhängigkeiten
Evtl Play-Agent-(GUI)-Utils Abhhängigkeiten erklären?