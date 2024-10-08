class Credentials:
    def __init__(self, username, password):
        """
        Encapsulate the username and password.
        
        Args:
            username(str): Username for authentication
            password(str): Password for authentication
        """
        self.username = username
        self.password = password