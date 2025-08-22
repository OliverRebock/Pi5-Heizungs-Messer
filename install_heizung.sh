#!/bin/bash
# =============================================================================
# ULTRA-MINIMAL INSTALLATION - Pi 5 mit 9 Sensoren
# =============================================================================
# Fokus: Einfach, schnell, funktioniert
# - 8x DS18B20 Temperatursensoren
# - 1x DHT22 (Temperatur + Luftfeuchtigkeit) 
# - InfluxDB + Grafana (ohne Login)
# - Python venv für DHT22
# =============================================================================

set -e  # Beende bei Fehlern

echo "🚀 ULTRA-MINIMAL Pi5 Sensor Installation"
echo "========================================"
echo "📦 9 Sensoren + InfluxDB + Grafana (ohne Login)"
echo ""

# =============================================================================
# 1. SYSTEM VORBEREITEN
# =============================================================================
echo "🔧 System vorbereiten..."
sudo apt update -y
sudo apt install -y python3-pip python3-venv git curl

# GPIO für DS18B20 aktivieren
echo "🔌 GPIO aktivieren..."
if ! grep -q "dtoverlay=w1-gpio" /boot/firmware/config.txt; then
    echo "dtoverlay=w1-gpio,gpiopin=4" | sudo tee -a /boot/firmware/config.txt
    echo "   ✅ GPIO konfiguriert"
else
    echo "   ✅ GPIO bereits konfiguriert"
fi

# =============================================================================
# 2. DOCKER INSTALLIEREN (EINFACH)
# =============================================================================
echo "🐳 Docker installieren..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "   ✅ Docker installiert"
else
    echo "   ✅ Docker bereits vorhanden"
fi

# User zur docker group hinzufügen (falls noch nicht)
if ! groups $USER | grep -q docker; then
    sudo usermod -aG docker $USER
    echo "   ✅ User zur docker group hinzugefügt"
fi

# Docker starten (ohne enable - das macht Probleme)
sudo systemctl start docker 2>/dev/null || true
sleep 3

# =============================================================================
# 3. PROJEKTVERZEICHNIS
# =============================================================================
PROJECT_DIR="$HOME/pi5-sensors"
echo "📁 Erstelle Projekt: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# =============================================================================
# 4. PYTHON SENSOR SCRIPT
# =============================================================================
echo "🐍 Erstelle Sensor Script..."

cat > sensor_reader.py << 'EOF'
#!/usr/bin/env python3
"""Ultra-minimal 9-Sensor Reader für Pi5"""

import os
import sys
import time
import glob
import configparser
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class Pi5SensorReader:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.setup_influxdb()
        
    def setup_influxdb(self):
        """InfluxDB Verbindung"""
        self.client = InfluxDBClient(
            url="http://localhost:8086",
            token="pi5-token-2024",
            org="pi5org"
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
    def read_ds18b20_sensors(self):
        """Lese alle DS18B20 Sensoren"""
        sensors = []
        devices = glob.glob('/sys/bus/w1/devices/28-*')
        
        for i, device in enumerate(devices[:8], 1):
            try:
                with open(f"{device}/w1_slave", 'r') as f:
                    data = f.read()
                if 'YES' in data:
                    temp_pos = data.find('t=') + 2
                    temp = float(data[temp_pos:]) / 1000.0
                    
                    name = self.config.get('labels', f'ds18b20_{i}', fallback=f'Sensor {i}')
                    sensors.append({
                        'name': name,
                        'temperature': temp,
                        'sensor_id': f'ds18b20_{i}'
                    })
                    print(f"   DS18B20 {i}: {temp:.1f}°C ({name})")
            except Exception as e:
                print(f"   ❌ DS18B20 {i}: {e}")
                
        return sensors
        
    def read_dht22(self):
        """Lese DHT22 Sensor - Pi 5 optimiert mit GPIO cleanup"""
        dht = None
        try:
            import adafruit_dht
            import board
            
            # Pi 5 spezifische Initialisierung 
            dht = adafruit_dht.DHT22(board.D18, use_pulseio=False)
            
            # 5 Versuche mit längeren Pausen für Pi 5
            for attempt in range(5):
                try:
                    # Pi 5 braucht mehr Zeit zwischen Lesungen
                    if attempt > 0:
                        time.sleep(3)
                    
                    temp = dht.temperature
                    humidity = dht.humidity
                    
                    # Validierung der Werte
                    if (temp is not None and humidity is not None and 
                        -40 <= temp <= 80 and 0 <= humidity <= 100):
                        name = self.config.get('labels', 'dht22', fallback='Raumklima')
                        print(f"   DHT22: {temp:.1f}°C, {humidity:.1f}% ({name})")
                        return {
                            'name': name,
                            'temperature': temp,
                            'humidity': humidity,
                            'sensor_id': 'dht22'
                        }
                    else:
                        print(f"   ⚠️  DHT22: Ungültige Werte (T:{temp}, H:{humidity})")
                        
                except RuntimeError as e:
                    # Pi 5 RuntimeError behandeln
                    if "Checksum did not validate" in str(e):
                        print(f"   ⚠️  DHT22: Prüfsummen-Fehler (Versuch {attempt+1}/5)")
                    elif "timed out" in str(e):
                        print(f"   ⚠️  DHT22: Timeout (Versuch {attempt+1}/5)")
                    else:
                        print(f"   ⚠️  DHT22: {e} (Versuch {attempt+1}/5)")
                except Exception as e:
                    if "GPIO busy" in str(e):
                        print(f"   ⚠️  DHT22: GPIO 18 belegt (Versuch {attempt+1}/5)")
                        # GPIO cleanup versuchen
                        if dht:
                            try:
                                dht.exit()
                            except:
                                pass
                        time.sleep(5)  # Längere Pause bei GPIO busy
                    else:
                        print(f"   ⚠️  DHT22: Unerwarteter Fehler: {e}")
                        
            print("   ❌ DHT22: Keine gültigen Daten nach 5 Versuchen")
            
        except ImportError:
            print("   ❌ DHT22: adafruit-circuitpython-dht nicht installiert")
        except Exception as e:
            print(f"   ❌ DHT22: Initialisierung fehlgeschlagen: {e}")
        finally:
            # GPIO cleanup
            if dht:
                try:
                    dht.exit()
                except:
                    pass
        except Exception as e:
            print(f"   ❌ DHT22: {e}")
            
        return None
        
    def write_to_influxdb(self, sensors, dht22_data):
        """Schreibe Daten zu InfluxDB"""
        try:
            points = []
            
            # DS18B20 Sensoren
            for sensor in sensors:
                point = Point("temperature") \
                    .tag("sensor_type", "ds18b20") \
                    .tag("sensor_id", sensor['sensor_id']) \
                    .tag("name", sensor['name']) \
                    .field("value", sensor['temperature'])
                points.append(point)
                
            # DHT22 Sensor
            if dht22_data:
                # Temperatur
                point = Point("temperature") \
                    .tag("sensor_type", "dht22") \
                    .tag("sensor_id", "dht22") \
                    .tag("name", dht22_data['name']) \
                    .field("value", dht22_data['temperature'])
                points.append(point)
                
                # Luftfeuchtigkeit
                point = Point("humidity") \
                    .tag("sensor_type", "dht22") \
                    .tag("sensor_id", "dht22") \
                    .tag("name", dht22_data['name']) \
                    .field("value", dht22_data['humidity'])
                points.append(point)
                
            # Schreibe alle Punkte
            if points:
                self.write_api.write(bucket="sensors", record=points)
                print(f"   ✅ {len(points)} Datenpunkte geschrieben")
                
        except Exception as e:
            print(f"   ❌ InfluxDB Fehler: {e}")
            
    def run_once(self):
        """Ein Durchlauf"""
        print(f"🌡️  Lese Sensoren... {datetime.now().strftime('%H:%M:%S')}")
        
        # Lese alle Sensoren
        ds18b20_sensors = self.read_ds18b20_sensors()
        dht22_data = self.read_dht22()
        
        # Schreibe zu InfluxDB
        self.write_to_influxdb(ds18b20_sensors, dht22_data)
        
        total_sensors = len(ds18b20_sensors) + (1 if dht22_data else 0)
        print(f"   📊 {total_sensors}/9 Sensoren erfolgreich gelesen")
        
    def run_continuous(self):
        """Kontinuierlich laufen"""
        print("🔄 Starte kontinuierliche Überwachung (30s Intervall)")
        while True:
            try:
                self.run_once()
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n👋 Beendet durch Benutzer")
                break
            except Exception as e:
                print(f"❌ Fehler: {e}")
                time.sleep(30)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test-Modus
        reader = Pi5SensorReader()
        reader.run_once()
    else:
        # Kontinuierlicher Modus
        reader = Pi5SensorReader()
        reader.run_continuous()
EOF

# =============================================================================
# 5. KONFIGURATION
# =============================================================================
echo "⚙️ Erstelle Konfiguration..."

cat > config.ini << 'EOF'
[database]
host = localhost
port = 8086
token = pi5-token-2024
org = pi5org
bucket = sensors

[labels]
# 🏷️ Passe die Sensornamen hier an
ds18b20_1 = Vorlauf Heizkreis
ds18b20_2 = Rücklauf Heizkreis  
ds18b20_3 = Warmwasser Speicher
ds18b20_4 = Außentemperatur
ds18b20_5 = Heizraum
ds18b20_6 = Pufferspeicher Oben
ds18b20_7 = Pufferspeicher Mitte
ds18b20_8 = Pufferspeicher Unten
dht22 = Raumklima Heizraum
EOF

# =============================================================================
# 6. DOCKER COMPOSE
# =============================================================================
echo "🐳 Erstelle Docker Compose..."

cat > docker-compose.yml << 'EOF'
services:
  influxdb:
    image: influxdb:2.7
    container_name: pi5-influxdb
    restart: unless-stopped
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=pi5sensors2024
      - DOCKER_INFLUXDB_INIT_ORG=pi5org
      - DOCKER_INFLUXDB_INIT_BUCKET=sensors
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=pi5-token-2024
    volumes:
      - influxdb-data:/var/lib/influxdb2

  grafana:
    image: grafana/grafana:latest
    container_name: pi5-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      # 🔓 GRAFANA OHNE LOGIN!
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
      - GF_AUTH_DISABLE_LOGIN_FORM=true
      - GF_SECURITY_ALLOW_EMBEDDING=true
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - influxdb

volumes:
  influxdb-data:
  grafana-data:
EOF

# =============================================================================
# 7. PYTHON VENV ERSTELLEN
# =============================================================================
echo "🐍 Erstelle Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installiere Python Packages für Pi 5..."
pip install --upgrade pip

# Pi 5 spezifische Installation
pip install influxdb-client configparser

# DHT22 Packages - Pi 5 optimiert
echo "🌡️ Installiere DHT22 Support für Pi 5..."
pip install --upgrade setuptools

# Pi 5 braucht lgpio!
echo "📡 Installiere Pi 5 GPIO Support..."
# Alternative Installation für lgpio - falls Paket nicht verfügbar
sudo apt-get install -y python3-lgpio 2>/dev/null || {
    echo "⚠️  python3-lgpio nicht verfügbar - installiere über pip..."
    pip install lgpio
}
# Versuche lgpio auch über apt
sudo apt-get install -y lgpio 2>/dev/null || echo "⚠️  lgpio apt-Paket nicht verfügbar"

pip install adafruit-blinka
pip install --force-reinstall adafruit-circuitpython-dht

# Teste DHT22 Installation
echo "🔧 Teste DHT22 Installation..."
python3 -c "
try:
    import lgpio
    print('✅ lgpio verfügbar')
    import adafruit_dht
    import board
    print('✅ DHT22 Packages erfolgreich installiert')
except ImportError as e:
    print(f'❌ DHT22 Import Fehler: {e}')
except Exception as e:
    print(f'⚠️ DHT22 Test Warnung: {e}')
"

# =============================================================================
# 8. SYSTEMD SERVICE
# =============================================================================
echo "⚙️ Erstelle Systemd Service..."

sudo tee /etc/systemd/system/pi5-sensors.service > /dev/null << EOF
[Unit]
Description=Pi5 Sensor Reader (9 Sensoren)
After=docker.service network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$PROJECT_DIR
ExecStartPre=/bin/sleep 20
ExecStartPre=/usr/bin/sudo /usr/bin/docker compose up -d
ExecStart=$PROJECT_DIR/venv/bin/python sensor_reader.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable pi5-sensors.service

# =============================================================================
# 9. DOCKER CONTAINER STARTEN  
# =============================================================================
echo "🚀 Starte Docker Container..."
if command -v docker &> /dev/null && sudo systemctl is-active --quiet docker; then
    # Prüfe ob User in docker group ist, sonst sudo verwenden
    if groups $USER | grep -q docker; then
        docker compose up -d
    else
        echo "   ⚠️ User noch nicht in docker group - verwende sudo"
        sudo docker compose up -d
    fi
    echo "   ✅ Container gestartet"
    
    # Warte auf InfluxDB
    echo "⏳ Warte auf InfluxDB..."
    sleep 15
    
else
    echo "   ⚠️  Docker nicht verfügbar - manueller Start nötig"
fi

# =============================================================================
# 10. TEST
# =============================================================================
echo "🧪 Teste Sensoren..."
source venv/bin/activate
python sensor_reader.py test

# =============================================================================
# 11. FERTIG!
# =============================================================================
echo ""
echo "🎉 INSTALLATION ABGESCHLOSSEN!"
echo "=============================="
echo ""
echo "✅ Installiert:"
echo "   🌡️  9 Sensoren (8x DS18B20 + 1x DHT22)"
echo "   🐳 Docker + InfluxDB + Grafana"
echo "   🔓 Grafana OHNE Login"
echo "   ⚙️  Systemd Service"
echo ""
echo "🌐 Zugriff:"
echo "   📊 Grafana: http://$(hostname -I | awk '{print $1}'):3000"
echo "   🗄️  InfluxDB: http://$(hostname -I | awk '{print $1}'):8086"
echo ""
echo "🔧 Befehle:"
echo "   Service start: sudo systemctl start pi5-sensors"
echo "   Service logs:  sudo journalctl -u pi5-sensors -f"
echo "   Sensor test:   cd $PROJECT_DIR && source venv/bin/activate && python sensor_reader.py test"
echo ""
echo "⚠️  NEUSTART ERFORDERLICH für GPIO!"
read -p "🔄 Jetzt neu starten? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    sudo reboot
fi

echo "🚀 Installation fertig! Nach Neustart läuft alles automatisch."
