#!/usr/bin/env python3
"""
🧪 Schneller Test für alle 9 Sensoren
"""

import os
import sys
import glob
import time

def test_ds18b20():
    """Teste DS18B20 Sensoren"""
    print("🔍 DS18B20 Sensoren:")
    devices = glob.glob('/sys/bus/w1/devices/28-*')
    print(f"   Gefunden: {len(devices)} Geräte")
    
    working = 0
    for i, device in enumerate(devices[:8], 1):
        try:
            with open(f"{device}/w1_slave", 'r') as f:
                data = f.read()
            if 'YES' in data:
                temp_pos = data.find('t=') + 2
                temp = float(data[temp_pos:]) / 1000.0
                print(f"   ✅ Sensor {i}: {temp:.1f}°C")
                working += 1
            else:
                print(f"   ❌ Sensor {i}: CRC Fehler")
        except Exception as e:
            print(f"   ❌ Sensor {i}: {e}")
    
    return working

def test_dht22():
    """Teste DHT22 Sensor"""
    print("\n🔍 DHT22 Sensor:")
    try:
        import adafruit_dht
        import board
        
        dht = adafruit_dht.DHT22(board.D18)
        
        for attempt in range(3):
            try:
                temp = dht.temperature
                humidity = dht.humidity
                
                if temp is not None and humidity is not None:
                    print(f"   ✅ DHT22: {temp:.1f}°C, {humidity:.1f}%")
                    return True
                else:
                    print(f"   ⏳ Versuch {attempt + 1}/3...")
                    time.sleep(2)
            except Exception:
                if attempt < 2:
                    time.sleep(2)
        
        print("   ❌ DHT22: Keine Daten nach 3 Versuchen")
        return False
        
    except ImportError:
        print("   ❌ DHT22: Module nicht installiert")
        print("      Lösung: pip install adafruit-circuitpython-dht")
        return False
    except Exception as e:
        print(f"   ❌ DHT22: {e}")
        return False

def main():
    print("🧪 PI5 SENSOR TEST")
    print("==================")
    
    # Test DS18B20
    ds18b20_count = test_ds18b20()
    
    # Test DHT22  
    dht22_ok = test_dht22()
    
    # Ergebnis
    total_sensors = ds18b20_count + (1 if dht22_ok else 0)
    dht22_measurements = 2 if dht22_ok else 0
    total_measurements = ds18b20_count + dht22_measurements
    
    print(f"\n📊 ERGEBNIS:")
    print(f"   Sensoren: {total_sensors}/9 funktionieren")
    print(f"   Messwerte: {total_measurements}/10 verfügbar")
    
    if total_sensors >= 8:
        print("   ✅ Sehr gut! Fast alle Sensoren funktionieren")
    elif total_sensors >= 5:
        print("   ⚠️  OK, aber einige Sensoren fehlen")
    else:
        print("   ❌ Viele Sensoren fehlen - GPIO/Verkabelung prüfen")

if __name__ == "__main__":
    main()
