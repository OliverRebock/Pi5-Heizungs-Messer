# Pi5 Heizungs Messer

Dieses Projekt dient zur Messung und Überwachung von Heizungsdaten mit einem Raspberry Pi 5. Es werden verschiedene Sensoren ausgelesen und die Daten zur weiteren Analyse bereitgestellt.

## Projektüberblick
- Python-Skripte zur Sensoransteuerung und Datenerfassung
- Unterstützung für DHT22 und weitere Temperatursensoren
- Hilfsskripte zur Fehlerbehebung und GPIO-Bereinigung

## Verzeichnisstruktur
- `dht22_debug.py` – Debugging und Testen des DHT22-Sensors
- `gpio_cleanup.py` – Bereinigt die GPIO-Pins des Raspberry Pi
- `heizung_debug.py` – Hauptskript zur Heizungsüberwachung
- `heizung_quickfix.sh` – Shell-Skript für schnelle Fehlerbehebung
- `install_heizung.sh` – Installationsskript für alle Abhängigkeiten
- `test_heizung_sensoren.py` – Testet die Funktion aller angeschlossenen Sensoren

## Installation
1. **Repository klonen**
   ```bash
   git clone https://github.com/OliverRebock/Pi5-Heizungs-Messer.git
   cd Pi5-Heizungs-Messer
   ```
2. **Installationsskript ausführen**
   ```bash
   chmod +x install_heizung.sh
   ./install_heizung.sh
   ```
   Das Skript installiert alle benötigten Python-Abhängigkeiten und richtet die Umgebung ein.
   
   **Hinweis:** Falls der Fehler "E: Unable to locate package lgpio" auftritt, ist das normal. 
   Das Skript installiert lgpio automatisch über pip als Alternative.

3. **(Optional) Quickfix-Skript ausführen**
   Bei Problemen mit der Installation oder Sensorerkennung kann das Quickfix-Skript helfen:
   ```bash
   chmod +x heizung_quickfix.sh
   ./heizung_quickfix.sh
   ```

## Nutzung
- Starte das Hauptskript zur Heizungsüberwachung:
  ```bash
  python heizung_debug.py
  ```
- Für Debugging einzelner Sensoren oder GPIO-Bereinigung können die jeweiligen Skripte direkt ausgeführt werden.

## Hinweise
- Das Projekt ist für den Einsatz auf einem Raspberry Pi 5 optimiert.
- Für die Nutzung der Sensoren müssen diese korrekt angeschlossen und konfiguriert sein.

## Lizenz
MIT License
