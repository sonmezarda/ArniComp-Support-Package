from VariableManager import VarTypes, Variable

class StackManager():
    def __init__(self, start_addr:int=0x0100, end_addr:int=0x01FF):
        self.start_addr = start_addr
        self.end_addr = end_addr
        self.size = end_addr - start_addr 
        self.stack_pointer_addr = start_addr
        self.stack_pointer_val = start_addr+1
        self.stack = [None] * self.size

    def push(self, value:int|Variable):
        if self.stack_pointer_addr < self.end_addr:
            self.stack[self.stack_pointer_addr - self.start_addr] = value
            self.stack_pointer_val += 1
        else:
            raise Exception("Stack overflow")

    def pop(self) -> int|Variable:
        if self.stack_pointer_addr > self.start_addr:
            self.stack_pointer_val -= 1
            return self.stack[self.stack_pointer_addr - self.start_addr]
        else:
            raise Exception("Stack underflow")