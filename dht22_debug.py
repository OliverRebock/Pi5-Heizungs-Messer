#!/usr/bin/env python3
"""
🌡️ DHT22 Debug Tool für Raspberry Pi 5
Speziell für GPIO 18 und Pi 5 Kompatibilität

Aufruf:
python3 dht22_debug.py
"""

import time
import sys

def test_imports():
    """Teste alle benötigten Imports"""
    print("🔍 Teste Python Imports...")
    
    try:
        import board
        print("✅ board importiert")
    except ImportError as e:
        print(f"❌ board fehlt: {e}")
        return False
        
    try:
        import adafruit_dht
        print("✅ adafruit_dht importiert")
    except ImportError as e:
        print(f"❌ adafruit_dht fehlt: {e}")
        return False
        
    try:
        import digitalio
        print("✅ digitalio importiert")
    except ImportError as e:
        print(f"❌ digitalio fehlt: {e}")
        return False
        
    return True

def test_gpio_access():
    """Teste GPIO Zugriff"""
    print("\n🔌 Teste GPIO Zugriff...")
    
    try:
        import board
        pin = board.D18
        print(f"✅ GPIO 18 verfügbar: {pin}")
        return True
    except Exception as e:
        print(f"❌ GPIO 18 Fehler: {e}")
        return False

def test_dht22_init():
    """Teste DHT22 Initialisierung"""
    print("\n🌡️ Teste DHT22 Initialisierung...")
    
    try:
        import adafruit_dht
        import board
        
        # Standard Init
        print("   Versuche Standard-Init...")
        dht = adafruit_dht.DHT22(board.D18)
        print("✅ Standard DHT22 Init erfolgreich")
        
        # Pi 5 optimiert
        print("   Versuche Pi5-optimierte Init...")
        dht_pi5 = adafruit_dht.DHT22(board.D18, use_pulseio=False)
        print("✅ Pi5-optimierte DHT22 Init erfolgreich")
        
        return dht_pi5
        
    except Exception as e:
        print(f"❌ DHT22 Init Fehler: {e}")
        return None

def test_dht22_reading(dht_sensor, attempts=10):
    """Teste DHT22 Lesungen"""
    print(f"\n📊 Teste DHT22 Lesungen ({attempts} Versuche)...")
    
    successful_reads = 0
    
    for i in range(attempts):
        try:
            print(f"   Versuch {i+1}/{attempts}...", end=" ")
            
            temp = dht_sensor.temperature
            humidity = dht_sensor.humidity
            
            if temp is not None and humidity is not None:
                if -40 <= temp <= 80 and 0 <= humidity <= 100:
                    print(f"✅ {temp:.1f}°C, {humidity:.1f}%")
                    successful_reads += 1
                else:
                    print(f"⚠️ Ungültig: {temp}°C, {humidity}%")
            else:
                print("❌ None-Werte")
                
        except RuntimeError as e:
            if "Checksum did not validate" in str(e):
                print("⚠️ Prüfsummen-Fehler")
            elif "timed out" in str(e):
                print("⚠️ Timeout")
            else:
                print(f"⚠️ RuntimeError: {e}")
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")
            
        # Pause zwischen Versuchen
        if i < attempts - 1:
            time.sleep(3)
    
    success_rate = (successful_reads / attempts) * 100
    print(f"\n📈 Erfolgsrate: {successful_reads}/{attempts} ({success_rate:.1f}%)")
    
    if success_rate >= 50:
        print("✅ DHT22 funktioniert gut!")
        return True
    elif success_rate >= 20:
        print("⚠️ DHT22 funktioniert teilweise")
        return False
    else:
        print("❌ DHT22 funktioniert nicht zuverlässig")
        return False

def show_recommendations():
    """Zeige Empfehlungen"""
    print("\n💡 DHT22 Empfehlungen für Pi 5:")
    print("   1. GPIO 18 verwenden (Physical Pin 12)")
    print("   2. use_pulseio=False bei Init setzen")
    print("   3. 3-5 Sekunden zwischen Lesungen warten")
    print("   4. RuntimeError abfangen (normal bei DHT22)")
    print("   5. Werte validieren (-40°C bis 80°C, 0-100%)")
    print("   6. 3.3V VCC, GND und GPIO 18 korrekt verkabeln")

def main():
    """Hauptfunktion"""
    print("🌡️ DHT22 Debug Tool für Raspberry Pi 5")
    print("=" * 50)
    
    # 1. Teste Imports
    if not test_imports():
        print("\n❌ Import-Fehler! Installiere zuerst:")
        print("   pip install adafruit-circuitpython-dht adafruit-blinka")
        sys.exit(1)
    
    # 2. Teste GPIO
    if not test_gpio_access():
        print("\n❌ GPIO-Fehler! Prüfe Verkabelung.")
        sys.exit(1)
    
    # 3. Teste DHT22 Init
    dht_sensor = test_dht22_init()
    if not dht_sensor:
        print("\n❌ DHT22 Init-Fehler!")
        sys.exit(1)
    
    # 4. Teste Lesungen
    if test_dht22_reading(dht_sensor):
        print("\n🎉 DHT22 funktioniert!")
    else:
        print("\n⚠️ DHT22 hat Probleme")
        show_recommendations()

if __name__ == "__main__":
    main()
