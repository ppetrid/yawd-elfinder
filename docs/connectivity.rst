Connectivity
============

yawd-elfinder can manage local files but also use 
`Django filesystem storages <https://docs.djangoproject.com/en/dev/ref/files/storage/>`_
to connect to remote filesystems.

Volume drivers
++++++++++++++

Volume drivers are python classes that yawd-elfinder uses to connect
to various file systems. yawd-elfinder right now implements two 
distinct volume drivers.

The first one is :class:`elfinder.volumes.filesystem.ElfinderVolumeLocalFileSystem`.
This driver handles files stored in the local file system. Both the ``default``
and ``image`` *optionsets* that are pre-configured in yawd-elfinder use
this driver to communicate with the file system.

The second driver is :class:`elfinder.volumes.storage.ElfinderVolumeStorage`.
This driver is able to connect to any filesystem using
`Django filesystem storages <https://docs.djangoproject.com/en/dev/ref/files/storage/>`_.
Please note that django storages are not originally designed for managing
the full filesystem, but for managing files. Therefore some operations
like removing directories may be disabled when using this driver. 
Especially for removing directories yawd-elfinder allows you to define an 
``rmDir`` callback that will be used to provide the functionality based
on your storage of choice.

.. note::

	You can manage local files using both the :class:`elfinder.volumes.filesystem.ElfinderVolumeLocalFileSystem`.
	and :class:`elfinder.volumes.storage.ElfinderVolumeStorage`
	drivers. However the first one is recommended, since it is implemented
	with the elfinder functionality in mind.

.. _example-dropbox:

Simple dropbox example
++++++++++++++++++++++

Let's suppose you want to connect yawd-elfinder with your dropbox files. 
With `django-dropbox <https://github.com/andres-torres-marroquin/django-dropbox>`_
installed and configured you could define the following at the bottom of 
your project's main settings file:

.. code-block:: python

	from elfinder.volumes.storage import ElfinderVolumeStorage
	
	ELFINDER_CONNECTOR_OPTION_SETS = {
	    'dropbox' : {
	        'debug': True,
	        'roots': [{
	            'id' : 'd',
	            'driver' : ElfinderVolumeStorage,
	            'storageClass' : 'django_dropbox.storage.DropboxStorage',
	            'keepAlive' : True,
	            'cache' : 3600
	        }]
	    }
	}

Then you could use the ``dropbox`` *optionset* in your models as follows:

.. code-block:: python

	from elfinder.fields import ElfinderField

	class MyModel(models.Model)
		...
		file_ = ElfinderField(optionset='dropbox')

Please take a look the :class:`elfinder.volumes.storage.ElfinderVolumeStorage`
API for more information on this drivers' usage and limitations.  

.. _custom-drivers:

Custom volume drivers
++++++++++++++++++++++

To expand the yawd-elfinder connectivity you can implement your own driver.
It should simply extend :class:`elfinder.volumes.base.ElfinderVolumeDriver`
and implement all methods raising a ``NotImplementedError`` exception.
To use your custom driver you must define a custom option set through the 
:ref:`setting-ELFINDER_CONNECTOR_OPTION_SETS` setting, just like we did in
the example above.