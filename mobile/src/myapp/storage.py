#mobile/src/myapp/storage.py
print(">>> importing mobile/src/myapp/storage.py")
import toga
import time
import jwt
print(">>> importing mobile/src/myapp/storage.py done")

class SecureStorage:
    def __init__(self, app=None):
        self.app = app
        
        # Initialize tokens dictionary on the app if needed
        if app:
            # Initialize tokens storage on app
            if not hasattr(app, '_tokens'):
                app._tokens = {}
                print("#mobile/src/myapp/storage.py Created new _tokens dict on app")
            else:
                print(f"#mobile/src/myapp/storage.py App already has _tokens: {list(app._tokens.keys())}, access_token={self.app._tokens.get('access_token')}")
        
    def save_tokens(self, access, refresh, token_type='bearer'):
        print(f"#mobile/src/myapp/storage.py SecureStorage.save_tokens() called App instance: {self.app}")
        
        if not self.app:
            print("#mobile/src/myapp/storage.py WARNING: No app instance, tokens won't persist!")
            self.app = toga.App.app # Ensure this isn't None
            #return
        
        try:
            # Decode JWT to get expiration
            payload = jwt.decode(access, options={"verify_signature": False})
            exp = payload["exp"]
            print(f"#mobile/src/myapp/storage.py Token expires at: {exp} (current time: {time.time()})")
        except Exception as e:
            print(f"Could not decode token: {e}")
            exp = 0
        
        # Store as a dictionary
        self.app._tokens = {
            'access_token': access,
            'refresh_token': refresh,
            'token_type': token_type,
            'exp': exp            
        }
        # Save to app's _tokens dict
        #self.app._tokens.update({
        #    'access': access,
        #    'refresh': refresh,
        #    'exp': exp
        #})
        
        print(f"#mobile/src/myapp/storage.py Tokens saved to app._tokens. Keys: {list(self.app._tokens.keys())}, self.app._tokens={self.app._tokens}")
    
    def access_token(self):
        if self.app and hasattr(self.app, '_tokens'):
            token = self.app._tokens.get('access_token')
            print(f"#mobile/src/myapp/storage.py access_token() called. Found token: {token is not None}, self.app._tokens={self.app._tokens}")
            return token
        print("#mobile/src/myapp/storage.py access_token() called. No app or _tokens")
        return None
    
    def is_access_expired(self):
        if not self.app or not hasattr(self.app, '_tokens'):
            print("#mobile/src/myapp/storage.py is_access_expired(): No tokens, returning True")
            return True
        
        exp = self.app._tokens.get('exp', 0)
        is_expired = time.time() > exp - 30
        print(f"#mobile/src/myapp/storage.py is_access_expired(): exp={exp}, current={time.time()}, expired={is_expired}")
        return is_expired
        
    def refresh_token(self):
        if self.app and hasattr(self.app, '_tokens'):
            return self.app._tokens.get("refresh_token")
        return None
        
    def get_access(self):
        return self.access_token()
    
    def get_refresh(self):
        return self.refresh_token()
    
    @property
    def access(self):
        return self.get_access()
    
    @property
    def refresh(self):
        return self.get_refresh()
    
    def clear(self):
        """Clear stored tokens"""
        print(f"#mobile/src/myapp/storage.py clear() token: {self.app._tokens}")
        if self.app and hasattr(self.app, '_tokens'):
            self.app._tokens.clear()