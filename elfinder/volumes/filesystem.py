import os, re, time, shutil, inspect, magic
from tarfile import TarFile
from PIL import Image
from elfinder.exceptions import ElfinderErrorMessages, NotAnImageError
from elfinder.utils.archivers import ZipFileArchiver
from base import ElfinderVolumeDriver

class ElfinderVolumeLocalFileSystem(ElfinderVolumeDriver):
    """
    elFinder driver for local filesystem.
    """
    
    _driverId = 'l'
    
    def __init__(self):
        super(ElfinderVolumeLocalFileSystem, self).__init__()
        
        #Required to count total archive files size
        self._archiveSize = 0
        
        self._options['alias']    = '' #alias to replace root dir_ name
        self._options['dirMode']  = 0755 #new dirs mode
        self._options['fileMode'] = 0644 #new files mode
        self._options['quarantine'] = '.quarantine' #quarantine folder name - required to check archive (must be hidden)
        self._options['maxArcFilesSize'] = 0 #max allowed archive files size (0 - no limit)
        
    #*********************************************************************#
    #*                        INIT AND CONFIGURE                         *#
    #*********************************************************************#
    
    def configure(self):
        """
        Configure after successfull mount.
        """
        self._aroot = os.path.realpath(self._root)
        root = self.stat(self._root)

        if self._options['quarantine']:
            self._attributes.append({
                'pattern' : r'^%s$' % re.escape('%s%s' % (self._separator, self._options['quarantine'])),
                'read' : False,
                'write' : False,
                'locked' : True,
                'hidden': True
            })

        #chek thumbnails path
        if self._options['tmbPath']:
            #tmb path set as dirname under root dir if it doe not contain a separator
            self._options['tmbPath'] = '%s%s%s' % (self._root, self._separator, self._options['tmbPath']) if not self._separator in self._options['tmbPath'] else self._normpath(self._options['tmbPath']) 

        super(ElfinderVolumeLocalFileSystem, self).configure()

        #if no thumbnails url - try to detect it
        if root['read'] and not self._tmbURL and self._URL:
            if self._tmbPath.startswith(self._root):
                self._tmbURL = self._URL + self._tmbPath[len(self._root)+1:].replace(self._separator, '/')
                if re.search("[^/?&=]$", self._tmbURL):
                    self._tmbURL += '/'

        #check quarantine dir
        if self._options['quarantine']:
            self._quarantine = '%s%s%s' % (self._root, self._separator, self._options['quarantine'])
            isdir = os.path.isdir(self._quarantine)
            
        if not self._options['quarantine'] or (isdir and not os.access(self._quarantine, os.W_OK)):
            self._archivers['extract'] = []
            self._disabled.append('extract')
        elif self._options['quarantine'] and not isdir:
            try:
                self._mkdir(self._root, self._options['quarantine'])
            except os.error:
                self._archivers['extract'] = []
                self._disabled.append('extract')
            
    #*********************************************************************#
    #*                               FS API                              *#
    #*********************************************************************#
    
    def _dirname(self, path):
        """
        Return parent directory path
        """
        return os.path.dirname(path)

    def _basename(self, path):
        """
        Return file name
        """
        return os.path.basename(path)

    def _joinPath(self, dir_, name):
        """
        Join dir name and file name and return full path
        """
        return os.path.join(dir_, name)
    
    def _normpath(self, path):
        """
        Return normalized path
        """
        return os.path.normpath(path)
    
    def _relpath(self, path):
        """
        Return file path related to root dir
        """
        return '' if path == self._root else path[len(self._root)+1:]
    
    def _abspath(self, path):
        """
        Convert path related to root dir into real path
        """
        return self._root if path == self._separator else self._joinPath(self._root, path)
    
    def _path(self, path):
        """
        Return fake path started from root dir
        """
        return self._rootName if path == self._root else self._joinPath(self._rootName, self._relpath(path))
    
    def _inpath(self, path, parent):
        """
        Return True if path is children of parent
        """
        try:
            return path == parent or path.startswith('%s%s' % (parent, self._separator))
        except:
            return False
    
    #***************** file stat ********************#

    def _stat(self, path):
        """
        Return stat for given path.
        If file does not exist, it returns empty array or False.
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
        """
        stat = {}

        if path != self._root and os.path.islink(path):
            target = self._readlink(path)
            if not target or target == path:
                stat['mime']  = 'symlink-broken'
                stat['read']  = False
                stat['write'] = False
                stat['size']  = 0
                return stat
            stat['alias']  = self._path(target)
            stat['target'] = target
            path  = target
            size  = os.lstat(path).st_size
        else:
            size = os.path.getsize(path)
        
        dir_ = os.path.isdir(path)
        
        stat['mime']  = 'directory' if dir_ else self.mimetype(path)
        stat['ts'] = os.path.getmtime(path)
        stat['read']  = os.access(path, os.R_OK)
        stat['write'] = os.access(path, os.W_OK)
        if stat['read']:
            stat['size'] = 0 if dir_ else size
        return stat
    
    def _subdirs(self, path):
        """
        Return True if path is dir and has at least one childs directory
        """
        for entry in os.listdir(path):
            p = path+self._separator+entry
            if os.path.isdir(entry) and not self.attr(path=p, name='hidden'):
                return True
        return False
    
    def _dimensions(self, path, mime):
        """
        Return object width and height
        Ususaly used for images, but can be realize for video etc...
        Can Raise a NotAnImageError
        """
        if mime.startswith('image'):
            try:
                im = Image.open(path)
                return '%sx%s' % im.size
            except:
                pass
        raise NotAnImageError
    
    #******************** file/dir content *********************#
    def _mimetype(self, path):
        """
        Attempt to read the file's mimetype
        """
        return magic.Magic(mime=True).from_file(path)
    
    def _readlink(self, path):
        """
        Return symlink target file
        """
        target = os.readlink(path)
        try:
            if target[0] != self._separator:
                target = os.path.dirname(path)+self._separator+target
        except TypeError:
            return None
        
        atarget = os.path.realpath(target)
        if self._inpath(atarget, self._aroot):
            return self._normpath(self._root+self._separator+atarget[len(self._aroot)+1:])      

    def _scandir(self, path):
        """
        Return files list in directory.
        The '.' and '..' special directories are ommited.
        """
        return map(lambda x: u'%s%s%s' % (path, self._separator, x), os.listdir(path))

    def _fopen(self, path, mode='rb'):
        """
        Open file and return file pointer
        """
        return open(path, mode)
    
    def _fclose(self, fp, **kwargs):
        """
        Close opened file
        """
        return fp.close()
    
    #********************  file/dir manipulations *************************#
    
    def _mkdir(self, path, name, mode=None):
        """
        Create dir and return created dir path or raise an os.error
        """
        path = u'%s%s%s' % (path, self._separator, name)
        os.mkdir(path, mode) if mode else os.mkdir(path, self._options['dirMode']) 
        return path

    def _mkfile(self, path, name):
        """
        Create file and return it's path or False on failed
        """
        path = u'%s%s%s' % (path, self._separator, name)

        open(path, 'w').close()
        os.chmod(path, self._options['fileMode'])
        return path

    def _symlink(self, source, targetDir, name):
        """
        Create symlink
        """
        return os.symlink(source, u'%s%s%s' % (targetDir, self._separator, name))

    def _copy(self, source, targetDir, name):
        """
        Copy file into another file
        """
        return shutil.copy(source, u'%s%s%s' % (targetDir, self._separator, name))

    def _move(self, source, targetDir, name):
        """
        Move file into another parent dir.
        Return new file path or False.
        """
        target = u'%s%s%s' % (targetDir, self._separator, name)
        return target if os.rename(source, target) else False

    def _unlink(self, path):
        """
        Remove file
        """
        return os.unlink(path)

    def _rmdir(self, path):
        """
        Remove dir
        """
        return os.rmdir(path)

    def _save(self, fp, dir_, name, mime, **kwargs):
        """
        Create new file and write into it from file pointer.
        Return new file path or False on error.
        """
        path = u'%s%s%s' % (dir_, self._separator, name)
        target = open(path, 'wb')
        
        read = fp.read(8192)
        while read:
            target.write(read)
            read = fp.read(8192)

        target.close()
        os.chmod(path, self._options['fileMode'])
        
        return path
    
    def _save_uploaded(self, uploaded_file, dir_, name, **kwargs):
        """
        Save the django UploadedFile object and return its new path
        """
        path = u'%s%s%s' % (dir_, self._separator, name)
        target = self._fopen(path, 'wb+')        
        for chunk in uploaded_file.chunks():
            target.write(chunk)
        target.close()
        os.chmod(path, self._options['fileMode'])
        
        return path
    
    def _getContents(self, path):
        """
        Get file contents
        """
        return open(path).read()

    def _filePutContents(self, path, content):
        """
        Write a string to a file.
        """
        f = open(path, 'w')
        f.write(content)
        f.close()

    def _checkArchivers(self):
        """
        Detect available archivers
        """
        self._archivers = {
            'create'  : { 'application/x-tar' : { 'ext' : 'tar' , 'archiver' : TarFile }, 
                         'application/x-gzip' : { 'ext' : 'tgz' , 'archiver' : TarFile },
                         'application/x-bzip2' : { 'ext' : 'tbz' , 'archiver' : TarFile },
                         'application/zip' : { 'ext' : 'zip' , 'archiver' : ZipFileArchiver }
                         },
            'extract' : { 'application/x-tar' : { 'ext' : 'tar' , 'archiver' : TarFile }, 
                         'application/x-gzip' : { 'ext' : 'tgz' , 'archiver' : TarFile },
                         'application/x-bzip2' : { 'ext' : 'tbz' , 'archiver' : TarFile },
                         'application/zip' : { 'ext' : 'zip' , 'archiver' : ZipFileArchiver }
                         }
        }
        
        #control available archive types from the options
        if 'archiveMimes' in self._options and self._options['archiveMimes']:
            for mime in self._archivers['create']:
                if not mime in self._options['archiveMimes']:
                    del self._archivers['create'][mime]
        
        #manualy add archivers
        if 'create' in self._options['archivers']:
            for mime, archiver in self._options['archivers']['create'].items():
                try:
                    conf = archiver['archiver']
                    archiver['ext']
                except:
                    continue
                #check if conf is class and implements open, add and close methods
                if not re.match(r'application/', mime) is None and inspect.isclass(conf) and hasattr(conf, 'open') and callable(getattr(conf, 'open')) and hasattr(conf, 'add') and callable(getattr(conf, 'add')) and hasattr(conf, 'close') and callable(getattr(conf, 'close')):
                    self._archivers['create'][mime] = archiver

        if 'extract' in self._options['archivers']:
            for mime, archiver in self._options['archivers']['extract'].items():
                try:
                    conf = archiver['archiver']
                    archiver['ext']
                except:
                    continue
                #check if conf is class and implements open, extractall and close methods
                if not re.match(r'application/', mime) is None and inspect.isclass(conf) and hasattr(conf, 'open') and callable(getattr(conf, 'open')) and hasattr(conf, 'extractall') and callable(getattr(conf, 'extractall')) and hasattr(conf, 'close') and callable(getattr(conf, 'close')):
                    self._archivers['extract'][mime] = archiver

    def _archive(self, dir_, files, name, arc):
        """
        Create archive and return its path
        """
        try:
            archiver = arc['archiver']
        except KeyError:
            raise Exception('Invalid archiver')
        
        cwd = os.getcwd()
        os.chdir(dir_)
        
        try:
            archive = archiver.open(name, "w")
            for file_ in files:
                archive.add(file_)
            archive.close()
        except:
            raise Exception('Could not create archive')

        os.chdir(cwd)
        path = u'%s%s%s' % (dir_, self._separator, name)
        
        if not os.path.isfile(path):
            raise Exception('Could not create archive')

        return path

    def _unpack(self, path, arc):
        """
        Unpack archive
        """
        try:
            archiver = arc['archiver']
        except KeyError:
            raise Exception('Invalid archiver')

        cwd = os.getcwd()
        dir_ = self._dirname(path)
        os.chdir(dir_)
        
        try:
            archive = archiver.open(path)
            archive.extractall()
            archive.close()
        except:
            raise Exception('Could not create archive')

        os.chdir(cwd)

    def _findSymlinks(self, path):
        """
        Recursive symlinks search
        """
        if os.path.islink(path):
            return True
        
        if os.path.isdir(path):
            for name in self._scandir(path):
                p = u'%s%s%s' % (path, self._separator, name)
                if os.path.islink(p) or not self.nameAccepted(name):
                    return True
                elif os.path.isdir(p) and self._findSymlinks(p):
                    return True
                elif os.path.isfile(p):
                    self._archiveSize += os.path.getsize(p)
        else:    
            self._archiveSize += os.path.getsize(path)

        return False

    def _extract(self, path, arc):
        """
        Extract files from archive
        """
        basename = self._basename(path)
        dirname = self._dirname(path)

        if self._quarantine:
            dir_name = u'%s%s' % (str(time.time()).replace(' ', '_'), basename)
            dir_ = u'%s%s%s' % (self._quarantine, self._separator, dir_name)
            archive = u'%s%s%s' % (dir_, self._separator, basename)
            
            self._mkdir(self._quarantine, dir_name)
            os.chmod(dir_, 0777)
            
            #copy in quarantine
            self._copy(path, dir_, basename)
            
            #extract in quarantine
            self._unpack(archive, arc)
            self._unlink(archive)
            
            #get files list
            ls = self._scandir(dir_)
            
            #no files - extract error ?
            if not ls:
                self.remove(dir_)
                return
            
            self._archiveSize = 0;
            
            #find symlinks
            symlinks = self._findSymlinks(dir_)
            #remove arc copy
            self.remove(dir_)
            
            if symlinks:
                raise Exception(ElfinderErrorMessages.ERROR_ARC_SYMLINKS)

            #check max files size
            if self._options['maxArcFilesSize'] > 0 and self._options['maxArcFilesSize'] < self._archiveSize:
                raise Exception(ElfinderErrorMessages.ERROR_ARC_MAXSIZE)

            #archive contains one item - extract in archive dir
            if len(ls) == 1:
                self._unpack(path, arc)
                result = u'%s%s%s' % (dirname, self._separator, self._basename(ls[0]))
            else:
                #for several files - create new directory
                #create unique name for directory
                name = basename
                m =re.search('/\.((tar\.(gz|bz|bz2|z|lzo))|cpio\.gz|ps\.gz|xcf\.(gz|bz2)|[a-z0-9]{1,4})$/i', name) 
                if m and m.group(0):
                    name = name[0:(len(name)-len(m.group(0)))]

                test = u'%s%s%s' % (dirname, self._separator, name)
                if os.path.exists(test) or os.path.islink(test):
                    name = self.uniqueName(dirname, name, '-', False)
                
                result  = u'%s%s%s' % (dirname, self._separator, name)
                archive = u'%s%s%s' % (result, self._separator, basename)

                self._mkdir(dirname, name)
                self._copy(path, result, basename)
                
                self._unpack(archive, arc)
                self._unlink(archive)

            if not os.path.exists(result):
                raise Exception('Could not extract archive')
            
            return result