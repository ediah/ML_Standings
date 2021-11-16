import time, os

class CacheManager:
    def __init__(self, filename, force_update = False):
        self.cache_dir = './cache/'
        self.cached_file = self.cache_dir + filename
        self.force_update = force_update
        self.max_lifetime = 60 * 60 * 3    # 3 часа
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
    def needUpdate(self):
        cache_exist = os.path.isfile(self.cached_file)
        need_update = False
        
        if cache_exist:
            lifetime = time.time() - os.path.getmtime(self.cached_file)
            need_update = (lifetime > self.max_lifetime)
            
        need_update = need_update or self.force_update
        
        return not (cache_exist and (not need_update))
            
    def read(self):
        with open(self.cached_file, 'r') as cache:
            data = cache.read()
        return data

    def write(self, data):
        with open(self.cached_file, 'w') as cache:
            cache.write(data) 
