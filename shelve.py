import json

class ShelveFile:
    def __init__(self, file):
        self._file=file
        self._data={}
        
    def __enter__(self):
        try:
            with open(self._file,'r') as f:
                try:
                    self._data=json.load(f)
                except ValueError:
                    self._data={}
        except OSError:
            self._data={}
                
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self._file,'w') as f:
            json.dump(self._data, f)
            
    def __getitem__(self,key):
        return self._data[key]
    
    def __setitem__(self,key,value):
        self._data[key]=value
        
    def __delitem__(self,key):
        del self._data[key]
        
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)
    
    def __contains__(self,key):
        return key in self._data
    
    def get(self,key,default=None):
        try:
            return self._data[key]
        except KeyError:
            return default