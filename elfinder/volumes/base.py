import os, re, datetime, time, sys, mimetypes
from PIL import Image
from base64 import b64encode, b64decode
from string import maketrans
from hashlib import md5
from django.core.cache import cache
from django.utils.translation import ugettext as _
from elfinder.exceptions import ElfinderErrorMessages, FileNotFoundError, DirNotFoundError, PermissionDeniedError, NamedError, NotAnImageError

class ElfinderVolumeDriver(object):
    """
    The base volume finder. Every elfinder volume driver should subclass this.
    """
    
    #The driver id.
    #Must be started from letter and contains [a-z0-9]
    #Used as part of volume id
    _driverId = 'a'
    
    #Directory separator - required by client
    _separator = os.sep
    
    #Mimetypes allowed to display
    _onlyMimes = []
    
    #Store files movedsubstr( or overwrited files info
    _removed = []
    
    #Cache by folders
    _dirsCache = []
    
    #*********************************************************************#
    #*                            INITIALIZATION                         *#
    #*********************************************************************#
    
    def __init__(self):
        """
        Default constructor
        """

        #Volume id - used as prefix for files hashes
        self._id = ''
        #Flag - volume "mounted" and available
        self._mounted = False
        #Root directory path
        self._root = ''
        #Root basename | alias
        self._rootName = ''
        #Default directory to open
        self._startPath = ''
        #Base URL
        self._URL = ''
        #Thumbnails dir path
        self._tmbPath = ''
        #Is thumbnails dir writable
        self._tmbPathWritable = False
        #Thumbnails base URL
        self._tmbURL = ''
        #Thumbnails size in px
        self._tmbSize = 48
        #Archivers config
        self._archivers = {
            'create' : {},
            'extract' : {}
        }
        #How many subdirs levels return for tree
        self._treeDeep = 1
        #Today 24:00 timestamp
        self._today = 0
        #Yesterday 24:00 timestamp
        self._yesterday = 0
        #A name pattern to ise for validitatinf path names
        self._nameValidator = None
        #Object configuration
        self._options = {
            'id' : '',
            #root directory path
            'path' : '',
            #root url, not set to disable sending URL to client (replacement for old "fileURL" option)
            'URL' : '',
            #open this path on initial request instead of root path
            'startPath' : '',
            #how many subdirs levels return per request
            'treeDeep' : 1,
            #directory separator. required by client to show paths correctly
            'separator' : os.sep,
            #directory for thumbnails
            'tmbPath' : '.tmb',
            #mode to create thumbnails dir
            'tmbPathMode' : 0777,
            #thumbnails dir URL. Set it if store thumbnails outside root directory
            'tmbURL' : '',
            #thumbnails size (px)
            'tmbSize' : 48,
            #thumbnails crop (True - crop, False - scale image to fit thumbnail size)
            'tmbCrop' : True,
            #thumbnails background color (hex #rrggbb or 'transparent')
            'tmbBgColor' : '#ffffff',
            #on paste file -  if True - old file will be replaced with new one, if False new file get name - original_name-number.ext
            'copyOverwrite' : True,
            #if True - join new and old directories content on paste
            'copyJoin' : True,
            #on upload -  if True - old file will be replaced with new one, if False new file get name - original_name-number.ext
            'uploadOverwrite' : True,
            #filter mime types to show
            'onlyMimes' : [],
            #mimetypes allowed to upload
            'uploadAllow' : [],
            #mimetypes not allowed to upload
            'uploadDeny' : [],
            #order to proccess uploadAllow and uploadDeny options
            'uploadOrder' : ['deny', 'allow'],
            #maximum upload file size. NOTE - this is size for every uploaded files
            'uploadMaxSize' : 0,
            #files dates format. CURRENTLY NOT IMPLEMENTED
            'dateFormat' : 'j M Y H:i',
            #files time format. CURRENTLY NOT IMPLEMENTED
            'timeFormat' : 'H:i',
            #if True - every folder will be check for children folders, otherwise all folders will be marked as having subfolders
            'checkSubfolders' : True,
            #allow to copy from this volume to other ones?
            'copyFrom' : True,
            #allow to copy from other volumes to this one?
            'copyTo' : True,
            #list of commands disabled on this root
            'disabled' : [],
            #regexp or function name to validate new file name
            'acceptedName' : r'^[^\.].*', #<-- DONT touch this! Use constructor options to overwrite it!
            #callable to control file permissions
            'accessControl' : None,
            #default permissions. not set hidden/locked here - take no effect
            'defaults' : {
                'read' : True,
                'write' : True
            },
            #files attributes
            'attributes' : [],
            #Allowed archive's mimetypes to create. Leave empty for all available types.
            'archiveMimes' : [],
            #Manual config for archivers. See example below. Leave empty for auto detect
            'archivers' : {},
        }

        #Defaults permissions
        self._defaults = {
            'read' : True,
            'write' : True,
            'locked' : False,
            'hidden' : False
        }
        #Access control function/class
        self._attributes = []
        #Access control function/class
        self._access = None
        #Mime types allowed to upload
        self._uploadAllow = []
        #Mime types denied to upload
        self._uploadDeny = []
        #Order to validate uploadAllow and uploadDeny
        self._uploadOrder = []
        #Maximum allowed upload file size.
        #Set as number or string with unit - "10M", "500K", "1G"
        self._uploadMaxSize = 0
        #List of disabled client's commands
        self._disabled = []
    
    def init(self):
        """
        Prepare driver before mount volume.
        Return True if volume is ready.
        """
        return True
        
    def configure(self):
        """
        Configure after successfull mount.
        By default set thumbnails path.
        Thumbnails are stored in local filesystem regardless of the volume
        """
        #set thumbnails path
        path = self._options['tmbPath']
        if path:
            try:
                stat = self.stat(path)
            except os.error:
                split = path.split(self._separator)
                try:
                    self._mkdir(path=self._separator.join(split[:-1]), name=split[-1], mode=self._options['tmbPathMode'])
                    stat = self.stat(path)
                except os.error:
                    stat = None
            
            if stat and stat['mime'] == 'directory' and stat['read']:
                self._tmbPath = path
                self._tmbPathWritable = stat['write']
                
    def _cachekeys(self):
        """
        Get volume cachekeys as a tuple
        """
        return ('%selfinder_dirs_cache' % self.id(),
        '%selfinder_stats_cache' % self.id())
                
    #*********************************************************************#
    #*                              PUBLIC API                           *#
    #*********************************************************************#
    
    def name(self):
        """
        Return driver name.
        """
        return self.__class__.__name__[len('elfinderdriver'):].lower()
    
    def driverId(self):
        """
        Return driver id. Used as a part of volume id.
        """
        return self._driverId
    
    def id(self):
        """
        Return volume id
        """
        return self._id
        
    def debug(self):
        """
        Return debug info for client
        """
        return {
            'id' : self.id(),
            'name' : self.name(),
        }
    
    def mount(self, opts):
        """
        "Mount" volume.
        Return True if volume available for read or write,
        False - otherwise
        """
        if not 'path' in opts or not opts['path']:
            raise Exception(_('Path undefined.'))
        
        
        self._options.update(opts)
        if self._options['id']:
            self._id = '%s%s_' % (self._driverId, self._options['id'])
        else:
            raise Exception(_('No volume id found'))
        
        self._root = self._normpath(self._options['path'])
        self._separator = self._options['separator'] if 'separator' in self._options else os.sep

        #default file attribute
        self._defaults = {
            'read' : self._options['defaults']['read'] if 'read' in self._options['defaults'] else True,
            'write' : self._options['defaults']['write'] if 'write' in self._options['defaults'] else True,
            'locked' : False,
            'hidden' : False
        }

        #root attributes
        self._attributes.append( {
            'pattern' : r'^%s$' % re.escape(self._separator),
            'locked' : True,
            'hidden' : False
        })

        #set files attributes
        if self._options['attributes']:
            for a in self._options['attributes']:
                #attributes must contain pattern and at least one rule
                if 'pattern' in a and len(a) > 1:
                    self._attributes.append(a)
        
        self._access = self._options['accessControl']
        self._today = time.mktime(datetime.date.today().timetuple())
        self._yesterday = self._today-86400

        self.init()

        #assign some options to private members
        self._onlyMimes = self._options['onlyMimes']
        self._uploadAllow = self._options['uploadAllow'] if 'uploadAllow' in self._options else []
        self._uploadDeny = self._options['uploadDeny'] if 'uploadDeny' in self._options else []
        self._uploadOrder = self._options['uploadOrder']
            
        try:
            unit = self._options['uploadMaxSize'][-1].lower()
            n = 1
            if unit == 'k':
                n = 1024
            elif unit == 'm':
                n = 1048576
            elif unit == 'g':
                n = 1073741824
            self._uploadMaxSize = int(self._options['uploadMaxSize'][:-1]) * n
        except TypeError:
            pass
        
        self._disabled = self._options['disabled'] if 'disabled' in self._options else []    
        self._rootName = self._basename(self._root) if not self._options['alias'] else self._options['alias']
        
        try:
            root = self.stat(self._root)
        except os.error:
            #attempt to create it
            self._mkdir(self._separator.join(self._root.split(self._separator)[:-1]), self._basename(self._root))
            root = self.stat(self._root)
            raise DirNotFoundError

        if (not 'read' in root or not root['read']) and (not 'write' in root and not root['write']):
            raise PermissionDeniedError
        
        if 'read' in root and root['read']:
            #check startPath - path to open by default instead of root
            if self._options['startPath']:
                try:
                    startpath = self._joinPath(self._root, self._options['startPath'])
                    start = self.stat(startpath)
                    if start['mime'] == 'directory' and start['read'] and not self.isHidden(start):
                        self._startPath = startpath
                        if startpath[-1] == self._options['separator']:
                            self._startPath = startpath[:-1]
                except os.error:
                    #Fail silently if startPath does not exist
                    pass
        else:
            self._options['URL'] = ''
            self._options['tmbURL'] = ''
            self._options['tmbPath'] = ''
            #read only volume
            self._attributes.insert(0, {
                'pattern' : r'.*',
                'read' : False
            })

        self._treeDeep = int(self._options['treeDeep']) if int(self._options['treeDeep']) > 0 else 1
        self._tmbSize  = int(self._options['tmbSize']) if int(self._options['tmbSize']) > 0 else 48
        self._URL = self._options['URL']
        if self._URL and re.search(r"[^/?&=]$", self._URL):
            self._URL += '/'

        self._tmbURL = self._options['tmbURL'] if self._options['tmbURL'] else ''
        if self._tmbURL and re.search(r"[^/?&=]$", self._tmbURL):
            self._tmbURL += '/'
        
        self._nameValidator = self._options['acceptedName'] if 'acceptedName' in self._options and self._options['acceptedName'] else None

        self._checkArchivers()
        self.configure()
        self._mounted = True
    
    def unmount(self):
        """
        Some "unmount" stuff - may be required by virtual fs
        """
        pass
    
    def setMimesFilter(self, mimes):
        """
        Set mimetypes allowed to display to client
        """
        self._onlyMimes = mimes

    def root(self):
        """
        Return root folder hash
        """
        return self.encode(self._root)
    
    def defaultPath(self):
        """
        Return root or startPath hash
        """
        return self.encode(self._startPath if self._startPath else self._root)
    
    def options(self, hash_):
        """
        Return volume options required by client
        """
        return {
            'path' : self._path(self.decode(hash_)),
            'url' : self._URL,
            'tmbUrl' : self._tmbURL,
            'disabled' : self._disabled,
            'separator' : self._separator,
            'copyOverwrite' : self._options['copyOverwrite'],
            'archivers' : {
                'create' : self._archivers['create'].keys(),
                'extract' : self._archivers['extract'].keys()
            }
        }
    
    def commandDisabled(self, cmd):
        """
        Return True if command disabled in options
        """
        return cmd in self._disabled
    
    def mimeAccepted(self, mime, mimes = [], empty = True):
        """
        Return True if mime is in required mimes list
        """
        mimes = mimes if mimes else self._onlyMimes
        if not mimes:
            return empty

        return mime == 'directory' or 'all' in mimes or 'All' in mimes or mime in mimes or mime[0:mime.find('/')] in mimes
    
    def isReadable(self):
        """
        Return True if volume is readable.
        """
        return self.stat(self._root)['read']
    
    def copyFromAllowed(self):
        """
        Return True if copy from this volume allowed
        """
        return self._options['copyFrom']
    
    def path(self, hash_):
        """
        Return file path related to root
        """
        return self._path(self.decode(hash_))
    
    def realpath(self, hash_):
        """
        Return file real path if file exists
        """
        path = self.decode(hash_)
        self.stat(path)
        return path
    
    def removed(self):
        """
        Return list of moved/overwrited files
        """
        return self._removed
    
    def resetRemoved(self):
        """
        Clean removed files list
        """
        self._removed = []
    
    def closest(self, hash_, attr, val):
        """
        Return file/dir hash or first founded child hash with 
        required attr == val
        """
        path = self.closestByAttr(self.decode(hash_), attr, val)
        return self.encode(path) if path else False
    
    def file(self, hash_):
        """
        Return file info or False on error. Raises a FileNotFoundError if file was not found
        """
        try:
            return self.stat(self.decode(hash_))
        except os.error:
            raise FileNotFoundError

    def dir(self, hash_, resolveLink=False):
        """
        Return folder info. Raises a DirNotFoundError if hash_ path is not a directory, 
        or FileNotFoundError if the hash_  path is not a valid file at all
        """

        dir_ = self.file(hash_)
        if resolveLink and 'thash' in dir_ and dir_['thash']:
            dir_ = self.file(dir_['thash'])
            
        if dir_['mime'] != 'directory' or self.isHidden(dir_):
            raise DirNotFoundError
        
        return dir_
    
    def scandir(self, hash_):
        """
        Return directory content or False on error. 
        Raises a DirNotFoundError if hash_ is not a valid dir, 
        or a PermissionDenied Error if the user cannot access the data
        """
        if not self.dir(hash_)['read']:
            raise PermissionDeniedError            
        return self.getScandir(self.decode(hash_))

    def ls(self, hash_):
        """
        Return dir files names list. Raises
        PermissionDeniedError, FileNotFoundError, DirNotFoundError
        """
        if not self.dir(hash_)['read']:
            raise PermissionDeniedError
        
        list_ = []
        path = self.decode(hash_)
       
        for stat in self.getScandir(path):
            if not self.isHiddden(stat) and self.mimeAccepted(stat['mime']):
                list_.append(stat['name'])

        return list_

    def tree(self, hash_='', deep=0, exclude=''):
        """
        Return subfolders for required folder or False on error
        """
        path = self.decode(hash_) if hash_ else self._root
        
        dir_ = self.stat(path)
        if dir_['mime'] != 'directory':
            return []
        
        dirs = self.gettree(path, (deep - 1) if deep > 0 else (self._treeDeep - 1), self.decode(exclude) if exclude else None)
        dirs[:0] = [dir_]
        return dirs
    
    def parents(self, hash_):
        """
        Return part of dirs tree from required dir up to root dir
        Raises DirNotFoundError, FileNotFoundError, PermissionDenied
        """
        current = self.dir(hash_)
        path = self.decode(hash_)
        tree = []
        
        while path and path != self._root:
            path = self._dirname(path)
            stat = self.stat(path)
            if self.isHidden(stat) or not stat['read']:
                raise PermissionDeniedError
            
            tree[:0] = [stat]
            if path != self._root:
                for dir_ in self.gettree(path, 0):
                    if not dir_ in tree:
                        tree.append(dir_)

        return tree if tree else [current]
    
    def tmb(self, hash_):
        """
        Create thumbnail for required file and return its name or None on fail.
        Will raise exception upon fail.
        """
        path = self.decode(hash_)

        try:
            stat = self.stat(path)
        except os.error:
            raise FileNotFoundError

        if 'tmb' in stat:
            return self.createTmb(path, stat) if stat['tmb'] == 1 else stat['tmb']
    
    def size(self, hash_):
        """
        Return file size / total directory size
        """
        return self.countSize(self.decode(hash_))
    
    def open(self, hash_):
        """
        Open file for reading and return file pointer
        """
 
        if self.file(hash_)['mime'] == 'directory':
            raise FileNotFoundError
        
        return self._fopen(self.decode(hash_), 'rb')
    
    def close(self, fp, hash_):
        """
        Close file pointer
        """
        self._fclose(fp, path=self.decode(hash_))

    def mkdir(self, dst, name):
        """
        Create directory and return dir info
        """

        if self.commandDisabled('mkdir'):
            raise PermissionDeniedError
        
        if not self.nameAccepted(name):
            raise Exception(ElfinderErrorMessages.ERROR_INVALID_NAME)
        
        try:
            dir_ = self.dir(dst) 
        except (FileNotFoundError, DirNotFoundError):
            raise NamedError(ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND, '#%s' % dst)
        
        if not dir_['write']:
            raise PermissionDeniedError
        
        path = self.decode(dst)
        dst  = self._joinPath(path, name)
        
        try:
            self.stat(dst)
            raise NamedError(ElfinderErrorMessages.ERROR_EXISTS, name)
        except:
            self.clearcache()

        return self.stat(self._mkdir(path, name))
    
    def mkfile(self, dst, name):
        """
        Create empty file and return its info
        """

        if self.commandDisabled('mkfile'):
            raise PermissionDeniedError
        
        if not self.nameAccepted(name):
            raise Exception(ElfinderErrorMessages.ERROR_INVALID_NAME)
        
        try:
            dir_ = self.dir(dst)
        except (FileNotFoundError, DirNotFoundError):
            raise NamedError(ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND, '#%s' % dst)
        
        path = self.decode(dst)
        if not dir_['write'] or not self.allowCreate(path, name):
            raise PermissionDeniedError
        
        try:
            self.stat(self._joinPath(path, name))
            raise NamedError(ElfinderErrorMessages.ERROR_EXISTS, name)
        except os.error:
            pass
    
        self.clearcache()
        return self.stat(self._mkfile(path, name))

    def rename(self, hash_, name):
        """
        Rename file and return file info
        """

        if self.commandDisabled('rename'):
            raise PermissionDeniedError
        
        if not self.nameAccepted(name):
            raise Exception(ElfinderErrorMessages.ERROR_INVALID_NAME)
        
        file_ = self.file(hash_)
        
        if name == file_['name']:
            return file_
        
        if self.isLocked(file_):
            raise NamedError(ElfinderErrorMessages.ERROR_LOCKED, file_['name'])
        
        path = self.decode(hash_)
        dir_  = self._dirname(path)
        try:
            self.stat(self._joinPath(dir_, name))
            raise NamedError(ElfinderErrorMessages.ERROR_EXISTS, name)
        except os.error:
            pass
        
        if not self.allowCreate(dir_, name):
            return PermissionDeniedError

        self.rmTmb(file_) #remove old name tmbs, we cannot do this after dir move
        self._move(path, dir_, name)
        path = self._joinPath(dir_, name)
        self.clearcache()

        return self.stat(path)

    def duplicate(self, hash_, suffix='copy'):
        """
        Create file copy with suffix "copy number" and return its info
        """

        if self.commandDisabled('duplicate'):
            raise PermissionDeniedError
        
        #check if source file exists, throw FileNotFoundError if it doesn't
        self.file(hash_)

        path = self.decode(hash_)
        dir_  = self._dirname(path)
        name = self.uniqueName(dir_, self._basename(path), ' %s ' % suffix)

        if not self.allowCreate(dir_, name):
            raise PermissionDeniedError

        return self.stat(self.copy(path, dir_, name))
    
    def upload(self, uploaded_file, dst):
        """
        Save uploaded file. 
        On success return array with new file stat and with removed file hash (if existed file was replaced)
        """
        
        #TODO: Check if after replacing calls to _save(), mimetype(), the methods are no longer needed

        if self.commandDisabled('upload'):
            raise PermissionDeniedError
        
        try:
            dir_ = self.dir(dst)
        except (FileNotFoundError, DirNotFoundError):
            raise NamedError(ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND, '#%s' % dst)

        if not dir_['write']:
            raise PermissionDeniedError
        
        if not self.nameAccepted(uploaded_file.name):
            raise Exception(ElfinderErrorMessages.ERROR_INVALID_NAME)
        
        mime = uploaded_file.content_type 

        #logic based on http://httpd.apache.org/docs/2.2/mod/mod_authz_host.html#order
        allow = self.mimeAccepted(mime, self._uploadAllow, None)
        deny   = self.mimeAccepted(mime, self._uploadDeny, None)
        if self._uploadOrder[0].lower() == 'allow': #['allow', 'deny'], default is to 'deny'
            upload = False #default is deny
            if not deny and allow == True: #match only allow
                upload = True
            #else: (both match | no match | match only deny): deny
        else: #['deny', 'allow'], default is to 'allow' - this is the default rule
            upload = True #default is allow
            if deny == True and not allow: #match only deny
                upload = False
            #else: (both match | no match | match only allow): allow }
        
        if not upload:
            raise Exception(ElfinderErrorMessages.ERROR_UPLOAD_FILE_MIME)

        if self._uploadMaxSize > 0 and uploaded_file.size > self._uploadMaxSize:
            raise Exception(ElfinderErrorMessages.ERROR_UPLOAD_FILE_SIZE)

        dstpath = self.decode(dst)
        name = uploaded_file.name
        test = self._joinPath(dstpath, name)

        try:
            file_ = self.stat(test)
            #file exists
            self.clearcache()
            if self._options['uploadOverwrite']:
                if not file_['write']:
                    raise PermissionDeniedError
                elif file_['mime'] == 'directory':
                    raise NamedError(ElfinderErrorMessages.ERROR_NOT_REPLACE, uploaded_file.name)
                self.remove(test)
            else:
                name = self.uniqueName(dstpath, uploaded_file.name, '-', False)
        except os.error: #file does not exist
            pass
        
        kwargs = {}
        try:
            im = Image.open(uploaded_file.temporary_file_path)
            (kwargs['w'], kwargs['h']) = im.size
        except:
            pass #file is not an image

        #self.clearcache()
        return self.stat(self._save_uploaded(uploaded_file, dstpath, name, **kwargs))
    
    def paste(self, volume, src, dst, rmSrc = False):
        """
        Paste files
        """
        
        if self.commandDisabled('paste'):
            raise PermissionDeniedError

        #check if src file exists, throw FileNotFoundError if it doesn't
        file_ = volume.file(src)
        name = file_['name']
        errpath = volume.path(src)
        
        try:
            dir_ = self.dir(dst)
        except (FileNotFoundError, DirNotFoundError):
            raise NamedError(ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND, '#%s' % dst)
        
        if not dir_['write'] or not file_['read']:
            raise PermissionDeniedError

        destination = self.decode(dst)

        test = volume.closest(src, 'locked' if rmSrc else 'read', rmSrc)
        if test:
            raise NamedError(ElfinderErrorMessages.ERROR_LOCKED, volume.path(test)) if rmSrc else PermissionDeniedError

        test = self._joinPath(destination, name)
        try:
            stat = self.stat(test)
            #file exists
            self.clearcache()
            if self._options['copyOverwrite']:
                #do not replace file with dir or dir with file
                if not self.isSameType(file_['mime'], stat['mime']):
                    raise NamedError(ElfinderErrorMessages.ERROR_NOT_REPLACE, self._path(test))
                #existed file is not writable
                if not stat['write']:
                    raise PermissionDeniedError()
                #existed file locked or has locked child
                locked = self.closestByAttr(test, 'locked', True)
                if locked:
                    raise NamedError(ElfinderErrorMessages.ERROR_LOCKED, self._path(locked))
                #target is entity file of alias
                if volume == self and (test == file_['target'] or test == self.decode(src)):
                    raise NamedError(ElfinderErrorMessages.ERROR_REPLACE, errpath)
                #remove existed file
                if not self.remove(test):
                    raise NamedError(ElfinderErrorMessages.ERROR_REPLACE, self._path(test))
            else:
                name = self.uniqueName(destination, name, ' ', False)
        except os.error:
            pass
        
        #copy/move inside current volume
        if (volume == self):
            source = self.decode(src)
            #do not copy into itself
            if self._inpath(destination, source):
                raise NamedError(ElfinderErrorMessages.ERROR_COPY_ITSELF, errpath)
            if rmSrc:
                path = self.move(source, destination, name)
            else:
                path = self.copy(source, destination, name)
            return self.stat(path)
        
        #copy/move from another volume
        if not self._options['copyTo'] or not volume.copyFromAllowed():
            raise PermissionDeniedError()
        
        path = self.copyFrom(volume, src, destination, name)
        
        if rmSrc:
            try:
                volume.rm(src)
                self._removed.append(file_)
            except:
                raise Exception(ElfinderErrorMessages.ERROR_RM_SRC)

        return self.stat(path)

    def getContents(self, hash_):
        """
        Return file contents
        """

        file_ = self.file(hash_)
        
        if file_['mime'] == 'directory':
            raise Exception(ElfinderErrorMessages.ERROR_NOT_FILE)
        
        if not file_['read']:
            raise PermissionDeniedError()
        
        return self._getContents(self.decode(hash_))
    
    def putContents(self, hash_, content):
        """
        Put content in text file and return file info.
        """
        if self.commandDisabled('edit'):
            raise PermissionDeniedError()
        
        path = self.decode(hash_)
        file_ = self.file(hash_)
        
        if not file_['write']:
            raise PermissionDeniedError()

        self.clearcache()
        self._filePutContents(path, content)
        return self.stat(path)
    
    def extract(self, hash_):
        """
        Extract files from archive
        """

        if self.commandDisabled('extract'):
            raise PermissionDeniedError()
        
        file_ = self.file(hash_)

        archiver = self._archivers['extract'][file_['mime']] if file_['mime'] in self._archivers['extract'] else False
        if not archiver:
            raise Exception(ElfinderErrorMessages.ERROR_NOT_ARCHIVE)
        
        path = self.decode(hash_)
        parent = self.stat(self._dirname(path))

        if not file_['read'] or not parent['write']:
            raise PermissionDeniedError()

        self.clearcache()
        path = self._extract(path, archiver)
        return self.stat(path)

    def archive(self, hashes, mime):
        """
        Add files to archive
        """

        if self.commandDisabled('archive'):
            raise PermissionDeniedError()

        archiver = self._archivers['create'][mime] if mime in self._archivers['create'] else False
        if not archiver:
            raise Exception(ElfinderErrorMessages.ERROR_ARCHIVE_TYPE)
        
        files = []
        for hash_ in hashes:
            file_ = self.file(hash_)
            
            if not file_['read']:
                raise PermissionDeniedError()

            path = self.decode(hash_)
            try: #check if dir_ is set
                dir_ #@UndefinedVariable
            except:
                dir_ = self._dirname(path)
                stat = self.stat(dir_)
                if not stat['write']:
                    raise PermissionDeniedError()

            files.append(self._basename(path))
        
        name = '%s.%s' % (files[0] if len(files) == 1 else 'Archive', archiver['ext'])
        name = self.uniqueName(dir_, name, '')
        
        self.clearcache()
        path = self._archive(dir_, files, name, archiver)
        return self.stat(path)

    def resize(self, hash_, width, height, x, y, mode = 'resize', bg = '', degree = 0):
        """
        Resize image
        """

        if self.commandDisabled('resize'):
            raise PermissionDeniedError()
        
        file_ = self.file(hash_)
        
        if not file_['write'] or not file_['read']:
            raise PermissionDeniedError()
        
        path = self.decode(hash_)
        if not self.canResize(path, file_):
            raise Exception(ElfinderErrorMessages.ERROR_UNSUPPORT_TYPE)

        if mode == 'propresize':
            result = self.imgResize(path, width, height, True, True)
        elif mode == 'crop':
            result = self.imgCrop(path, width, height, x, y)
        elif mode == 'fitsquare':
            result = self.imgSquareFit(path, width, height, bg if bg else self._options['tmbBgColor'])
        elif mode == 'rotate':
            result = self.imgRotate(path, degree, bg if bg else self._options['tmbBgColor'])
        else:
            result = self.imgResize(path, width, height, False, True)

        if result:
            self.rmTmb(file_)
            self.clearcache()
            return self.stat(path)
        
        raise Exception(_('Could not resize image'))

    def rm(self, hash_):
        """
        Remove file/dir
        """
        if self.commandDisabled('rm'):
            raise PermissionDeniedError()
        return self.remove(self.decode(hash_))
    
    def search(self, q, mimes):
        """
        Search files
        """
        return self.doSearch(self._root, q, mimes)

    def dimensions(self, hash_):
        """
        Return image dimensions.
        Raise FileNotFoundError or NotAnImageError
        """
        return self._dimensions(self.decode(hash_), self.file(hash_)['mime'])
        
    #*********************************************************************#
    #*                               FS API                              *#
    #*********************************************************************#
    
    #***************** paths *******************#
    
    def encode(self, path):
        """
        Encode path into hash
        """
        if path:
            #cut ROOT from path for security reason, even if hacker decodes the path he will not know the root
            #files hashes will also be valid, even if root changes
            p = self._relpath(path)
            #if reqesting root dir path will be empty, then assign '/' as we cannot leave it blank for crypt
            if not p:
                p = self._separator

            #TODO: crypt path and return hash
            hash_ = self.crypt(p)
            #hash is used as id in HTML that means it must contain vaild chars
            #make base64 html safe and append prefix in begining
            hash_ = b64encode(hash_).translate(maketrans('+/=', '-_.'))

            #remove dots '.' at the end (used to be '=' in base64, before the translation)
            hash_ = hash_.rstrip('.')

            #append volume id to make hash unique
            return self.id()+hash_
    
    def decode(self, hash_):
        """
        Decode path from hash
        """
        if hash_.startswith(self.id()):
            #cut volume id after it was prepended in encode
            h = hash_[len(self.id()):]
            #replace HTML safe base64 to normal
            h = h.encode('ascii').translate(maketrans('-_.', '+/='))
            #put cut = at the end
            h += "=" * ((4 - len(h) % 4) % 4)
            h = b64decode(h)
            #TODO: uncrypt hash and return path
            path = self.uncrypt(h) 
            #append ROOT to path after it was cut in encode
            return self._abspath(path) 
        return ''
    
    def crypt(self, path):
        """
        Return crypted path 
        Not implemented
        """
        return path
    
    def uncrypt(self, hash_):
        """
        Return uncrypted path 
        Not implemented
        """
        return hash_
    
    def nameAccepted(self, name):
        """
        Validate file name based on self._options['acceptedName'] regexp
        """
        if self._nameValidator:
            return re.search(self._nameValidator, name)
        return True

    def uniqueName(self, dir_, name, suffix = ' copy', checkNum=True):
        """
        Return new unique name based on file name and suffix
        """
        ext  = ''
        m = re.search(r'\.((tar\.(gz|bz|bz2|z|lzo))|cpio\.gz|ps\.gz|xcf\.(gz|bz2)|[a-z0-9]{1,4})$', name, re.IGNORECASE)
        if m:
            ext  = '.%s' % m.group(1)
            name = name[0:len(name)-len(m.group(0))] 
        
        m = re.search('(%s)(\d*)$' % suffix, name, re.IGNORECASE)
        if checkNum and m and m.group(2):
            i = int(m.group(2))
            name = name[0:len(name)-len(m.group(2))]
        else:
            i = 1
            name += suffix

        max_ = i+100000
        while i <= max_:
            n = '%s%s%s' % (name, (i if i > 0 else ''), ext)
            try:
                self.stat(self._joinPath(dir_, n))
            except os.error:
                self.clearcache()
                return n
            i+=1

        return name+md5(dir_)+ext
    
    #*********************** file stat *********************#
    
    def attr(self, path, name, val=None):
        """
        Check file attribute
        """
        if not name in self._defaults:
            return False

        perm = None
        #TODO: replace this with signals??
        if self._access:
            if hasattr(self._access, '__call__'):
                perm = self._access(name, path, self)

            if perm != None:
                return perm

        path = self._relpath(path).replace(self._separator, '/')
        path = u'/%s' % path

        for attrs in self._attributes:
            if name in attrs and 'pattern' in attrs and re.search(attrs['pattern'], path):
                perm = attrs[name]
        
        return (self._defaults[name] if not val else val) if not perm else perm

    def allowCreate(self, dir_, name):
        """
        Return ``True`` if file with given ``name`` can be created in the ``dir_`` folder.
        """
        path = self._joinPath(dir_, name)
        perm = None
        
        if self._access:
            if hasattr(self._access, '__call__'):
                perm = self._access(name, path, self)
            
            if perm != None:
                return perm
        
        testPath = self._separator+self._relpath(path)
        
        for i in range(0, len(self._attributes)):
            attrs = self._attributes[i]
            if 'write' in attrs and 'pattern' in attrs and re.search(attrs['pattern'], testPath):
                perm = attrs['write']

        return True if perm is None else perm

    def stat(self, path):
        """
        Return fileinfo. Raises os.error if the path is invalid
        """
        statCache = cache.get(self._cachekeys()[1], {})
        if not path in statCache:
            self.updateCache(path, self._stat(path), statCache)
            cache.set(self._cachekeys()[1], statCache)
        return statCache[path]

    def updateCache(self, path, stat, statCache):
        """
        Put file stat in cache and return it
        """
        if not stat:
            statCache[path] = {}
            return

        stat['hash'] = self.encode(path)
        root = (path == self._root)
        if root:
            stat['volumeid'] = self.id()
            if self._rootName:
                stat['name'] = self._rootName
        else:
            if not 'name' in stat or not stat['name']:
                stat['name'] = self._basename(path)

            if not 'phash' in stat or not stat['phash']:
                stat['phash'] = self.encode(self._dirname(path))

        if not 'mime' in stat or not stat['mime']:
            stat['mime'] = self.mimetype(stat['name'])
            
        if not 'size' in stat or (not stat['size'] and stat['mime'] == 'directory'):
            stat['size'] = 'unknown'

        stat['read'] = int(self.attr(path=path, name='read', val=stat['read'] if 'read' in stat else None))
        stat['write'] = int(self.attr(path=path, name='write', val=stat['write'] if 'write' in stat else None))

        if root:
            stat['locked'] = 1
        elif self.attr(path=path, name='locked', val=self.isLocked(stat)):
            stat['locked'] = 1
        elif 'locked' in stat:
            del stat['locked']

        if root and 'hidden' in stat:
            del stat['hidden']
        elif self.attr(path=path, name='hidden', val=self.isHidden(stat)) or not self.mimeAccepted(stat['mime']):
            stat['hidden'] = 0 if root else 1
        elif 'hidden' in stat:
            del stat['hidden']

        if stat['read'] and not self.isHidden(stat):
            if stat['mime'] == 'directory':
                #for dir - check for subdirs
                if self._options['checkSubfolders']:
                    if 'dirs' in stat:
                        if stat['dirs']:
                            stat['dirs'] = 1
                        else:
                            del stat['dirs']
                    elif 'alias' in stat and stat['alias'] and 'target' in stat and stat['target']:
                        stat['dirs'] = int('dirs' in statCache[stat['target']]) if stat['target'] in statCache else self._subdirs(stat['target']) 
                    elif self._subdirs(path):
                        stat['dirs'] = 1
                else:
                    stat['dirs'] = 1
            else:
                #for files - check for thumbnails
                p = stat['target'] if 'target' in stat else path
                if self._tmbURL and not 'tmb' in stat and self.canCreateTmb(p, stat):
                    tmb = self.gettmb(p, stat)
                    stat['tmb'] = tmb if tmb else 1
        
        if 'alias' in stat and stat['alias'] and 'target' in stat and stat['target']:
            stat['thash'] = self.encode(stat['target'])
            del stat['target']

        statCache[path] = stat

    def cacheDir(self, path):
        """
        Get stat for folder content and put in cache
        """
        dirsCache = cache.get(self._cachekeys()[0], {})
        dirsCache[path] = []

        for p in self._scandir(path):
            stat = self.stat(p)
            if not self.isHidden(stat):
                dirsCache[path].append(p)
        cache.set(self._cachekeys()[0], dirsCache)
        return dirsCache[path]

    def getDirsCache(self, path):
        """
        Returns the cached dictionary for this path
        """
        dirsCache = cache.get(self._cachekeys()[0], {})
        return dirsCache[path] if path in dirsCache else []

    def clearcache(self):
        """
        Clean cached directory stat info
        """
        for cachekey in self._cachekeys():
            cache.delete(cachekey)

    def mimetype(self, path, name = ''):
        """
        Return file mimetype.  
        """
        mime = self._mimetype(path)
        int_mime = None

        if not mime or mime in ['inode/x-empty', 'application/empty']:
            int_mime = self.mimetypeInternalDetect(name if name else path)
                
        return int_mime if int_mime else mime

    def mimetypeInternalDetect(self, path):
        """
        Detect file mimetype using "internal" method
        """
        return mimetypes.guess_type(path)[0]
    
    def countSize(self, path):
        """
        Return file/total directory size
        """
        try:
            stat = self.stat(path)
        except os.error:
            #used to return 'unknown' but 0 is more suitable for adding sizes
            return 0  
        
        if not stat['read'] or self.isHidden(stat):
            #used to return 'unknown' but 0 is more suitable for adding sizes
            return 0
        
        if stat['mime'] != 'directory':
            return stat['size']
        
        subdirs = self._options['checkSubfolders']
        self._options['checkSubfolders'] = True
        result = 0
        for stat in self.getScandir(path):
            size = self.countSize(self._joinPath(path, stat['name'])) if stat['mime'] == 'directory' and stat['read'] else stat['size']
            if (size > 0):
                result += size

        self._options['checkSubfolders'] = subdirs
        return result

    def isSameType(self, mime1, mime2):
        """
        Return True if all mimes is directory or files
        """
        return (mime1 == 'directory' and mime1 == mime2) or (mime1 != 'directory' and mime2 != 'directory')

    def closestByAttr(self, path, attr, val):
        """
        If file has required attr == val - return file path,
        If dir has child with has required attr == val - return child path
        """
        try:
            stat = self.stat(path)
        except os.error:
            return False
        
        v = stat[attr] if attr in stat else False
        if v == val:
            return path

        return self.childsByAttr(path, attr, val) if stat['mime'] == 'directory' else False

    def childsByAttr(self, path, attr, val):
        """
        Return first found children with required attr == val
        """
        for p in self._scandir(path):
            _p = self.closestByAttr(p, attr, val)
            if _p != False:
                return _p
        return False

    #*****************  get content *******************#

    def getScandir(self, path):
        """
        Return required directory files info.
        If onlyMimes is set - return only dirs and files of required mimes
        """
        files = []
        dirsCache = self.getDirsCache(path)
        if not dirsCache:
            dirsCache = self.cacheDir(path)

        for p in dirsCache:
            stat = self.stat(p)
            if not self.isHidden(stat):
                files.append(stat)

        return files

    def gettree(self, path, deep, exclude=''):
        """
        Return subdirs tree
        """
        dirs = []
        
        dirsCache = self.getDirsCache(path)
        if not dirsCache:
            dirsCache = self.cacheDir(path)

        for p in dirsCache:
            stat = self.stat(p)
            if not self.isHidden(stat) and p != exclude and stat['mime'] == 'directory':
                dirs.append(stat)
                if deep > 0 and 'dirs' in stat and stat['dirs']:
                    dirs += self.gettree(p, deep-1)
        return dirs

    def doSearch(self, path, q, mimes):
        """
        Recursive files search
        """
        result = []
        for p in self._scandir(path):
            try:
                stat = self.stat(p)
            except os.error: #invalid links
                continue

            if self.isHidden(stat) or not self.mimeAccepted(stat['mime']):
                continue
            
            name = stat['name']

            if q in name:
                stat['path'] = self._path(p)
                if self._URL and not 'url' in stat:
                    stat['url'] = self._URL + p[len(self._root) + 1:].replace(self._separator, '/')
                result.append(stat)

            if stat['mime'] == 'directory' and stat['read'] and not 'alias' in  stat:
                result += self.doSearch(p, q, mimes)

        return result
        
    #**********************  manipulations  ******************#

    def copy(self, src, dst, name):
        """
        Copy file/recursive copy dir only in current volume.
        Return new file path or False.
        """

        srcStat = self.stat(src)
        self.clearcache()
        
        if 'thash' in srcStat and srcStat['thash']:           
            target = self.decode(srcStat['thash'])
            stat = self.stat(target)
            self.clearcache()
            
            try:
                self._symlink(target, dst, name)
            except:
                raise NamedError(ElfinderErrorMessages.ERROR_COPY, self._path(src))
            
            return self._joinPath(dst, name)
        
        if srcStat['mime'] == 'directory':
            test = self.stat(self._joinPath(dst, name))
            
            if test['mime'] != 'directory': 
                raise NamedError(ElfinderErrorMessages.ERROR_COPY, self._path(src))
            
            try:
                self._mkdir(dst, name)
            except:
                raise NamedError(ElfinderErrorMessages.ERROR_COPY, self._path(src)) 
            
            dst = self._joinPath(dst, name)
            for stat in self.getScandir(src):
                if not self.isHidden(stat):
                    name = stat['name']
                    try:
                        self.copy(self._joinPath(src, name), dst, name)
                    except:
                        self.remove(dst, True) #fall back
                        return None

            self.clearcache()
            return dst 

        try:
            self._copy(src, dst, name)
        except:
            raise NamedError(ElfinderErrorMessages.ERROR_COPY, self._path(src))
        
        return self._joinPath(dst, name)

    def move(self, src, dst, name):
        """
        Move file
        Return new file path or False.
        """

        stat = self.stat(src)
        stat['realpath'] = src
        self.rmTmb(stat) #can not do rmTmb() after _move()
        self.clearcache()
        
        try:
            self._move(src, dst, name)
            self._removed.append(stat)
            return self._joinPath(dst, name)
        except:
            raise NamedError(ElfinderErrorMessages.ERROR_MOVE, self._path(src))

    def copyFrom(self, volume, src, destination, name):
        """
        Copy file from another volume.
        Return new file path or False.
        """ 

        try:
            source = volume.file(src)
        except FileNotFoundError:
            raise NamedError(ElfinderErrorMessages.ERROR_COPY, '#'.src, volume.error())
        
        errpath = volume.path(src)
        
        if not self.nameAccepted(source['name']):
            raise Exception(ElfinderErrorMessages.ERROR_INVALID_NAME)
                
        if not source['read']:
            raise PermissionDeniedError()
        
        if source['mime'] == 'directory':
            stat = self.stat(self._joinPath(destination, name))
            self.clearcache()
            if stat['mime'] != 'directory' and not self._mkdir(destination, name):
                raise NamedError(ElfinderErrorMessages.ERROR_COPY, errpath)
            
            path = self._joinPath(destination, name) 
            for entry in volume.scandir(src):
                if not self.copyFrom(volume, entry['hash'], path, entry['name']):
                    return False
        else:
            mime = source['mime']
            kwargs = { 'source' : source }

            if mime.startswith('image'):
                try:
                    dim = volume.dimensions(src)
                    s = dim.split('x')
                    kwargs['w'] = s[0]
                    kwargs['h'] = s[1]
                except NotAnImageError:
                    pass

            try:
                fp = volume.open(src)
                path = self._save(fp, destination, name, mime, **kwargs)
                volume.close(fp, src)
            except:
                raise NamedError(ElfinderErrorMessages.ERROR_COPY, errpath)
        
        return path

    def remove(self, path, force = False):
        """
        Remove file/ recursive remove dir
        """

        try:
            stat = self.stat(path)
        except os.error:
            raise NamedError(ElfinderErrorMessages.ERROR_RM, self._path(path))

        stat['realpath'] = path
        self.rmTmb(stat)
        self.clearcache()
        
        if not force and self.isLocked(stat):
            raise NamedError(ElfinderErrorMessages.ERROR_LOCKED, self._path(path))

        if stat['mime'] == 'directory':
            for p in self._scandir(path):
                self.remove(p)

            try:
                self._rmdir(path)
            except:
                raise NamedError(ElfinderErrorMessages.ERROR_RM, self._path(path))

        else:
            try:
                self._unlink(path)
            except:
                raise NamedError(ElfinderErrorMessages.ERROR_RM, self._path(path))

        self._removed.append(stat)
    
    #************************* thumbnails **************************#

    def tmbname(self, stat):
        """
        Return thumbnail file name for required file
        """
        return u'%s%s.png' % (stat['hash'], stat['ts'])

    def gettmb(self, path, stat):
        """
        Return thumnbnail name if exists
        """
        if self._tmbURL and self._tmbPath:
            #file itself thumnbnail
            if path.startswith(self._tmbPath):
                return self._basename(path)

            name = self.tmbname(stat)
            try:
                self.stat(u'%s%s%s' % (self._tmbPath, self._separator, name))
                return name
            except os.error:
                return None

    def canCreateTmb(self, path, stat):
        """
        Return True if thumnbnail for required file can be created
        """
        return self._tmbPathWritable and not path.startswith(self._tmbPath) and stat['mime'].startswith('image') 

    def canResize(self, path, stat):
        """
        Return True if required file can be resized.
        By default - the same as canCreateTmb
        """
        return self.canCreateTmb(path, stat)

    def createTmb(self, path, stat):
        """
        Create thumnbnail and return it's URL on success.
        Raises PermissionDeniedError, os.error, NotAnImageError
        """

        if not self.canCreateTmb(path, stat):
            raise PermissionDeniedError()

        name = self.tmbname(stat)
        self._copy(path, self._tmbPath, name)
        tmb  = u'%s%s%s' % (self._tmbPath, self._separator, name)

        tmbSize = self._tmbSize        
        try:
            im = Image.open(tmb)
            s = im.size
        except:
            self._unlink(tmb)
            raise NotAnImageError
    
        # If image smaller or equal thumbnail size - just fitting to thumbnail square 
        if s[0] <= tmbSize and s[1]  <= tmbSize:
            try:
                self.imgSquareFit(tmb, tmbSize, tmbSize, self._options['tmbBgColor'], 'png')
            except:
                self._unlink(tmb)
                raise
        elif self._options['tmbCrop']:

            #Resize and crop if image bigger than thumbnail
            if not ((s[0] > tmbSize and s[1] <= tmbSize) or (s[0] <= tmbSize and s[1] > tmbSize)) or (s[0] > tmbSize and s[1] > tmbSize):
                try:
                    self.imgResize(tmb, tmbSize, tmbSize, True, False, 'png')
                except:
                    self._unlink(tmb)
                    raise
                
            try: #reopen image to get its size
                im = Image.open(tmb)
            except:
                self.unlink(tmb)
                raise NotAnImageError
            
            s = im.size
            x = int((s[0] - tmbSize)/2) if s[0] > tmbSize else 0
            y = int((s[1] - tmbSize)/2) if s[1] > tmbSize else 0
            
            try:
                self.imgCrop(tmb, tmbSize, tmbSize, x, y, 'png')
            except:
                self.unlink(tmb)
                raise
        else:
            try:
                im.thumbnail((tmbSize, tmbSize), Image.ANTIALIAS)
                im.save(tmb, 'png')
                self.imgSquareFit(tmb, tmbSize, tmbSize, self._options['tmbBgColor'], 'png' )
            except:
                self._unlink(tmb)
                raise

        return name

    def imgResize(self, path, width, height, keepProportions = False, resizeByBiggerSide = True, destformat = None):
        """
        Resize image
        """
        try:
            im = Image.open(path)
            s = im.size
        except:
            raise NotAnImageError
    
        size_w = width
        size_h = height

        if keepProportions:
            orig_w, orig_h = s[0], s[1]
            
            #Resizing by biggest side
            if resizeByBiggerSide:
                if (orig_w > orig_h):
                    size_h = orig_h * width / orig_w
                    size_w = width
                else:
                    size_w = orig_w * height / orig_h
                    size_h = height
            elif orig_w > orig_h:
                size_w = orig_w * height / orig_h
                size_h = height
            else:
                size_h = orig_h * width / orig_w
                size_w = width

        resized = im.resize((size_w, size_h), Image.ANTIALIAS)
        resized.save(path, destformat if destformat else im.format)
        
        return path

    def imgCrop(self, path, width, height, x, y, destformat = None):
        """
        Crop image
        """
        try:
            im = Image.open(path)
        except:
            raise NotAnImageError

        cropped = im.crop((x, y, width+x, height+y))
        cropped.save(path, destformat if destformat else im.format)

        return path

    def imgSquareFit(self, path, width, height, bgcolor = '#0000ff', destformat = None):
        """
        Put image to square
        """
        try:
            im = Image.open(path)
        except:
            raise NotAnImageError

        bg = Image.new('RGB', (width, height), bgcolor)

        if im.mode == 'RGBA':
            bg.paste(im, ((width-im.size[0])/2, (height-im.size[1])/2), im)
        else: #do not use a mask if file is not in RGBA mode.
            bg.paste(im, ((width-im.size[0])/2, (height-im.size[1])/2))

        bg.save(path, destformat if destformat else im.format)

        return path

    def imgRotate(self, path, degree, bgcolor = '#ffffff', destformat = None):
        """
        Rotate image
        """
        try:
            tempim = Image.open(path)
            im = tempim.convert('RGBA')
        except:
            raise NotAnImageError

        rotated = im.rotate(angle=degree)
        bg = Image.new('RGB', rotated.size, bgcolor)
        
        result = Image.composite(rotated, bg, rotated)
        result.save(path, destformat if destformat else im.format)

        return path

    def rmTmb(self, stat):
        """
        Remove thumbnail, also remove recursively if stat is directory
        """
        if stat['mime'] == 'directory':
            for p in self._scandir(self.decode(stat['hash'])):
                self.rmTmb(self.stat(p))
        elif 'tmb' in stat and stat['tmb'] and stat['tmb'] != '1':
            tmb = '%s%s%s' % (self._tmbPath, self._separator, stat['tmb'])
            try:
                self.stat(tmb)
                self._unlink(tmb)
            except:
                pass
            self.clearcache()
    
    def isHidden(self, stat):
        """
        Check if the file/directory is hidden
        """
        return 'hidden' in stat and stat['hidden']

    def isLocked(self, stat):
        """
        Check if the file/directory is locked
        """
        return 'locked' in stat and stat['locked']
    
    #*********************************************************************#
    #*             API TO BE IMPLEMENTED IN SUB-CLASSES                  *#
    #*********************************************************************#
    
    def _dirname(self, path):
        """
        Return parent directory path
        """
        raise NotImplementedError

    def _basename(self, path):
        """
        Return file name
        """
        raise NotImplementedError

    def _joinPath(self, dir_, name):
        """
        Join dir name and file name and return full path.
        Some drivers (db) use int as path - so we give to concat path to driver itself
        """
        raise NotImplementedError

    def _normpath(self, path):
        """
        Return normalized path
        """
        raise NotImplementedError

    def _relpath(self, path):
        """
        Return file path related to root dir
        """
        raise NotImplementedError

    def _abspath(self, path):
        """
        Convert path related to root dir into real path
        """
        raise NotImplementedError

    def _path(self, path):
        """
        Return fake path started from root dir.
        Required to show path on client side.
        """
        raise NotImplementedError
     
    def _inpath(self, path, parent):
        """
        Return true if path is children of parent
        """
        raise NotImplementedError

    def _stat(self, path):
        """
        Return stat for given path.
        Stat contains following fields:
        - (int)    size    file size in b. required
        - (int)    ts      file modification time in unix time. required
        - (string) mime    mimetype. required for folders, others - optionally
        - (bool)   read    read permissions. required
        - (bool)   write   write permissions. required
        - (bool)   locked  is object locked. optionally
        - (bool)   hidden  is object hidden. optionally
        - (string) alias   for symlinks - link target path relative to root path. optionally
        - (string) target  for symlinks - link target path. optionally
        
        Must raise an os.error on fail
        """
        raise NotImplementedError

    #***************** file stat ********************#

    def _subdirs(self, path):
        """
        Return true if path is dir and has at least one childs directory
        """
        raise NotImplementedError

    def _dimensions(self, path, mime):
        """
        Return object width and height
        Ususaly used for images, but can be realize for video etc...
        """
        raise NotImplementedError
    
    #******************** file/dir content *********************#

    def _mimetype(self, path):
        """
        Attempt to read the file's mimetype
        """
        raise NotImplementedError

    def _scandir(self, path):
        """
        Return files list in directory
        """
        raise NotImplementedError

    def _fopen(self, path, mode="rb"):
        """
        Open file and return file pointer
        """
        raise NotImplementedError

    def _fclose(self, fp, **kwargs):
        """
        Close opened file
        """
        raise NotImplementedError
    
    #********************  file/dir manipulations *************************#

    def _mkdir(self, path, name):
        """
        Create dir and return created dir path or false on failed
        """
        raise NotImplementedError

    def _mkfile(self, path, name):
        """
        Create file and return it's path or false on failed
        """
        raise NotImplementedError

    def _symlink(self, source, targetDir, name):
        """
        Create symlink
        """
        raise NotImplementedError

    def _copy(self, source, targetDir, name):
        """
        Copy file into another file (only inside one volume)
        """
        raise NotImplementedError

    def _move(self, source, targetDir, name):
        """
        Move file into another parent dir.
        Return new file path or false.
        """
        raise NotImplementedError
    

    def _unlink(self, path):
        """
        Remove file
        """
        raise NotImplementedError

    def _rmdir(self, path):
        """
        Remove dir
        """
        raise NotImplementedError


    def _save(self, fp, dir_, name, mime, **kwargs):
        """
        Create new file and write into it from file pointer.
        Return the new file path
        """
        raise NotImplementedError
    
    def _save_uploaded(self, uploaded_file, dir_, name, **kwargs):
        """
        Save the django UploadedFile object and return its new path
        """
        raise NotImplementedError

    def _getContents(self, path):
        """
        Get file contents
        """
        raise NotImplementedError

    def _filePutContents(self, path, content):
        """
        Write a string to a file
        """
        raise NotImplementedError

    def _extract(self, path, arc):
        """
        Extract files from archive
        """
        raise NotImplementedError

    def _archive(self, dir_, files, name, arc):
        """
        Create archive and return its path
        """
        raise NotImplementedError

    def _checkArchivers(self):
        """
        Detect available archivers
        """
        raise NotImplementedError