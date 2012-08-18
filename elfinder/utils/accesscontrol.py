import os

class elFinderTestACL:
    def fsAccess(self, attr, path, data, volume):
        """
        Make dotfiles not readable, not writable, hidden and locked.
        Should return None to allow for original attr value, boolean otherwise
        """
        if os.path.basename(path) in ['.tmb', '.quarantine']:
            #keep reserved folder names intact
            return None
 
        if volume.name() == 'localfilesystem':
            if attr in ['read', 'write'] and os.path.basename(path).startswith('.'):
                return False