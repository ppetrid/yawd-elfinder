import os, re, time, shutil, magic
from hashlib import md5
from PIL import Image
from django.conf import settings
from elfinder.exceptions import ElfinderErrorMessages, NotAnImageError
from base import ElfinderVolumeDriver

class ElfinderVolumeLocalFileSystem(ElfinderVolumeDriver):
    """
    elFinder driver for local filesystem.
    """
    
    _driver_id = 'l'
    
    def __init__(self):
        """
        Override the original __init__ method to define some 
        ElfinderVolumeLocalFileSystem-specific options.
        """
        super(ElfinderVolumeLocalFileSystem, self).__init__()
        
        #Required to count total archive files size
        self._archiveSize = 0
        
        self._options['dirMode']  = 0755 #new dirs mode
        self._options['fileMode'] = 0644 #new files mode
        self._options['quarantine'] = '.quarantine' #quarantine folder name - required to check archive (must be hidden)
        
    #*********************************************************************#
    #*                        INIT AND CONFIGURE                         *#
    #*********************************************************************#
    
    def mount(self, opts):
        """
        Override the original mount method so that
        ``path`` and ``URL`` settings point to the ``MEDIA_ROOT``
        and ``MEDIA_URL`` Django settings by default.
        """

        if not 'path' in opts or not opts['path']:
            self._options['path'] = settings.MEDIA_ROOT
            
        if not 'URL' in opts or not opts['URL']:
            self._options['URL'] = settings.MEDIA_URL

        return super(ElfinderVolumeLocalFileSystem, self).mount(opts)
    
    def _configure(self):
        """
        Configure after successful mount.
        """
        self._aroot = os.path.realpath(self._root)

        if self._options['quarantine']:
            self._attributes.append({
                'pattern' : '^%s$' % re.escape('%s%s' % (self._separator, self._options['quarantine'])),
                'read' : False,
                'write' : False,
                'locked' : True,
                'hidden': True
            })

        super(ElfinderVolumeLocalFileSystem, self)._configure()

        #if no thumbnails url - try to detect it
        if not self._options['tmbURL'] and self._options['URL']:
            if self._options['tmbPath'].startswith(self._root):
                self._options['tmbURL'] = self._urlize(self._options['URL'] + self._options['tmbPath'][len(self._root)+1:].replace(self._separator, '/'))

        #check quarantine dir
        if self._options['quarantine']:
            self._quarantine = self._join_path(self._root, self._options['quarantine'])
            isdir = os.path.isdir(self._quarantine)

        if not self._options['quarantine'] or (isdir and not os.access(self._quarantine, os.W_OK)):
            self._archivers['extract'] = []
            self._options['disabled'].append('extract')
        elif self._options['quarantine'] and not isdir:
            try:
                self._mkdir(self._quarantine)
            except os.error:
                self._archivers['extract'] = []
                self._options['disabled'].append('extract')
            
    #*********************************************************************#
    #*                  API TO BE IMPLEMENTED IN SUB-CLASSES             *#
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

    def _join_path(self, path1, path2):
        """
        Join two paths and return full path. If the latter path is
        absolute, return it.
        """
        
        return os.path.join(path1, path2)
    
    def _normpath(self, path):
        """
        Return normalized path.
        """
        return os.path.normpath(path)
    
    def _get_available_name(self, dir_, name, ext, i):
        """
        Get an available name for this file name.
        """

        while i <= 10000:
            n = '%s%s%s' % (name, (i if i > 0 else ''), ext)
            if not os.path.exists(self._join_path(dir_, n)):
                return n
            i+=1

        return name+md5(dir_)+ext

    #************************* file/dir info *********************#

    def _stat(self, path):
        """
        Return stat for given path.
        Stat contains following fields:
        - (int)    size    file size in b. required
        - (int)    ts      file modification time in unix time. required
        - (string) mime    mimetype. required for folders, others - optionally
        - (bool)   read    read permissions. required
        - (bool)   write   write permissions. required
        - (string) alias   for symlinks - link target path relative to root path. optionally
        - (string) target  for symlinks - link target path. optionally
        
        Must raise an os.error on fail
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
        else: #raise os.error on fail
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
            p = self._join_path(path, entry)
            if os.path.isdir(p) and not self._attr(p, 'hidden'):
                return True
    
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
                target = self._join_path(self._dirname(path), target)
        except TypeError:
            return None
        
        atarget = os.path.realpath(target)
        if self._inpath(atarget, self._aroot):
            return self._normpath(self._join_path(self._root, atarget[len(self._aroot)+1:]))      

    def _scandir(self, path):
        """
        Return files list in directory.
        The '.' and '..' special directories are omitted.
        """
        return map(lambda x: self._join_path(path, x), os.listdir(path))

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
    
    def _openimage(self, path):
        """
        Open an image file.
        """
        return Image.open(path)
    
    def _saveimage(self, im, path, form):
        """
        Save an image file
        """
        im.save(path, form)
    
    #********************  file/dir manipulations *************************#
    
    def _mkdir(self, path, mode=None):
        """
        Create dir and return created dir path or raise an os.error
        """
        os.mkdir(path, mode) if mode else os.mkdir(path, self._options['dirMode']) 
        return path

    def _mkfile(self, path, name):
        """
        Create file and return it's path or False on failed
        """
        path = self._join_path(path, name)

        open(path, 'w').close()
        os.chmod(path, self._options['fileMode'])
        return path

    def _symlink(self, source, target_dir, name):
        """
        Create symlink
        """
        return os.symlink(source, self._join_path(target_dir, name))

    def _copy(self, source, target_dir, name):
        """
        Copy file into another file
        """
        return shutil.copy(source, self._join_path(target_dir, name))

    def _move(self, source, target_dir, name):
        """
        Move file into another parent dir.
        Return new file path or raise os.error.
        """
        target = self._join_path(target_dir, name)
        os.rename(source, target)
        return target
        
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

    def _save(self, fp, dir_, name, **kwargs):
        """
        Create new file and write into it from file pointer.
        Return new file path or False on error.
        """
        path = self._join_path(dir_, name)
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
        path = self._join_path(dir_, name)
        target = self._fopen(path, 'wb+')        
        for chunk in uploaded_file.chunks():
            target.write(chunk)
        target.close()
        os.chmod(path, self._options['fileMode'])
        
        return path
    
    def _get_contents(self, path):
        """
        Get file contents
        """
        return open(path).read()

    def _put_contents(self, path, content):
        """
        Write a string to a file.
        """
        f = open(path, 'w')
        f.write(content)
        f.close()

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
            for p in self._scandir(path):
                if os.path.islink(p) or not self._name_accepted(self._basename(p)):
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
        
        #TODO: Take mime filters into consideration
        
        basename = self._basename(path)
        dirname = self._dirname(path)

        if self._quarantine:
            dir_name = u'%s%s' % (str(time.time()).replace(' ', '_'), basename)
            dir_ = self._join_path(self._quarantine, dir_name)
            archive = self._join_path(dir_, basename)
            
            self._mkdir(dir_)
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
            if self._options['maxArchiveSize'] > 0 and self._options['maxArchiveSize'] < self._archiveSize:
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

                test = self._join_path(dirname, name)
                if os.path.exists(test) or os.path.islink(test):
                    name = self._unique_name(dirname, name, '-', False)
                
                result  = self._join_path(dirname, name)
                archive = self._join_path(result, basename)

                self._mkdir(result)
                self._copy(path, result, basename)
                
                self._unpack(archive, arc)
                self._unlink(archive)

            if not os.path.exists(result):
                raise Exception('Could not extract archive')
            
            return result