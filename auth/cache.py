import os
import pickle
import time
from cryptography.fernet import Fernet
import requests

class CacheHandler:
    """
    A class to handle encryption, saving, and loading of cached data (cookies or tokens)
    for secure storage and retrieval.

    Attributes:
        cache_file (str): Path to the cache file where data will be stored.
        key_file (str): Path to the file containing the encryption key.
        domain (str): The domain for which the cache applies.
        encryption_key (bytes): The encryption key used for encrypting/decrypting data.
    """
        
    def __init__(self, cache_file, key_file, domain):
        """
        Initializes the CacheHandler instance.

        Args:
            cache_file (str): The file path to store cached data.
            key_file (str): The file path to store the encryption key.
            domain (str): The domain for which the cache will be used.
        """
                
        self.cache_file = cache_file
        self.key_file = key_file
        self.domain = domain
        self.encryption_key = self.load_gen_key()


    def load_gen_key(self) -> str:
        """
        Loads the encryption key from the key file or generates a new key if the file doesn't exist.

        If the key file exists, reads and returns the key. Otherwise, generates a new key,
        saves it to the key file, and returns it.

        Returns:
            bytes: The encryption key.
        """

        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as kf:
                return kf.read()     
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as kf:
                kf.write(key)
            return key
        

    def encrypt(self, data) -> bytes:
        """
        Encrypts the given data using the encryption key.

        Args:
            data (bytes): The data to be encrypted.

        Returns:
            bytes: The encrypted data.
        """

        encryptor = Fernet(self.encryption_key)
        return encryptor.encrypt(data)
    

    def decrypt(self, data) -> str:
        """
        Decrypts the given encrypted data using the encryption key.

        Args:
            data (bytes): The encrypted data to be decrypted.

        Returns:
            bytes: The decrypted data.
        """

        decryptor = Fernet(self.encryption_key)
        return decryptor.decrypt(data)
    

    def save_cache(self, username, data, data_type) -> None:
        """
        Saves encrypted cache data (cookies or tokens) to the cache file.

        Args:
            username (str): The username associated with the cache data.
            data (bytes): The data to be cached.
            data_type (str): The type of data being cached (e.g., 'cookies' or 'token').
        """

        cache_data = {
            'username': username,
            'data': data,
            'data_type': data_type,
            'timestamp': time.time()
        }
        serialized_data = pickle.dumps(cache_data)
        encrypted_data = self.encrypt(serialized_data)

        with open(self.cache_file, 'wb') as cf:
            cf.write(encrypted_data)


    def load_cache(self) -> dict|None:
        """
        Loads the cached data from the cache file, decrypts it, and returns it.

        Returns:
            dict: The decrypted cache data (if available).
            None: else
        """

        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'rb') as cf:
                data = cf.read()
                serialized_data = self.decrypt(data)
                return pickle.loads(serialized_data)
        
        return None
    

    def validate_cookies(self, cache_data) -> dict|None:
        """
        Validates if the provided cookie cache data is still valid.

        Args:
            cache_data (dict): The cached cookie data to validate.

        Returns:
            dict: Cookie dict if the cookie data is valid, None otherwise.
        """

        cookie_dict = None
        
        if cache_data:
            cookie_dict = cache_data['data']
            session = requests.Session()
            for name, value in cookie_dict.items():
                session.cookies.set(name, value)
            
        headers = {"Accept": "application/json; odata=verbose"}
        if session:
            endpoint = f"{self.domain}/_api/web/"
            response = session.get(endpoint, headers=headers)
            if response.status_code == 200:
                return cookie_dict
        return None
    

    def validate_token(self, cache_data) -> str|None:
        """
        Validates if the provided token cache data is still valid.

        Args:
            cache_data (dict): The cached token data to validate.

        Returns:
            bool: True if the token data is valid, False otherwise.
        """

        auth_token = None
        session = None
        headers = {"Accept": "application/json; odata=verbose"}
        
        if cache_data:
            auth_token = cache_data['data']
            headers.update({"Authorization": f"Bearer {auth_token}"})
            session = requests.Session()
        
        if session:
            endpoint = f"{self.domain}/_api/web/"
            response = session.get(endpoint, headers=headers)
            if response.status_code == 200:
                return auth_token
        return None

