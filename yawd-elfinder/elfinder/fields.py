from django.db import models
from django.forms import CharField
from connector import ElfinderConnector

class ElfinderFile(object):
    """
    This object represents an Elfinder file.
    """
    
    def __init__(self, hash_, optionset):
        self.hash = hash_
        self.optionset = optionset
        self._info = None
    
    def _get_info(self):
        if self._info is None:
            
            if not self.hash:
                self._info = {}
            else:
                try:
                    from conf import settings as ls

                    connector = ElfinderConnector(ls.ELFINDER_CONNECTOR_OPTION_SETS[self.optionset])
                    info = connector.execute('info', targets = [self.hash], options=True)['files'][0]
                        
                    #get image dimensions
                    if 'mime' in info and info['mime'].startswith('image'):
                        info['dim'] = connector.execute('dim', target=self.hash)['dim']
                        
                    #calculate thumbnail url
                    if 'tmb' in info and 'tmbUrl' in info:
                        info['tmb'] = '%s%s' % (info['tmbUrl'], info['tmb'])
                        del info['tmbUrl']
                            
                    #`url` key is the equivelant `rootUrl` of the elfinderwidget
                    if 'url' in info: 
                        info['rootUrl'] = info['url']
                        del info['url']
    
                    self._info = info
                except:
                    from django.utils.translation import ugettext as _
                    self._info = { 'error' : _('This file is no longer valid') }  

        return self._info
        
    @property
    def url(self):
        info = self._get_info()
        return '%s%s' % (info['rootUrl'], '/'.join(info['path'].split(info['separator'])[1:]))
    
    @property
    def info(self):
        return self._get_info()
            
    def __unicode__(self):
        return self.hash

class ElfinderFormField(CharField):
    """
    This class specifies the default widget for the elfinder form field
    """
    
    def __init__(self, optionset, *args, **kwargs):
        from widgets import ElfinderWidget
        super(ElfinderFormField, self).__init__(*args, **kwargs)
        #self.validators.append(FilePathOrURLValidator(verify_exists=True))
        self.widget = ElfinderWidget(optionset)

class ElfinderField(models.Field):
    """
    This model field is used to hold the path of a file uploaded to the server or a full URL pointing to a file
    """
    
    description = "An elfinder file model field."
    __metaclass__ = models.SubfieldBase

    def __init__(self, optionset='default', *args, **kwargs):
        self.optionset = optionset

        if not 'max_length' in kwargs:
            kwargs['max_length'] = 100 #default field length

        super(ElfinderField, self).__init__(*args, **kwargs)
        
    def get_internal_type(self):
        return "CharField"
        
    def to_python(self, value):
        if isinstance(value, ElfinderFile):
            return value
        return ElfinderFile(hash_=value, optionset=self.optionset)
    
    def get_prep_value(self, value):
        if isinstance(value, ElfinderFile):
            return value.hash
        return value
    
    def get_prep_lookup(self, lookup_type, value):
        # We only handle 'exact' and 'in'. All others are errors.
        if lookup_type in ['year', 'month', 'day']:
            raise TypeError('Lookup type %r not supported.' % lookup_type)
        
        return super(ElfinderField, self).get_prep_lookup(lookup_type, value)
        
    def formfield(self, **kwargs):
        defaults = {
                'form_class': ElfinderFormField,
                'optionset' : self.optionset
        }
        defaults.update(kwargs)
        return super(ElfinderField, self).formfield(**defaults)