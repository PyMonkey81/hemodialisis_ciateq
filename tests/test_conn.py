import serial.tools.list_ports
print("Puertos detectados:", list(serial.tools.list_ports.comports()))