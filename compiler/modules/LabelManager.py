class LabelManager:
    def __init__(self):
        self.labels = [""]
        self.current_if_count = 0

    def add_label(self, name: str):
        self.labels.append(name)

    def get_label(self, name: str) -> int | None:
        return name if name in self.labels else None

    def remove_label(self, name: str):
        if name in self.labels:
            self.labels.remove(name)

    def clear_labels(self):
        self.labels.clear()

    def create_if_label(self) -> str:
        self.current_if_count += 1
        label_name = f"if_{self.current_if_count}"
        self.add_label(label_name)
        return label_name
