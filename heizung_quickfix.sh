#!/bin/bash
# 🚀 Pi5 Quick Fix für lgpio und Docker Permissions
# Für Systeme die bereits install_simple.sh ausgeführt haben

echo "🔧 Pi5 Quick Fix für häufige Probleme..."

# 1. lgpio installieren
echo "📡 Installiere Pi 5 GPIO Support..."
sudo apt-get update
sudo apt-get install -y python3-lgpio lgpio

# In venv installieren
cd ~/pi5-sensors
source venv/bin/activate
pip install lgpio

# 2. Docker Permissions fixen
echo "🐳 Fixe Docker Permissions..."
sudo usermod -aG docker $USER

# 3. Service mit sudo docker update
echo "⚙️ Update systemd service..."
sudo tee /etc/systemd/system/pi5-sensors.service > /dev/null << 'EOF'
[Unit]
Description=Pi5 Sensor Reader (9 Sensoren)
After=docker.service network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pi5-sensors
ExecStartPre=/bin/sleep 20
ExecStartPre=/usr/bin/sudo /usr/bin/docker compose up -d
ExecStart=/home/pi/pi5-sensors/venv/bin/python sensor_reader.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# 4. Service neu laden
sudo systemctl daemon-reload
sudo systemctl stop pi5-sensors
sudo systemctl start pi5-sensors

# 5. Container manuell starten
echo "🚀 Starte Container..."
cd ~/pi5-sensors
sudo docker compose up -d

echo ""
echo "🎉 Quick Fix abgeschlossen!"
echo ""
echo "🔧 Bei 'GPIO busy' Fehler:"
echo "   sudo systemctl stop pi5-sensors"
echo "   curl -sSL https://raw.githubusercontent.com/OliverRebock/Heizung_small/main/gpio_cleanup.py | python3"
echo ""
echo "🔧 Teste jetzt:"
echo "   cd ~/pi5-sensors"
echo "   source venv/bin/activate"
echo "   python sensor_reader.py test"
echo ""
echo "📊 Service Status:"
echo "   sudo systemctl status pi5-sensors"
echo ""
echo "🌐 Zugriff:"
echo "   Grafana: http://$(hostname -I | awk '{print $1}'):3000"
echo "   InfluxDB: http://$(hostname -I | awk '{print $1}'):8086"
echo ""
echo "⚠️ WICHTIG: Logout/Login für Docker Permissions!"
