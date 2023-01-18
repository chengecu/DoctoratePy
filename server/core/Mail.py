class Mail:
    def __init__(self, id: int, name: str, _from: str, subject: str,
                 content: str, items: str):
        self.id = id
        self.name = name
        self._from = _from
        self.subject = subject
        self.content = content
        self.items = items

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_from(self):
        return self._from

    def set_from(self, _from):
        self._from = _from

    def get_subject(self):
        return self.subject

    def set_subject(self, subject):
        self.subject = subject

    def get_content(self):
        return self.content

    def set_content(self, content):
        self.content = content

    def get_items(self):
        return self.items

    def set_items(self, items):
        self.items = items
