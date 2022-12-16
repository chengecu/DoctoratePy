class Account:
    
    def __init__(self, uid: int, phone: str, password: str, secret: str, user: str,
                 mails: str, assist_char_list: str, friend: str, ban: int):
        self.uid = uid
        self.phone = phone
        self.password = password
        self.secret = secret
        self.user = user
        self.mails = mails
        self.assist_char_list = assist_char_list
        self.friend = friend
        self.ban = ban

    def get_uid(self):
        return self.uid

    def set_uid(self, uid):
        self.uid = uid

    def get_phone(self):
        return self.phone

    def set_phone(self, phone):
        self.phone = phone

    def get_password(self):
        return self.password

    def set_password(self, password):
        self.password = password

    def get_secret(self):
        return self.secret

    def set_secret(self, secret):
        self.secret = secret

    def get_user(self):
        return self.user

    def set_user(self, user):
        self.user = user

    def get_mails(self):
        return self.mails

    def set_mails(self, mails):
        self.mails = mails

    def get_assist_char_list(self):
        return self.assistCharList

    def set_assist_char_list(self, assist_char_list):
        self.assistCharList = assist_char_list

    def get_friend(self):
        return self.friend

    def set_friend(self, friend):
        self.friend = friend

    def get_ban(self):
        return self.ban

    def set_ban(self, ban):
        self.ban = ban
