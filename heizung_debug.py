#!/usr/bin/env python3
"""
🔍 Sensor Debug Tool für Pi5 - Findet fehlende Sensoren
Prüft Hardware, Software und InfluxDB systematisch

Aufruf:
python3 sensor_debug.py
"""

import os
import sys
import time
import subprocess
import configparser
from pathlib import Path

def print_header(title):
    """Schöne Überschrift"""
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print(f"{'='*50}")

def check_ds18b20_hardware():
    """Prüfe DS18B20 Hardware"""
    print_header("DS18B20 HARDWARE CHECK")
    
    # 1. GPIO Module geladen?
    print("📡 GPIO Module:")
    modules = ['w1_gpio', 'w1_therm']
    for module in modules:
        try:
            result = subprocess.run(['lsmod'], capture_output=True, text=True)
            if module in result.stdout:
                print(f"   ✅ {module} geladen")
            else:
                print(f"   ❌ {module} NICHT geladen")
                print(f"      Fix: sudo modprobe {module}")
        except:
            print(f"   ⚠️ {module} Status unbekannt")
    
    # 2. w1 Devices
    print("\n🌡️ DS18B20 Sensoren erkannt:")
    w1_path = "/sys/bus/w1/devices/"
    try:
        if os.path.exists(w1_path):
            devices = [d for d in os.listdir(w1_path) if d.startswith('28-')]
            if devices:
                for i, device in enumerate(devices, 1):
                    print(f"   ✅ DS18B20_{i}: {device}")
                    
                    # Temperatur lesen
                    temp_file = f"{w1_path}{device}/w1_slave"
                    try:
                        with open(temp_file, 'r') as f:
                            data = f.read()
                            if 'YES' in data:
                                temp_str = data.split('t=')[1].strip()
                                temp = float(temp_str) / 1000.0
                                print(f"      📊 {temp:.1f}°C")
                            else:
                                print(f"      ❌ CRC Fehler")
                    except Exception as e:
                        print(f"      ⚠️ Lesefehler: {e}")
                        
                print(f"\n📈 TOTAL: {len(devices)} DS18B20 Sensoren erkannt")
                return devices
            else:
                print("   ❌ KEINE DS18B20 Sensoren gefunden!")
                print("      Mögliche Ursachen:")
                print("      - Verkabelung prüfen (GPIO 4, 3.3V, GND)")
                print("      - w1-gpio nicht aktiviert in /boot/config.txt")
                print("      - Sensor defekt")
                return []
        else:
            print("   ❌ /sys/bus/w1/devices/ existiert nicht")
            print("      Fix: sudo modprobe w1-gpio w1-therm")
            return []
    except Exception as e:
        print(f"   ❌ Fehler beim Lesen: {e}")
        return []

def check_dht22_hardware():
    """Prüfe DHT22 Hardware"""
    print_header("DHT22 HARDWARE CHECK")
    
    try:
        # Import Test
        print("📦 Import Test:")
        try:
            import adafruit_dht
            import board
            print("   ✅ adafruit_dht verfügbar")
            print("   ✅ board verfügbar")
        except ImportError as e:
            print(f"   ❌ Import Fehler: {e}")
            return False
            
        # GPIO Test
        print("\n🔌 GPIO Test:")
        try:
            pin = board.D18
            print(f"   ✅ GPIO 18 verfügbar: {pin}")
        except Exception as e:
            print(f"   ❌ GPIO 18 Fehler: {e}")
            return False
            
        # DHT22 Test
        print("\n🌡️ DHT22 Sensor Test:")
        try:
            dht = adafruit_dht.DHT22(board.D18, use_pulseio=False)
            
            for attempt in range(3):
                try:
                    temp = dht.temperature
                    humidity = dht.humidity
                    
                    if temp is not None and humidity is not None:
                        print(f"   ✅ DHT22: {temp:.1f}°C, {humidity:.1f}%")
                        dht.exit()
                        return True
                    else:
                        print(f"   ⚠️ Versuch {attempt+1}: None-Werte")
                        
                except RuntimeError as e:
                    print(f"   ⚠️ Versuch {attempt+1}: {e}")
                except Exception as e:
                    print(f"   ❌ Versuch {attempt+1}: {e}")
                    
                if attempt < 2:
                    time.sleep(3)
                    
            print("   ❌ DHT22 liefert keine gültigen Daten")
            try:
                dht.exit()
            except:
                pass
            return False
            
        except Exception as e:
            print(f"   ❌ DHT22 Init Fehler: {e}")
            return False
            
    except Exception as e:
        print(f"❌ DHT22 Test fehlgeschlagen: {e}")
        return False

def check_config():
    """Prüfe Konfiguration"""
    print_header("KONFIGURATION CHECK")
    
    config_file = os.path.join(os.path.dirname(__file__), "config.ini")
    if not os.path.exists(config_file):
        print(f"❌ config.ini nicht gefunden: {config_file}")
        return None
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        print("📋 Konfigurierte Sensoren:")
        # Database Config
        if 'database' in config:
            print("\n🗄️ Database:")
            for key, value in config['database'].items():
                print(f"   {key}: {value}")
        # Labels Config
        if 'labels' in config:
            print("\n🏷️ Sensor Labels:")
            sensor_count = 0
            for key, value in config['labels'].items():
                print(f"   {key}: {value}")
                sensor_count += 1
            print(f"\n📊 TOTAL: {sensor_count} Sensoren konfiguriert")
            return config
        else:
            print("❌ Keine [labels] Sektion gefunden")
            return None
    except Exception as e:
        print(f"❌ Config Fehler: {e}")
        return None

def check_influxdb_connection():
    """Prüfe InfluxDB Verbindung"""
    print_header("INFLUXDB CONNECTION CHECK")
    
    try:
        from influxdb_client import InfluxDBClient
        
        # Config laden
        config = configparser.ConfigParser()
        config.read("/home/pi/pi5-sensors/config.ini")
        
        if 'database' not in config:
            print("❌ Database config fehlt")
            return False
            
        host = config.get('database', 'host', fallback='localhost')
        port = config.get('database', 'port', fallback='8086')
        token = config.get('database', 'token', fallback='pi5-token-2024')
        org = config.get('database', 'org', fallback='pi5org')
        bucket = config.get('database', 'bucket', fallback='sensors')
        
        print(f"🔗 Verbinde zu InfluxDB:")
        print(f"   Host: {host}:{port}")
        print(f"   Org: {org}")
        print(f"   Bucket: {bucket}")
        
        # Verbindung testen
        url = f"http://{host}:{port}"
        client = InfluxDBClient(url=url, token=token, org=org)
        
        # Health Check
        health = client.health()
        if health.status == "pass":
            print("   ✅ InfluxDB erreichbar")
            
            # Query API testen
            query_api = client.query_api()
            
            # Letzte Daten abfragen
            query = f'''
            from(bucket: "{bucket}")
                |> range(start: -1h)
                |> last()
            '''
            
            try:
                result = query_api.query(query)
                
                print("\n📊 Letzte Sensor-Daten (1h):")
                sensor_data = {}
                
                for table in result:
                    for record in table.records:
                        measurement = record.get_measurement()
                        field = record.get_field()
                        value = record.get_value()
                        sensor_name = record.values.get('sensor_name', 'unknown')
                        
                        key = f"{sensor_name}_{field}"
                        sensor_data[key] = {
                            'value': value,
                            'time': record.get_time(),
                            'measurement': measurement
                        }
                
                if sensor_data:
                    for sensor, data in sensor_data.items():
                        age = (time.time() - data['time'].timestamp()) / 60
                        print(f"   ✅ {sensor}: {data['value']:.1f} (vor {age:.0f}min)")
                    
                    print(f"\n📈 TOTAL: {len(sensor_data)} Sensor-Werte in InfluxDB")
                else:
                    print("   ⚠️ KEINE Sensor-Daten in InfluxDB gefunden!")
                    print("      Mögliche Ursachen:")
                    print("      - Service läuft nicht")
                    print("      - Sensoren defekt")  
                    print("      - Schreibfehler")
                    
            except Exception as e:
                print(f"   ❌ Query Fehler: {e}")
                
            client.close()
            return True
        else:
            print(f"   ❌ InfluxDB nicht gesund: {health.status}")
            return False
            
    except ImportError:
        print("❌ influxdb-client nicht installiert")
        return False
    except Exception as e:
        print(f"❌ InfluxDB Verbindung fehlgeschlagen: {e}")
        return False

def check_service_status():
    """Prüfe Service Status"""
    print_header("SERVICE STATUS CHECK")
    
    # Service Status
    try:
        result = subprocess.run(['systemctl', 'status', 'pi5-sensors'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pi5-sensors service läuft")
        else:
            print("❌ pi5-sensors service läuft NICHT")
            print("   Fix: sudo systemctl start pi5-sensors")
    except Exception as e:
        print(f"❌ Service Status Fehler: {e}")
    
    # Live Logs (letzte 10 Zeilen)
    print("\n📝 Service Logs (letzte 10 Zeilen):")
    try:
        result = subprocess.run(['journalctl', '-u', 'pi5-sensors', '-n', '10', '--no-pager'], 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        else:
            print("   Keine Logs verfügbar")
    except Exception as e:
        print(f"❌ Log Fehler: {e}")

def main():
    """Hauptfunktion"""
    print("🔍 SENSOR DEBUG TOOL für Pi5")
    print("=" * 50)
    
    # Prüfe ob wir im richtigen Verzeichnis sind
    if not os.path.exists("/home/pi/pi5-sensors"):
        print("❌ pi5-sensors Verzeichnis nicht gefunden!")
        print("   Installiere zuerst das Projekt")
        sys.exit(1)
    
    os.chdir("/home/pi/pi5-sensors")
    
    # Aktiviere venv für Python Tests
    venv_python = "/home/pi/pi5-sensors/venv/bin/python3"
    if os.path.exists(venv_python):
        # Füge venv zum Python Path hinzu
        venv_site = "/home/pi/pi5-sensors/venv/lib/python3.11/site-packages"
        if os.path.exists(venv_site):
            sys.path.insert(0, venv_site)
    
    # 1. Hardware Checks
    ds18b20_devices = check_ds18b20_hardware()
    dht22_working = check_dht22_hardware()
    
    # 2. Config Check
    config = check_config()
    
    # 3. InfluxDB Check
    influx_working = check_influxdb_connection()
    
    # 4. Service Check
    check_service_status()
    
    # 5. Zusammenfassung
    print_header("ZUSAMMENFASSUNG")
    
    expected_sensors = 9
    found_sensors = len(ds18b20_devices) + (1 if dht22_working else 0)
    
    print(f"🎯 Erwartete Sensoren: {expected_sensors}")
    print(f"🔍 Gefundene Sensoren: {found_sensors}")
    print(f"📊 DS18B20: {len(ds18b20_devices)}/8")
    print(f"🌡️ DHT22: {'✅' if dht22_working else '❌'}")
    print(f"🗄️ InfluxDB: {'✅' if influx_working else '❌'}")
    
    if found_sensors < expected_sensors:
        print(f"\n⚠️ {expected_sensors - found_sensors} Sensor(en) fehlen!")
        print("\n💡 Nächste Schritte:")
        
        if len(ds18b20_devices) < 8:
            missing = 8 - len(ds18b20_devices)
            print(f"   1. {missing} DS18B20 Sensor(en) prüfen:")
            print("      - Verkabelung (GPIO 4, 3.3V, GND)")
            print("      - 4.7kΩ Pull-up Widerstand")
            print("      - Sensor defekt?")
            
        if not dht22_working:
            print("   2. DHT22 Sensor prüfen:")
            print("      - Verkabelung (GPIO 18, 3.3V, GND)")
            print("      - sudo systemctl stop pi5-sensors")
            print("      - python3 sensor_reader.py test")
            
        if not influx_working:
            print("   3. InfluxDB prüfen:")
            print("      - docker compose ps")
            print("      - sudo systemctl restart pi5-sensors")
    else:
        print("\n🎉 Alle Sensoren gefunden!")
        if not influx_working:
            print("   Aber InfluxDB Problem - Service neu starten")

if __name__ == "__main__":
    main()
