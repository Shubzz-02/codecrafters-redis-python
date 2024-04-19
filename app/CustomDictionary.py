import time


class TTLDictionary:
    def __init__(self):
        self._data = {}

    def set(self, key, value, ttl=None):
        if ttl:
            expiration_time = time.time() + int(ttl) / 1000  # Convert milliseconds to seconds
        else:
            expiration_time = None
        self._data[key] = {'value': value, 'expiration_time': expiration_time}

    def get(self, key):
        if key not in self._data:
            return None
        item = self._data[key]
        if item['expiration_time'] is not None and item['expiration_time'] < time.time():
            del self._data[key]
            return None
        return item['value']

    def remove(self, key):
        if key in self._data:
            del self._data[key]

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.remove(key)
