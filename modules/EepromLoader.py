import serial

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

    def write(self, program_file:str="program.bin"):
        self.serial.write(b'L')  # Load command

        with open(program_file, "rb") as f:
            data = f.read()
            if len(data) > 65536:
                raise ValueError("Program çok büyük!")
            data += b'\x00' * (65536 - len(data)) 
            self.serial.write(data)

        print(f"{program_file} loaded")

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
            