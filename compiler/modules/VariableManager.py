from __future__ import annotations
from enum import Enum, IntEnum


class Variable():
    def __init__(self, size:int, name:str, address:int, value:int = 0, value_type:any = None):
        self.size = size
        self.name = name
        self.address = address
        self.value = value
        self.value_type = value_type
        self.__post_init__()

    def __post_init__(self):
        if self.value is None:
            self.value = 0
        if self.size <= 0:
            raise ValueError("Variable size must be greater than 0")
        if self.address < 0:
            raise ValueError("Variable address must be non-negative")
    
    def get_low_address(self) -> int:
        return self.address & 0xFF
    
    def get_high_address(self) -> int:
        return (self.address >> 8) & 0xFF
    
    @staticmethod
    def get_value_type():
        return None
    
    def __str__(self):
        addr_str = '{:04X}'.format(self.address)
        return f"Variable(name={self.name}, address={addr_str}, size={self.size}, value={self.value}, value_type={self.value_type.__name__ if self.value_type else 'None'})"

class ByteVariable(Variable):
    def __init__(self, name:str, address:int, value:int = 0):
        super().__init__(size=ByteVariable.get_size(), value_type=int, name=name, address=address, value=value)
        if not (0 <= value < 256):
            raise ValueError("Byte variable value must be between 0 and 255")

    @staticmethod
    def get_value_type():
        return int
    
    @staticmethod
    def get_size():
        return 1

class ByteArrayVariable(Variable):
    def __init__(self, name:str, address:int, size:int, value:list[int] = None):
        super().__init__(size=size, value_type=list, name=name, address=address, value=value)
        if value is None:
            self.value = [0] * size
        if not (0 < size <= 256):
            raise ValueError("Byte array variable size must be between 1 and 256")

    @staticmethod
    def get_value_type():
        return list

    @staticmethod
    def get_size():
        return 1

class VarTypes(Enum):
    BYTE = ByteVariable
    BYTE_ARRAY = ByteArrayVariable

class IntTypes(IntEnum):
    DECIMAL = 0
    BINARY = 1
    HEX = 2

class VarManager():
    def __init__(self, mem_start_addr:int, mem_end_addr:int, memory_size:int = 65536):
        self.memory_size = memory_size
        self.mem_start_addr = mem_start_addr
        self.mem_end_addr = mem_end_addr
        self.variables = {}
        self.addresses = {}
        self.mem_var_size = self.mem_start_addr - self.mem_end_addr
    
    def create_variable(self, var_name:str, var_type:VarTypes, var_value)-> Variable:
        if var_type not in VarTypes:
            raise ValueError(f"Unsupported variable type: {var_type}")
        
        if not self.__validate_variable_name(var_name):
            raise ValueError(f"Invalid variable name: {var_name}")
        
        if self.check_variable_exists(var_name):
            raise ValueError(f"Variable '{var_name}' already exists.")

        proper_address = self.__find_free_address(var_type.value.get_size())
        if proper_address is None:
            raise MemoryError(f"Not enough memory to create variable '{var_name}' of type '{var_type.name}'")

        new_var = var_type.value(name=var_name, address=proper_address, value=var_value)
        self.variables[var_name] = new_var
        self.addresses[proper_address] = new_var

        return new_var

    def create_array_variable(self, var_name:str, var_type:VarTypes, array_len:int, var_value:list[int]) -> Variable:
        if not self.__validate_variable_name(var_name):
            raise ValueError(f"Invalid variable name: {var_name}")

        if self.check_variable_exists(var_name):
            raise ValueError(f"Variable '{var_name}' already exists.")

        proper_address = self.__find_free_address(array_len*var_type.value.get_size())
        if proper_address is None:
            raise MemoryError(f"Not enough memory to create variable '{var_name}' of type '{var_type.name}'")

        new_var = var_type.value(name=var_name, address=proper_address, size=array_len, value=var_value)
        self.variables[var_name] = new_var
        for offset in range(array_len):
            self.addresses[proper_address + offset] = new_var

        return new_var

    def __find_free_address(self, var_size:int) -> int|None:
        for addr in range(self.mem_start_addr, self.mem_end_addr - var_size + 1):
            is_free = True
            for offset in range(var_size):
                if (addr + offset) in self.addresses:
                    is_free = False
                    break
            if is_free:
                return addr

    def get_variable_from_address(self, address:int) -> Variable|None:
        if address < self.mem_start_addr or address > self.mem_end_addr:
            raise ValueError(f"Address {address} is out of bounds.")

        return self.addresses.get(address, None)
    
    def get_variable(self, var_name:str) -> Variable:
        if var_name not in self.variables:
            raise ValueError(f"Variable '{var_name}' does not exist.")
        return self.variables[var_name]

    def print_memory(self, start_addr:int = None, end_addr:int = None, int_type:IntTypes=IntTypes.HEX) -> None:
        start_addr = start_addr if start_addr is not None else self.mem_start_addr
        end_addr = end_addr if end_addr is not None else self.mem_end_addr

        val_str = "{:04X}" 
        if int_type == IntTypes.DECIMAL:
                val_str = "{:04d}"
        elif int_type == IntTypes.BINARY:
            val_str = "{:016b}"
        elif int_type == IntTypes.HEX:
            val_str = "{:04X}"
            
        for addr in range(start_addr, end_addr+1):
            var = self.get_variable_from_address(addr)
            print(f"{addr:04X}: {val_str.format(var.value if var else 0)}")

    
    def free_variable(self, var_name:str) -> None:
        if var_name not in self.variables:
            raise ValueError(f"Variable '{var_name}' does not exist.")
        
        var:Variable = self.variables[var_name]
        del self.variables[var_name]
        del self.addresses[var.address]
        

    def check_variable_exists(self, var_name:str) -> bool:
        return var_name in self.variables
    
    def __validate_variable_name(self, var_name:str) -> bool:
        return var_name.isidentifier()

if __name__ == "__main__":
    vm = VarManager(mem_start_addr=0, mem_end_addr=0x0100)

    var = vm.create_variable("test", VarTypes.BYTE, 42)
    vm.print_memory(0, 10, IntTypes.HEX)
    print(var)