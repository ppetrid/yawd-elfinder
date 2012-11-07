******************
Volume drivers API
******************

yawd-elfinder implemets two volume drivers:

* :class:`elfinder.volumes.storage.ElfinderVolumeStorage` and
* :class:`elfinder.volumes.filesystem.ElfinderVolumeLocalFileSystem`

The first must be used along with `Django storages <https://docs.djangoproject.com/en/dev/topics/files/#storage-objects>`_
and the latter is designed for native access to the local filesystem.
Both drivers implement the
:class:`elfinder.volumes.base.ElfinderVolumeDriver` API.

Base driver
+++++++++++

.. automodule:: elfinder.volumes.base
	:members:
	:private-members:

ElfinderVolumeStorage
+++++++++++++++++++++
	
.. automodule:: elfinder.volumes.storage
	:members:
	:private-members:
	
ElfinderVolumeLocalFileSystem
+++++++++++++++++++++++++++++
	
.. automodule:: elfinder.volumes.filesystem
	:members:
	:private-members: