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

The current version is 0.90.00, use the github version for the latest fixes.

:ref:`changelog`

.. _elfinder: http://elfinder.org

Usage and demo
==============

See the yawd-elfinder documentation for information on 
`how to install the demo <http://yawd-elfinder.readthedocs.org/en/latest/installation.html#example-project>`_
and `use yawd-elfinder <http://yawd-elfinder.readthedocs.org/en/latest/usage.html>`_.

Screenshots
===========

The admin widget

.. image:: http://static.yawd.eu/www/yawd-elfinder-widget.jpg

Elfinder in action

.. image:: http://static.yawd.eu/www/yawd-elfinder-rotate.jpg 