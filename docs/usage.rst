*******************
Quick-start guide: Using yawd-elfinder
*******************

Before reading this quick-start guide make sure yawd-elfinder is 
:ref:`installed <install>` and :ref:`configured <config>`.

The ElfinderFile model field
============================

You should start by defining model fields that refer to files 
managed by elfinder. For example, to define an image field for a simple
article model:

.. code-block:: python

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
how to do this, view the :ref:`example-dropbox` below and visit the
:ref:`setting-ELFINDER_CONNECTOR_OPTION_SETS` setting documentation.

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
``SimpleArticle`` model instance, use the 
:class:`elfinder.fields.ElfinderFile` ``url`` property to retrieve the 
image url:

.. code-block:: django
   
   <img src="{{object.image.url}}" alt="{{object.name}}" />

Further reading
===============

You can read some additional  yawd-elfinder articles on the 
`yawd blog <http://blog.yawd.eu/tag/yawd-elfinder/>`_:

* `Managing files with django - a yawd-elfinder tutorial <http://blog.yawd.eu/2012/managing-files-with-django-yawd-elfinder-tutorial/>`_

