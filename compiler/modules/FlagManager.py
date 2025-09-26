class FlagManager:
    def __init__(self):
        self.eq_flag = False
        self.lt_flag = False
        self.gt_flag = False
        self.c_flag = False
        self.flags = {
            "EQ": self.eq_flag,
            "LT": self.lt_flag,
            "GT": self.gt_flag,
            "C" : self.c_flag
        }
    
    def set_last_operation():
        pass

