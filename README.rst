yawd-elfinder, a file management solution for Django
====================================================

`elFinder`_ is a jQuery web file manager providing standard features -such as 
uploading, moving, renaming files etc-, as well as a set of advanced features
such as image resizing/cropping/rotation and archive file creation.

**yawd-elfinder** provides a fully-featured python/django implementation for the 
elfinder connector v.2. A custom Model Field (tied to a nice form widget) 
is also provided. Therefore, you can easily manage your files 
through the Django admin interface, assign them to model fields and access
the file URLs in your Django templates.

**yawd-elfinder** can manage local files but also use Django filesystem storages to
connect to remote filesystems. A set of django options allows control over
file and directory permissions, accepted mime types, max file sizes etc. 

The current version is 0.90.03, use the github version for the latest fixes.

.. note::
	yawd-admin v0.90.03 is the last version intended to work with
	Django 1.4. The current master is actively developed under Django 1.5
	and does NOT work with older Django releases. For those still using
	Django 1.4, you can checkout the ``0.90.x`` branch or use the yawd-elfinder
	v0.90.03 pypi package. New features will not be backported to the ``0.90.x``
	branch. Since many of us run production systems tied to Django 1.4, both
	v0.90.03 and the latest documentation will be online on readthedocs.org. 

.. _elfinder: http://elfinder.org

Usage and demo
==============

See the `yawd-elfinder v0.90.03 documentation <http://yawd-elfinder.readthedocs.org/en/v0.90.03/>`_
for information on how to install the demo and use yawd-elfinder.

Screenshots
===========

The admin widget

.. image:: http://static.yawd.eu/www/yawd-elfinder-widget.jpg

Elfinder in action

.. image:: http://static.yawd.eu/www/yawd-elfinder-rotate.jpg 