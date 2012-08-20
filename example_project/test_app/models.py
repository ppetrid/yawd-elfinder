from django.db import models
from elfinder.fields import ElfinderField 

class YawdElfinderTestModel(models.Model):
    name = models.CharField(max_length=100)
    content = models.TextField()
    anyfile = ElfinderField()
    image = ElfinderField(optionset='image')
    
    def __unicode__(self):
        return self.name