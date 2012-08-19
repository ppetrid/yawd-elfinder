from os.path import join
from django.conf import settings
from elfinder.utils.accesscontrol import elFinderTestACL
from elfinder.volumes.filesystem import ElfinderVolumeLocalFileSystem

ELFINDER_JS_URLS = {
    'a_jquery' : '//ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js',
    'b_jqueryui' : '//ajax.googleapis.com/ajax/libs/jqueryui/1.8.22/jquery-ui.min.js',
    'c_elfinder' : '%selfinder/js/elfinder.full.js' % settings.STATIC_URL
}
#allow to override any key in the project settings file   
ELFINDER_JS_URLS.update(getattr(settings, 'ELFINDER_JS_URLS', {}))

ELFINDER_CSS_URLS = {
    'a_jqueryui' : '//ajax.googleapis.com/ajax/libs/jqueryui/1.8.22/themes/smoothness/jquery-ui.css',
    'b_elfinder' : '%selfinder/css/elfinder.min.css' % settings.STATIC_URL
}
#allow to override any key in the project settings file   
ELFINDER_CSS_URLS.update(getattr(settings, 'ELFINDER_CSS_URLS', {}))

ELFINDER_WIDGET_JS_URL = '%sjs/jquery.elfinder-widget.full.js' % settings.STATIC_URL
ELFINDER_WIDGET_CSS_URL = '%scss/jquery.elfinder-widget.full.css' % settings.STATIC_URL

ELFINDER_CONNECTOR_OPTION_SETS = {
    #the default keywords demonstrates all possible configuration options
    #it allowes all file types, except from hidden files
    'default' : {
        'debug' : True,
        'roots' : [ 
            #{
            #    'driver' : ElfinderVolumeLocalFileSystem,
            #    'path'  : join(settings.MEDIA_ROOT, 'files'),
            #},
            {
                'id' : 'lff',
                'driver' : ElfinderVolumeLocalFileSystem,
                'path' : join(settings.MEDIA_ROOT, 'files'),
                'alias' : 'Elfinder files',
                #open this path on initial request instead of root path
                #'startPath' : '',
                'URL' : '%sfiles/' % settings.MEDIA_URL,
                #how many subdirs levels return per request
                #'treeDeep' : 1,
                #directory separator. required by client to show paths correctly
                #'separator' : os.sep,
                #directory for thumbnails
                #'tmbPath' : '.tmb',
                #mode to create thumbnails dir
                #'tmbPathMode' : 0777,
                #thumbnails dir URL. Set it if store thumbnails outside root directory
                #'tmbURL' : '',
                #thumbnails size (px)
                #'tmbSize' : 48,
                #thumbnails crop (True - crop, False - scale image to fit thumbnail size)
                #'tmbCrop' : True,
                #thumbnails background color (hex #rrggbb or 'transparent')
                #'tmbBgColor' : '#ffffff',
                #on paste file -  if True - old file will be replaced with new one, if False new file get name - original_name-number.ext
                #'copyOverwrite' : True,
                #if True - join new and old directories content on paste
                #'copyJoin' : True,
                #filter mime types to show
                #'onlyMimes' : [],
                #on upload -  if True - old file will be replaced with new one, if False new file get name - original_name-number.ext
                'uploadOverwrite' : True,
                #mimetypes allowed to upload
                'uploadAllow' : ['all',],
                #mimetypes not allowed to upload
                'uploadDeny' : ['all',],
                #order to proccess uploadAllow and uploadDeny options
                'uploadOrder' : ['deny', 'allow'],
                #maximum upload file size. NOTE - this is size for every uploaded files
                'uploadMaxSize' : '128m',
                #if True - every folder will be check for children folders, otherwise all folders will be marked as having subfolders
                #'checkSubfolders' : True,
                #allow to copy from this volume to other ones?
                #'copyFrom' : True,
                #allow to copy from other volumes to this one?
                #'copyTo' : True,
                #list of commands disabled on this root
                #'disabled' : [],
                #regexp or function name to validate new file name
                #enable this to allow creating hidden files
                #'acceptedName' : r'.*',
                #function/class method to control files permissions
                #the elFinderTestACL hides all files starting with .
                'accessControl' : [elFinderTestACL(), 'fsAccess'],
                #some data required by access control
                #'accessControlData' : None,
                #default permissions. not set hidden/locked here - take no effect
                #'defaults' : {
                #    'read' : True,
                #    'write' : True
                #},
                'attributes' : [
                    {
                        'pattern' : r'\.tmb$',
                        'read' : True,
                        'write': True,
                        'hidden' : True,
                        'locked' : True
                    },
                    #{   
                    #    'pattern' : r'\/my-inaccessible-folder$',
                    #    'write' : False,
                    #    'read' : False,
                    #    'hidden' : True,
                    #    'locked' : True
                    #},
                ],
                #Allowed archive's mimetypes to create. Leave empty for all available types.
                #'archiveMimes' : [],
                #Manual config for archivers. Leave empty for auto detect
                'archivers' : {
                    #create archivers must be a dictionary containing a class implementing the open, add, close methods and the archiver's file extension
                    #they should operate like the python's built-in tarfile.TarFile classes
                    #http://docs.python.org/library/zipfile.html
                    #'create' : { 'ext' : 'rar', 'archiver' : MyRarArchiver },
                    #extract archiver class must implement the open, extractall and close methods
                    #they should operate like python's built-in tarfile.TarFile classes
                    #for more information see http://docs.python.org/library/tarfile.html
                    #'extract' : { 'ext' : 'rar', 'archiver' : MyRarExtractor },
                }
            }
        ]
    },
    #option set to only allow image files
    'image' : {
        'roots' : [
            {
                'id' : 'lffim',
                'driver' : ElfinderVolumeLocalFileSystem,
                'path' : join(settings.MEDIA_ROOT, 'images'),
                'alias' : 'Elfinder images',
                'URL' : '%simages/' % settings.MEDIA_URL,
                'onlyMimes' : ['image',],
                'uploadAllow' : ['image',],
                'uploadDeny' : ['all',],
                'uploadMaxSize' : '128m',
                'disabled' : ['mkfile', 'archive'],
                'accessControl' : [elFinderTestACL(), 'fsAccess'],
                'attributes' : [
                    {
                        'pattern' : r'\.tmb$',
                        'read' : True,
                        'write': True,
                        'hidden' : True,
                        'locked' : True
                    },
                ],
            }
        ]  
    }
}

ELFINDER_CONNECTOR_OPTION_SETS.update(getattr(settings, 'ELFINDER_CONNECTOR_OPTS', {}))