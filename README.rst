yawd-elfinder, a file management solution for Django
====================================================

`elFinder`_ is a jQuery file manager providing standard features -such as 
uploading, moving, renaming files etc-, as well as a set of advanced features
such as image resizing/cropping/rotation and archive file creation.

**yawd-elfinder** provides a fully-featured python/django implementation for the 
elfinder connector v.2. A custom Model Field (tied to a nice form widget) 
is also provided. Therefore, you can easily manage your files 
through the Django admin interface, assign them to model fields and access
the file URLs in your Django templates.

The implementation follows the original PHP connector logic; you have full 
control over the allowed mime types, hidding/locking specific folders etc. 
In future release we plan to implement an FTP volume driver.

.. _elfinder: http://elfinder.org

Screenshots
===========

The admin widget

.. image:: http://static.yawd.eu/www/yawd-elfinder-widget.jpg

Elfinder in action

.. image:: http://static.yawd.eu/www/yawd-elfinder-rotate.jpg

Usage and demo
==============

See the yawd-elfinder documentation for information on 
how to install the demo and use yawd-elfinder. 