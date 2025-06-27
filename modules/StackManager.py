from VariableManager import VarTypes

class StackManager():
    def __init__(self, mem_start_addr:int, memory_size:int = 65536):
        self.memory_size = memory_size
        self.mem_start_addr = mem_start_addr
        self.mem_end_addr = mem_start_addr + 255
        self.stack_pointer_addr = mem_start_addr # stack size = max 255
        self.current_address = mem_start_addr + 1

        self.__check_mem_bounds(self.stack_pointer_addr)
    
    def __check_mem_bounds(self, address:int) -> bool:
        if self.mem_end_addr <= self.mem_start_addr:
            raise ValueError("Memory end address must be greater than memory start address.")
        
        if self.mem_start_addr < 0 or self.mem_start_addr >= self.memory_size:
            raise ValueError("Memory start address must be within the bounds of the memory size.")
        
        if self.mem_start_addr + 255 >= self.memory_size:
            raise ValueError("Memory start address plus 255 must be within the bounds of the memory size.")

    def push(self, var_type:VarTypes=VarTypes.BYTE) -> int:
        var_size = var_type.value.get_size()
        if self.current_address + var_size > self.mem_end_addr:
            raise OverflowError("Stack overflow: Cannot push to stack beyond memory limit.")
        self.current_address += var_type.value.get_size()
        return self.current_address

    def pop(self, var_type:VarTypes=VarTypes.BYTE) -> int:
        var_size = var_type.value.get_size()
        if self.current_address - var_size < self.mem_start_addr:
            raise OverflowError("Stack underflow: Cannot pop from empty stack.")
        self.current_address -= var_type.value.get_size()
        return self.current_address
    
    