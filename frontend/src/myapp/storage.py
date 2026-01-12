# storage.py
import time
import jwt

class SecureStorage:
    def __init__(self, app=None):
        self.app = app
        
        # Initialize tokens dictionary on the app if needed
        if app:
            # Initialize tokens storage on app
            if not hasattr(app, '_tokens'):
                app._tokens = {}
                print("Created new _tokens dict on app")
            else:
                print(f"App already has _tokens: {list(app._tokens.keys())}")
        
    def save_tokens(self, access, refresh):
        print(f"SecureStorage.save_tokens() called")
        print(f"App instance: {self.app}")
        
        if not self.app:
            print("WARNING: No app instance, tokens won't persist!")
            return
        
        try:
            # Decode JWT to get expiration
            payload = jwt.decode(access, options={"verify_signature": False})
            exp = payload["exp"]
            print(f"Token expires at: {exp} (current time: {time.time()})")
        except Exception as e:
            print(f"Could not decode token: {e}")
            exp = 0
        
        # Save to app's _tokens dict
        self.app._tokens.update({
            'access': access,
            'refresh': refresh,
            'exp': exp
        })
        
        print(f"Tokens saved to app._tokens. Keys: {list(self.app._tokens.keys())}")
    
    def access_token(self):
        if self.app and hasattr(self.app, '_tokens'):
            token = self.app._tokens.get('access')
            print(f"access_token() called. Found token: {token is not None}")
            return token
        print("access_token() called. No app or _tokens")
        return None
    
    def is_access_expired(self):
        if not self.app or not hasattr(self.app, '_tokens'):
            print("is_access_expired(): No tokens, returning True")
            return True
        
        exp = self.app._tokens.get('exp', 0)
        is_expired = time.time() > exp - 30
        print(f"is_access_expired(): exp={exp}, current={time.time()}, expired={is_expired}")
        return is_expired
        
    def refresh_token(self):
        if self.app and hasattr(self.app, '_tokens'):
            return self.app._tokens.get("refresh")
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
        if self.app and hasattr(self.app, '_tokens'):
            self.app._tokens.clear()