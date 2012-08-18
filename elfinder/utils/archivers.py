from zipfile import ZipFile

class ZipFileArchiver(object):
    def __init__(self, *args, **kwargs):
        print args
        self.zipfile = ZipFile(*args, **kwargs)
    
    @classmethod
    def open(self, *args, **kwargs):
        return ZipFileArchiver(*args,**kwargs) 
    
    def add(self, *args, **kwargs):
        self.zipfile.write(*args, **kwargs)
    
    def extractall(self, *args, **kwargs):
        self.zipfile.extractall(*args, **kwargs)

    def close(self):
        self.zipfile.close()