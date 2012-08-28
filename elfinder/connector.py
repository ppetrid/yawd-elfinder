import os, re, time, urllib
from django.utils.translation import ugettext as _
from exceptions import ElfinderErrorMessages, VolumeNotFoundError, DirNotFoundError, FileNotFoundError, NamedError, NotAnImageError

class ElfinderConnector:
    """
    A python implementation of the 
    `elfinder connector api v2.0  <https://github.com/Studio-42/elFinder/wiki/Client-Server-API-2.0>`_. At the moment, it supports all elfinder commands except from ``netDrivers``.
    """

    _version = '2.0'
    _commit = 'b0144a0'
    _netDrivers = {}
    _commands = {
        'open' : { 'target' : False, 'tree' : False, 'init' : False, 'mimes' : False },
        'ls' : { 'target' : True, 'mimes' : False },
        'tree' : { 'target' : True },
        'parents' : { 'target' : True },
        'tmb' : { 'targets' : True },
        'file' : { 'target' : True, 'download' : False, 'request' : False },
        'size' : { 'targets' : True },
        'mkdir' : { 'target' : True, 'name' : True },
        'mkfile' : { 'target' : True, 'name' : True, 'mimes' : False },
        'rm' : { 'targets' : True },
        'rename' : { 'target' : True, 'name' : True, 'mimes' : False },
        'duplicate' : { 'targets' : True },
        'paste' : { 'dst' : True, 'targets' : True, 'cut' : False, 'mimes' : False },
        'upload' : { 'target' : True, 'FILES' : True, 'mimes' : False, 'html' : False },
        'get' : { 'target' : True },
        'put' : { 'target' : True, 'content' : '', 'mimes' : False },
        'archive' : { 'targets' : True, 'type_' : True, 'mimes' : False },
        'extract' : { 'target' : True, 'mimes' : False },
        'search' : { 'q' : True, 'mimes' : False },
        'info' : { 'targets' : True, 'options': False },
        'dim' : { 'target' : True },
        'resize' : {'target' : True, 'width' : True, 'height' : True, 'mode' : False, 'x' : False, 'y' : False, 'degree' : False },
        #TODO: implement netmount
        'netmount'  : { 'protocol' : True, 'host' : True, 'path' : False, 'port' : False, 'user' : True, 'pass' : True, 'alias' : False, 'options' : False}
    }

    def __init__(self, opts, session = None):
        self._volumes = {}
        self._default = None
        self._loaded = False
        self._session = session
        self._time =  time.time()
        self._debug = 'debug' in opts and opts['debug'] 
        self._uploadDebug = ''
        self._mountErrors = []
        
        #TODO: Use signals instead of the original connector's binding mechanism
        if not 'roots' in opts:
            opts['roots'] = []
        
        #for root in self.getNetVolumes():
        #    opts['roots'].append(root)

        for o in opts['roots']:
            class_ = o['driver'] if 'driver' in o else ''  
                      
            try:
                volume = class_()
            except TypeError:
                self._mountErrors.append('Driver "%s" does not exist' % class_)
            except:
                #TODO: should we fail silently?
                raise

            try:
                volume.mount(o)
            except Exception as e:
                self._mountErrors.append('Driver "%s" " %s' % (class_, e))
                break
            
            id_ = volume.id()
            self._volumes[id_] = volume
            if not self._default and volume.isReadable():
                self._default = self._volumes[id_]

        self._loaded = (self._default is not None)
    
    def loaded(self):
        """
        Check if the volume driver is loaded
        """
        return self._loaded

    def version(self, commit=False):
        """
        Get api version. The commit number refers to the corresponding official elfinder github commit number.
        """
        return '%s - %s' % (self._version, self._commit) if commit else self._version
    
    def commandExists(self, cmd):
        """
        Check if command exists
        """
        return cmd in self._commands and hasattr(self, cmd) and callable(getattr(self, cmd))
    
    def commandArgsList(self, cmd):
        """
        Return command required arguments info
        """
        return self._commands[cmd] if self.commandExists(cmd) else {}
    
    def realpath(self, hash_):
        """
        Return file real path.
        Raises a VolumeNotFoundError exception if volume was not found.
        """
        return self._volume(hash_).realpath(hash_)
    
    #def getNetVolumes(self):
    #    """
    #    Return  network volumes config.
    #    """
    #    return self._session.get('elFinderNetVolumes', []) if  self._session else []
        
    #def setNetVolumes(self, volumes):
    #    """
    #    Save network volumes config.
    #    """
    #    self._session['elFinderNetVolumes'] = volumes

    def error(self, *args):
        """
        Normalize error messages
        """
        errors = []
        for msg in args:
            if not isinstance(msg, basestring):
                errors += msg
            else:
                errors.append(msg)
        
        if not errors:
            return [ElfinderErrorMessages.ERROR_UNKNOWN,]
        return errors
    
    def execute(self, cmd, **kwargs):
        """
        Exec command and return result
        """        
        if not self._loaded:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_CONF, ElfinderErrorMessages.ERROR_CONF_NO_VOL)}

        if 'mimes' in kwargs:
            for id_ in self._volumes:
                self._volumes[id_].setMimesFilter(kwargs['mimes'])
        
        if not self.commandExists(cmd):
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_UNKNOWN_CMD, cmd)}
        
        for arg, req in self.commandArgsList(cmd).items():
            if req and not kwargs[arg]:
                return {'error' : self.error(ElfinderErrorMessages.ERROR_INV_PARAMS, cmd)}
        
        result = getattr(self, cmd)(**kwargs)
        
        if 'removed' in result:
            for id_ in self._volumes:
                result['removed'] += self._volumes[id_].removed()
                self._volumes[id_].resetRemoved()
        
        #call handlers for this command
        #TODO: a signal must be sent here
        
        #replace removed files info with removed files hashes
        if 'removed' in result:
            removed = []
            for file_ in result['removed']:
                if not file_['hash'] in removed:
                    removed.append(file_['hash'])
            result['removed'] = removed

        #remove hidden files and filter files by mimetypes
        if 'added' in result:
            result['added'] = self._filter(result['added'])
        
        #remove hidden files and filter files by mimetypes
        if 'changed' in result:
            result['changed'] = self._filter(result['changed'])
        
        if self._debug or ('debug' in kwargs and kwargs['debug']):
            result['debug'] = {
                'connector' : 'yawd-python',
                'time' : time.time() - self._time,
                'upload' : self._uploadDebug,
                'volumes' : [],
                'mountErrors' : self._mountErrors
            }
            
            for id_,volume in self._volumes.items():
                result['debug']['volumes'].append(volume.debug())
            
        return result

    def open(self, target='', init=False, tree=False, debug=False):
        """
        **Command**: Open a directory
        
        Return:
            An array with following elements:
                :cwd:          opened directory information
                :files:        opened directory content [and dirs tree if kwargs['tree'] is ``True``]
                :api:          api version (if kwargs['init'] is ``True``)
                :uplMaxSize:   The maximum allowed upload size (if kwargs['init'] is ``True``)
                :error:        on failed
        """
        hash_ = 'default folder' if init else '#%s' % target

        if not init and not target:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_INV_PARAMS, 'open')}

        #detect volume
        try:
            volume = self._volume(target)
        except VolumeNotFoundError as e:
            if not init:
                return {'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, hash_, e)}
            else:
                #on init request we can get invalid dir hash -
                #dir which can not be opened now, but remembered by client,
                #so open default volume
                volume = self._default
        
        try:
            cwd = volume.dir(hash_=target, resolveLink=True)
            if not cwd['read'] and init:
                try:
                    cwd = volume.dir(hash_=volume.defaultPath(), resolveLink=True)
                except (DirNotFoundError, FileNotFoundError) as e:
                    return {'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, hash_, e)}
        except (DirNotFoundError, FileNotFoundError) as e:
            if init:
                cwd = volume.dir(hash_=volume.defaultPath(), resolveLink=True)
            else:
                return {'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, hash_, e)}

        if not cwd['read']:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, hash_, ElfinderErrorMessages.ERROR_PERM_DENIED)}

        files = []
        #get folder trees
        if tree:
            for id_ in self._volumes:
                files += self._volumes[id_].tree(exclude=target)
        
        #get current working directory files list and add to files if not exists in it
        try:
            ls = volume.scandir(cwd['hash'])
        except Exception as e:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, cwd['name'], e)}
        
        for file_ in ls:
            if not file_ in files:
                files.append(file_)

        result = {
            'cwd' : cwd,
            'options' : volume.options(target),
            'files' : files
        }

        if init:
            result['api'] = self._version
            result['netDrivers'] = self._netDrivers.keys()
            #TODO: Do we need Upload Max Size?
        
        return result

    def ls(self, target, mimes=[], debug=False):
        """
        **Command**: Return a directory's file list
        """
        try:
            return { 'list' : self._volume(target).ls(target) }
        except:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, '#%s' % target) }

    def tree(self, target, debug=False):
        """
        **Command**: Return subdirs for required directory
        """
        try:
            return { 'tree' : self._volume(target).tree(target) }
        except:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, '#%s' % target) }
    
    def parents(self, target, debug=False):
        """
        **Command**: Return parents dir for required directory
        """
        try:
            return {'tree' : self._volume(target).parents(target) }
        except:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, u'#%s' % target) }

    def tmb(self, targets, debug=False):
        """
        **Command**: Return new automatically-created thumbnails list
        """
        result  = { 'images' : {} }
        for target in targets:
            try:
                thumb = self._volume(target).tmb(target)
                if thumb:
                    result['images'][target] = thumb  
            except VolumeNotFoundError:
                continue

        return result
    
    def file(self, target, request=None, download=False, debug=False):
        """
        **Command**: Get a file
        
        Required to output file in browser when volume URL is not set.
        Used to download the file as well.
        
        Return:
            An array containing an opened file pointer, the root itself and the required response headers
        """
        try:
            volume = self._volume(target)
            file_ = volume.file(target)
        except (VolumeNotFoundError, FileNotFoundError): 
            return { 'error' : _('File not found'), 'header' : { 'Status' : 404 }, 'raw' : True }
        
        if not file_['read']:
            return { 'error' : _('Access denied'), 'header' : { 'Status' : 403 }, 'raw' : True }
        
        try:
            fp = volume.open(target)
        except os.error: #Normally this could raise a FileNotFoundError as well, but we already checked this
            return { 'error' : _('File not found'), 'header' : { 'Status' : 404 }, 'raw' : True }

        if download:
            disp = 'attachment'
            mime = 'application/octet-stream'
        else:
            disp  = 'inline' if re.match('(image|text)', file_['mime'], re.IGNORECASE) or file_['mime'] == 'application/x-shockwave-flash' else 'attachment'  
            mime = file_['mime']

        filenameEncoded = urllib.quote(file_['name'])
        if not '%' in filenameEncoded: #ASCII only
            filename = 'filename="%s"' % file_['name']
        elif request and hasattr(request, 'META') and 'HTTP_USER_AGENT' in request.META:
            ua = request.META['HTTP_USER_AGENT']
            if re.search('MSIE [4-8]', ua): #IE < 9 do not support RFC 6266 (RFC 2231/RFC 5987)
                filename = 'filename="%s"' % filenameEncoded
            elif not 'Chrome'in ua and 'Safari' in ua: # Safari
                filename = 'filename="%s"' % file_['name'].replace('"','')
            else: #RFC 6266 (RFC 2231/RFC 5987)
                filename = "filename*=UTF-8''%s" % filenameEncoded
        else:
            filename = ''

        result = {
            'volume' : volume,
            'pointer' : fp,
            'info' : file_,
            'header' : {
                'Content-Type' : mime, 
                'Content-Disposition' : '%s; %s' % (disp, filename),
                'Content-Location' : file_['name'],
                'Content-Transfer-Encoding' : 'binary',
                'Content-Length' : file_['size'],
                #'Connection' : 'close'
            }
        }

        return result

    def size(self, targets, debug=False):
        """
        **Command**: Count total file size of all directories in ``targets`` param.
        """
        size = 0
        
        for target in targets:
            try:
                volume = self._volume(target)
                file_ = volume.file(target)
            except (VolumeNotFoundError, FileNotFoundError):
                file_ = { 'read' : 0 }
                
            if not file_['read']:
                return { 'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, u'#%s' % target) }
            
            size += volume.size(target)

        return { 'size' : size }

    def mkdir(self, target, name, debug=False):
        """
        **Command**: Create a new directory
        """
        try:
            volume = self._volume(target)
        except VolumeNotFoundError:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_MKDIR, name, ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND, '#%s' % target)}

        try:
            return { 'added' : [volume.mkdir(target, name)] }
        except NamedError as e:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_MKDIR, name, e, e.name) }
        except Exception as e:
            return { 'error': self.error(ElfinderErrorMessages.ERROR_MKDIR, name, e) }

    def mkfile(self, target, name, mimes=[], debug=False):
        """
        **Command**: Create a new, empty file.
        """
        try:
            volume = self._volume(target)
        except VolumeNotFoundError:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_MKFILE, name, ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND, '#%s' % target)}

        try:
            return { 'added' : [volume.mkfile(target, name)] }
        except NamedError as e:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_MKFILE, name, e, e.name) }
        except Exception as e:
            return { 'error': self.error(ElfinderErrorMessages.ERROR_MKFILE, name, e) }

    def rename(self, target, name, mimes=[], debug=False):
        """
        **Command**: Rename a file.
        """
        try:
            volume = self._volume(target)
            rm = volume.file(target)
        except (VolumeNotFoundError, FileNotFoundError):
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_RENAME, '#%s' % target, ElfinderErrorMessages.ERROR_FILE_NOT_FOUND) }

        rm['realpath'] = volume.realpath(target)
        try:
            return { 'added' : [volume.rename(target, name)], 'removed' : [rm] }
        except NamedError as e:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_RENAME, rm['name'], e, e.name) }
        except Exception as e: 
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_RENAME, rm['name'], e) }

    def duplicate(self, targets, suffix='copy', debug=False):
        """
        **Command**: Duplicate a file. Create a copy with "{suffix} %d" suffix,
        where "%d" is an integer and ``suffix`` an argument that defaults to `'copy`'.. 
        """
        result = { 'added' : [] }
        
        for target in targets:
            try:
                volume = self._volume(target)
                volume.file(target)
            except (VolumeNotFoundError, FileNotFoundError):
                result['warning'] = self.error(ElfinderErrorMessages.ERROR_COPY, u'#%s' % target, ElfinderErrorMessages.ERROR_FILE_NOT_FOUND)
                continue
            
            try:
                result['added'].append(volume.duplicate(target, suffix))
            except Exception as e:
                result['warning'] = self.error(e)
        
        return result
    
    def rm(self, targets, debug=False):
        """
        **Command**: Remove directories or files.
        """
        result  = {'removed' : []}

        for target in targets:
            try:
                volume = self._volume(target)
            except VolumeNotFoundError:
                result['warning'] = self.error(ElfinderErrorMessages.ERROR_RM, '#%s' % target, ElfinderErrorMessages.ERROR_FILE_NOT_FOUND)
                continue

            try:
                volume.rm(target)
            except NamedError as e:
                result['warning'] = self.error(e, e.name)
            except Exception as e:
                result['warning'] = self.error(e)

        return result
    
    def upload(self, target, FILES, html=False, mimes=[], debug=False):
        """
        **Command**: Save uploaded files.
        """
        header = { 'Content-Type' : 'text/html; charset=utf-8' } if html else {}
        result = { 'added' : [], 'header' : header }

        try:
            files = FILES.getlist('upload[]')
        except KeyError:
            files = []

        if not isinstance(files, list) or not files:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_UPLOAD, ElfinderErrorMessages.ERROR_UPLOAD_NO_FILES), 'header' : header }

        try:
            volume = self._volume(target)
        except VolumeNotFoundError:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_UPLOAD, ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND, '#%s' % target), 'header' : header }
        
        for uploaded_file in files:
            try:
                file_ = volume.upload(uploaded_file, target)
                result['added'].append(file_)
            except Exception, e:
                result['warning'] = self.error(ElfinderErrorMessages.ERROR_UPLOAD_FILE, uploaded_file.name, e)
                self._uploadDebug = 'Upload error: Django handler error'

        return result

    def paste(self, targets, dst, cut=False, mimes=[], debug=False):
        """
        **Command**: Copy/move ``targets`` files into a new destination ``dst``.
        """
        error = ElfinderErrorMessages.ERROR_MOVE if cut else ElfinderErrorMessages.ERROR_COPY
        result = { 'added' : [], 'removed' : [] }
        
        try:
            dstVolume = self._volume(dst)
        except VolumeNotFoundError:
            return { 'error' : self.error(error, u'#%s' % targets[0], ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND, u'#%s' % dst) }
        
        for target in targets:
            try:
                srcVolume = self._volume(target)
            except VolumeNotFoundError:
                result['warning'] = self.error(error, u'#%s' % target, ElfinderErrorMessages.ERROR_FILE_NOT_FOUND)
                continue
            
            try:
                result['added'].append(dstVolume.paste(srcVolume, target, dst, cut))
            except NamedError as e:
                result['warning'] = self.error(e, e.name)
            except Exception as e:
                result['warning'] = self.error(e)

        return result

    def get(self, target, debug=False):
        """
        **Command**: Return file contents
        """        
        try:
            volume = self._volume(target)
            volume.file(target)
        except (VolumeNotFoundError, FileNotFoundError):
            return {'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, u'#%s' % target, ElfinderErrorMessages.ERROR_FILE_NOT_FOUND)}
        
        try:
            content = volume.getContents(target)
        except Exception as e:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_OPEN, volume.path(target), e)}
        
        #the content will be returned as json, so try to json encode it
        #throw an error if it cannot be properly serialized
        try:
            from django.utils import simplejson as json
            json.dumps(content)
        except:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_NOT_UTF8_CONTENT, volume.path(target))}
        
        return {'content' : content }

    def put(self, target, content, mimes=[], debug=False):
        """
       **Command**:  Save ``content`` into a text file
        """
        try:
            volume = self._volume(target)
            volume.file(target)
        except (VolumeNotFoundError, FileNotFoundError):
            return {'error' : self.error(ElfinderErrorMessages.ERROR_SAVE, u'#%s' % target, ElfinderErrorMessages.ERROR_FILE_NOT_FOUND)}
        
        try:
            return {'changed' : [volume.putContents(target, content)]} 
        except Exception as e:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_SAVE, volume.path(target), e)}

    def extract(self, target, mimes=[], debug=False):
        """
        Extract files from archive
        """
        #TODO: Mimes are currently not being used
        try:
            volume = self._volume(target)
            volume.file(target)
        except (VolumeNotFoundError, FileNotFoundError):
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_EXTRACT, u'#%s' % target, ElfinderErrorMessages.ERROR_FILE_NOT_FOUND) }

        try:
            return {'added' : [volume.extract(target)] }
        except Exception as e:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_EXTRACT, volume.path(target), e)}

    def archive(self, targets, type_, mimes=[], debug=False):
        """
        **Command**: Create a new archive file containing all files in
        ``targets`` param.
        """
        #TODO: Mimes are currently not being used
        try:
            volume = self._volume(targets[0])
        except:
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_ARCHIVE, ElfinderErrorMessages.ERROR_TRGDIR_NOT_FOUND) }
    
        try:
            return {'added' : [volume.archive(targets, type_)]}
        except Exception as e:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_ARCHIVE, e)}

    def search(self, q, mimes=[], debug=False):
        """
        **Command**: Search files for ``q``.
        """
        q = q.strip()
        result = []
        for volume in self._volumes.values():
            result += volume.search(q, mimes)
        return {'files' : result}

    def info(self, targets, options=False, debug=False):
        """
        **Command**: Return file info (used by client "places" ui)
        """
        files = []
        for hash_ in targets:
            try:
                volume = self._volume(hash_)
                if options:
                    options = volume.options(hash_)
                    options.update(volume.file(hash_))
                    files.append(options)
                else:
                    files.append(volume.file(hash_))
            except:
                continue

        return {'files' : files}

    def dim(self, target, debug=False):
        """
        **Command**: Return image dimmensions
        """        
        try:
            return { 'dim' : self._volume(target).dimensions(target) }
        except (VolumeNotFoundError, FileNotFoundError, NotAnImageError):
            return {}

    def resize(self, target, width, height, mode=None, x='0', y='0', degree='0', debug=False):
        """
        **Command**: Resize ``target`` image
        """
        width, height, x, y, degree = int(width), int(height), int(x), int(y), int(degree)
        bg = ''

        try:
            volume = self._volume(target)
            volume.file(target)
        except (VolumeNotFoundError, FileNotFoundError):
            return { 'error' : self.error(ElfinderErrorMessages.ERROR_RESIZE, '#%s' % target, ElfinderErrorMessages.ERROR_FILE_NOT_FOUND) }
        
        try:
            return { 'changed' : [volume.resize(target, width, height, x, y, mode, bg, degree)]}
        except Exception as e:
            return {'error' : self.error(ElfinderErrorMessages.ERROR_RESIZE, volume.path(target), e)}

    def _volume(self, hash_):
        """
        Return root - file's owner
        """
        if hash_:
            for id_, v in self._volumes.items():
                if hash_.find(id_) == 0:
                    return v
        raise VolumeNotFoundError()

    def _filter(self, files):
        """
        Remove hidden files and files with required mime types from the provided file list
        """
        for file_ in files:
            if ('hidden' in file_ and file_['hidden']) or not self._default.mimeAccepted(file_['mime']):
                files.remove(file_)
        return files