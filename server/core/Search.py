class SearchAssistCharList:
    def __init__(self, uid: int, status: str, chars: str, social_assist_char_list: str,
                 assist_char_list: str):
        self.uid = uid
        self.status = status
        self.chars = chars
        self.social_assist_char_list = social_assist_char_list
        self.assist_char_list = assist_char_list

    def get_uid(self):
        return self.uid

    def set_uid(self, uid):
        self.uid = uid

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status

    def get_chars(self):
        return self.chars

    def set_chars(self, chars):
        self.chars = chars

    def get_social_assist_char_list(self):
        return self.social_assist_char_list

    def set_social_assist_char_list(self, social_assist_char_list):
        self.social_assist_char_list = social_assist_char_list

    def get_assist_char_list(self):
        return self.assist_char_list

    def set_assist_char_list(self, assist_char_list):
        self.assist_char_list = assist_char_list


class SearchUidList:
    def __init__(self, uid: int, level: str):
        self.uid = uid
        self.level = level

    def get_uid(self):
        return self.uid

    def set_uid(self, uid):
        self.uid = uid

    def get_level(self):
        return self.level

    def set_level(self, level):
        self.level = level
