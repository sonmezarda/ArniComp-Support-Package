import serial
import time
class EepromLoader:
    def __init__(self, port:str='/dev/ttyACM0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = serial.Serial(port, baudrate)
        if not self.serial.is_open:
            raise Exception("Serial port could not be opened.")

    def close_serial(self):
        if self.serial.is_open:
            self.serial.close()
            print("Serial port closed.")
        else:
            print("Serial port is already closed.")

    def open_serial(self):
        if not self.serial.is_open:
            self.serial.open()
            print("Serial port opened.")
        else:
            print("Serial port is already open.")

    def write(self, bin_path):
        ser = self.serial
        with open(bin_path, "rb") as f:
            data = f.read()
            print("Yükleme başlatılıyor...")
            ser.write(b'L')
            ser.flush()
            time.sleep(0.1)  # pico hazır olsun
            ser.write(data)
            ser.flush()
            print("Yükleme tamamlandı. Cihaza yazılıyor...")

        # Serial'den logları oku
        timeout = time.time() + 5  # max 5 saniye log bekle
        while True:
            if ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()
                print("PICO:", line)
            if time.time() > timeout:
                break

    def check_file(self, program_file:str="program.bin", top_n=64):
        with open(program_file, "rb") as f:
            data = f.read()

        return data[:top_n] 

    def check_serial(self):
        self.serial.write(b'D')

        while True:
            line = self.serial.readline().decode().strip()
            print(line)
            if "3F" in line:
                break

