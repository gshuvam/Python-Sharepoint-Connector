import os
import pickle
import time
from cryptography.fernet import Fernet
import requests

class CacheHandler:
    def __init__(self, cache_file, key_file, domain):
        self.cache_file = cache_file
        self.key_file = key_file
        self.domain = domain
        self.encryption_key = self.load_gen_key()

    def load_gen_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as kf:
                return kf.read()     
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as kf:
                kf.write(key)
            return key
        
    def encrypt(self, data):
        encryptor = Fernet(self.encryption_key)
        return encryptor.encrypt(data)
    
    def decrypt(self, data):
        decryptor = Fernet(self.encryption_key)
        return decryptor.decrypt(data)
    
    def save_cache(self, username, data, data_type):
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

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'rb') as cf:
                data = cf.read()
                serialized_data = self.decrypt(data)
                return pickle.loads(serialized_data)
        
        return None
    
    def validate_cookies(self, cache_data):
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
    
    def validate_token(self, cache_data):
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

