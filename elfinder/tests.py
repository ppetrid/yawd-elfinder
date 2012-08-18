import os
from django.test.utils import override_settings
from django.test import TestCase
from django.conf import settings
from yawdcms.elfinder.elfinder import elFinder

@override_settings(MEDIA_ROOT=os.path.normpath(os.path.join(os.path.dirname(__file__),'..','test-media')))
class LocalFilesystem(TestCase):
    """
    Test LocalFileSystemVolumeDriver. 
    """
    def setUp(self):
        self._opts = {
            'locale' : 'en_US.UTF-8',
            'roots' : [{
                'id' : 'fsmr',
                'driver' : 'LocalFileSystem',
                'path' : settings.MEDIA_ROOT,
                'URL' : settings.MEDIA_URL,
            }]
        }
        self._elfinder = elFinder(self._opts)
    
    #def test_command_supported(self):
        #elfinder = elFinder({})
        #self.assertTrue(elfinder.commandExists('open'))
    
    def test_command_disabled(self):
        pass
    
    def test_open_options(self):
        #test 'debug' option actually returns debug info 
        self._opts['debug'] = True
        elfinder = elFinder(self._opts)
        output = elfinder.execute('open', init=True)
        self.assertTrue(output['debug']['connector'] == 'yawd-python') #check connector is valid
        self.assertTrue(len(output['debug']['volumes']) == 1) #check configuration reads volumes as expected
        self.assertTrue(output['debug']['volumes'][0]['id'] ==  'lfsmr_') #check debug contains the right volume info
        
        #test invalid root configuration
        self._opts['roots'][0]['path'] = '/some-non-existing-path'
        elfinder = elFinder(self._opts)
        output = elfinder.execute('open', init=True)
        self.assertTrue('errConf' in output['error'])
        self.assertTrue('errNoVolumes' in output['error'])
        
        #test mime filtering

    def test_open_media_root(self):
        
        #test error case with no init and no target
        output = self._elfinder.execute('open')
        self.assertTrue('error' in output)

        #init
        output = self._elfinder.execute('open', init=True)
        self.assertFalse('error' in output)
        self.assertTrue('files' in output)
        self.assertTrue('cwd' in output and output['cwd']) #check cwd exists and is not empty
        self.assertFalse('debug' in output)
        self.assertTrue(len(self._elfinder._volumes) == 1) #only one volume exists
        self.assertTrue('lfsmr_' in self._elfinder._volumes) #automatically generated volume id

        #check output['files'] contains the 'test' subfolder
        found_readable_tests = False
        for file_ in output['files']:
            if file_['name'] == 'tests':
                found_readable_tests = file_['read'] == 1
                break
        self.assertTrue(found_readable_tests == True)
        
    def test_parents_command(self):
        output = self._elfinder.execute('parents', target=self._elfinder._volumes.itervalues().next().encode('tests'))
        self.assertFalse('error' in output)
        self.assertTrue(len(output['tree']) == 1)
        self.assertTrue(output['tree'][0]['name'] == 'media')
        self.assertTrue(output['tree'][0]['read'] == 1)
        
    def test_mkdir_rmdir_command(self):
        output = self._elfinder.execute('mkdir', target=self._elfinder._volumes.itervalues().next().encode('tests'), name='yawdtests')
        self.assertFalse('error' in output)
        self.assertTrue(output['added'][0]['name'] == 'yawdtests')

        output = self._elfinder.execute('rm', targets=[self._elfinder._volumes.itervalues().next().encode(os.path.join(settings.MEDIA_ROOT, 'yawdtests'))])
        self.assertFalse('error' in output)
        self.assertTrue('lfsmr_eWF3ZHRlc3Rz' in output['removed'])