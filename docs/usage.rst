*******************
Using yawd-elfinder
*******************

Before reading this guide, make sure yawd-elfinder is 
:ref:`installed <install>` and :ref:`configured <config>`.

The ElfinderFile model field
============================

You should start by defining model fields that refer to files 
managed by elfinder. For example, to define an image field for a simple
article model

.. code-block:: django

   from django.db import models
   from elfinder.fields import ElfinderField 

   class SimpleArticle(models.Model):
      name = models.CharField(max_length=100)
      content = models.TextField()
      image = ElfinderField(optionset='image')
    
      def __unicode__(self):
         return self.name
         
The :class:`elfinder.fields.ElfinderField` field associates the ``image``
member with an :class:`elfinder.fields.ElfinderFile` object. The ``optionset``
argument specifies a set of configuration options that define stuff like 
allowed file types, where to store uploaded files etc. yawd-elfinder by default
configures two optionsets: ``default`` and ``image``. When using

.. code-block:: python
   
   my_field = ElfinderField(optionset='default')

...yawd-elfinder will store uploaded files to a `'files'` directory under your 
``MEDIA_ROOT``, and allow all kinds of files to be uploaded and managed.

When using

.. code-block:: python

   my_field = ElfinderField(optionset='image')

...yawd-elfinder will store uploaded files to an `'images'` directory under your 
``MEDIA_ROOT``, and allow inly image files to be uploaded and managed.

Of course, you can define your own *optionsets*. For more information on 
how to do this, view the :ref:`setting-ELFINDER_CONNECTOR_OPTION_SETS` 
setting documentation.

:class:`elfinder.fields.ElfinderFile` can also accept a ``start_path`` argument
to indicate the default folder to open for this field. For example, to open
a folder named *'languages'* you could use the following code:

.. code-block:: python

   my_field = ElfinderField(optionset='image', start_path='languages')
   
yawd-elfinder expects that the path defined in ``star_path`` is *relative to
the volume root* (see the :ref:`setting-path` setting). In fact, 
``start_path`` sets the  :ref:`setting-startPath` setting to the
provided value.


Django templates
================

Based on the above ``SimpleArticle`` example, if ``object`` is a 
``SimpleArticle`` model instance, use the `url` 
:class:`elfinder.fields.ElfinderFile` property to retrieve the image url

.. code-block:: django
   
   <img src="{{:object.image.url}}" alt="{{object.name}}" />

Volume Drivers
==============

yawd-elfinder currently handles files stored in the local file system. In 
future releases a driver using the Django :class:`Storage` API 
will be implemented, allowing for connecting to remote filesystems 
(FTP etc). Another idea might be to implement a driver that stores files 
exclusively in the database 
(like `django-elfinder <https://github.com/mikery/django-elfinder>`_ does). 

Ofcourse you can always implement your own driver (that should extend 
:class:`elfinder.volumes.base.ElfinderVolumeDriver`) and use the 
:ref:`setting-ELFINDER_CONNECTOR_OPTION_SETS` setting to define a ``root`` 
that uses your driver.