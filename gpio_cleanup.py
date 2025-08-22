#!/usr/bin/env python3
"""
🔧 GPIO Cleanup Tool für Raspberry Pi 5
Speziell um "GPIO busy" Probleme zu lösen

Aufruf:
python3 gpio_cleanup.py
"""

import subprocess
import time
import sys
import os

def check_service_status():
    """Prüfe ob pi5-sensors service läuft"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'pi5-sensors'], 
                              capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except:
        return False

def stop_service():
    """Stoppe pi5-sensors service"""
    print("🛑 Stoppe pi5-sensors service...")
    try:
        subprocess.run(['sudo', 'systemctl', 'stop', 'pi5-sensors'], check=True)
        print("   ✅ Service gestoppt")
        time.sleep(2)
        return True
    except subprocess.CalledProcessError:
        print("   ⚠️ Service konnte nicht gestoppt werden")
        return False

def kill_python_processes():
    """Töte hängende Python Prozesse"""
    print("💀 Töte hängende Python Prozesse...")
    try:
        # Finde Python Prozesse die sensor_reader.py verwenden
        result = subprocess.run(['pgrep', '-f', 'sensor_reader'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], check=True)
                    print(f"   ✅ Prozess {pid} beendet")
                except:
                    print(f"   ⚠️ Prozess {pid} konnte nicht beendet werden")
        else:
            print("   ✅ Keine hängenden Prozesse gefunden")
    except:
        print("   ⚠️ Fehler beim Suchen nach Prozessen")

def cleanup_gpio():
    """GPIO cleanup"""
    print("🔌 GPIO Cleanup...")
    try:
        # Versuche GPIO zu resetten
        if os.path.exists('/sys/class/gpio/unexport'):
            subprocess.run(['echo', '18'], input='18\n', text=True, 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("   ✅ GPIO cleanup durchgeführt")
    except:
        print("   ⚠️ GPIO cleanup fehlgeschlagen")

def restart_service():
    """Starte pi5-sensors service neu"""
    print("🚀 Starte pi5-sensors service...")
    try:
        subprocess.run(['sudo', 'systemctl', 'start', 'pi5-sensors'], check=True)
        time.sleep(3)
        
        # Status prüfen
        if check_service_status():
            print("   ✅ Service erfolgreich gestartet")
            return True
        else:
            print("   ⚠️ Service läuft nicht")
            return False
    except subprocess.CalledProcessError:
        print("   ❌ Service konnte nicht gestartet werden")
        return False

def test_dht22():
    """Teste DHT22 direkt"""
    print("🌡️ Teste DHT22...")
    try:
        # Wechsle zum Projektverzeichnis
        os.chdir('/home/pi/pi5-sensors')
        
        # Aktiviere venv und teste
        test_code = """
import sys
sys.path.insert(0, '/home/pi/pi5-sensors/venv/lib/python3.11/site-packages')
try:
    import adafruit_dht
    import board
    
    dht = adafruit_dht.DHT22(board.D18, use_pulseio=False)
    temp = dht.temperature
    humidity = dht.humidity
    
    if temp is not None and humidity is not None:
        print(f'✅ DHT22: {temp:.1f}°C, {humidity:.1f}%')
    else:
        print('⚠️ DHT22: Keine Daten')
        
    dht.exit()
    
except Exception as e:
    print(f'❌ DHT22 Fehler: {e}')
"""
        
        result = subprocess.run(['/home/pi/pi5-sensors/venv/bin/python3', '-c', test_code],
                              capture_output=True, text=True, timeout=30)
        
        print(f"   {result.stdout.strip()}")
        if result.stderr:
            print(f"   Fehler: {result.stderr.strip()}")
            
    except subprocess.TimeoutExpired:
        print("   ⚠️ DHT22 Test timeout")
    except Exception as e:
        print(f"   ❌ DHT22 Test fehlgeschlagen: {e}")

def show_status():
    """Zeige aktuellen Status"""
    print("\n📊 Status nach Cleanup:")
    
    # Service Status
    if check_service_status():
        print("   ✅ pi5-sensors service: läuft")
    else:
        print("   ❌ pi5-sensors service: gestoppt")
    
    # Docker Status
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=pi5-'], 
                              capture_output=True, text=True)
        if 'pi5-influxdb' in result.stdout and 'pi5-grafana' in result.stdout:
            print("   ✅ Docker Container: laufen")
        else:
            print("   ⚠️ Docker Container: Problem")
    except:
        print("   ❌ Docker: nicht verfügbar")

def main():
    """Hauptfunktion"""
    print("🔧 GPIO Cleanup Tool für Pi 5")
    print("=" * 40)
    
    # 1. Service stoppen
    if check_service_status():
        stop_service()
    else:
        print("✅ pi5-sensors service bereits gestoppt")
    
    # 2. Hängende Prozesse töten
    kill_python_processes()
    
    # 3. GPIO cleanup
    cleanup_gpio()
    
    # 4. Kurz warten
    print("⏳ Warte 5 Sekunden...")
    time.sleep(5)
    
    # 5. DHT22 testen
    test_dht22()
    
    # 6. Service neu starten
    restart_service()
    
    # 7. Status anzeigen
    show_status()
    
    print("\n🎉 GPIO Cleanup abgeschlossen!")
    print("\n💡 Wenn immer noch 'GPIO busy':")
    print("   1. sudo reboot")
    print("   2. Oder: sudo systemctl stop pi5-sensors && python3 gpio_cleanup.py")

if __name__ == "__main__":
    main()
