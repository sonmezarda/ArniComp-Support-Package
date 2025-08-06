class LabelManager:
    def __init__(self):
        self.labels = {}
        self.current_if_count = 0
        self.labelcount = 0

    def add_label(self, name: str, current_assembly_length: int):
        self.labels[name] = current_assembly_length - self.labelcount
        self.labelcount += 1

    def get_label(self, name: str) -> int | None:
        return self.labels[name] if name in self.labels else None

    def is_label_defined(self, name: str) -> bool:
        print(f"Checking if label '{name}' is defined: {'Yes' if name in self.labels else 'No'}")
        return name in self.labels.keys()
    
    def remove_label(self, name: str):
        if name in self.labels:
            del self.labels[name]
    def update_label_position(self, name: str, current_assembly_length: int):
        if name in self.labels:
            self.labels[name] = current_assembly_length - self.labelcount
        else:
            raise ValueError(f"Label '{name}' does not exist.")

    def clear_labels(self):
        self.labels.clear()

    def create_if_label(self, current_assembly_length: int) -> tuple[str, int]:
        self.current_if_count += 1
        label_name = f"if_{self.current_if_count}"
        self.add_label(label_name, current_assembly_length)
        return label_name, self.labels[label_name]
