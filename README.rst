yawd-elfinder - Elfinder-based file management solution for Django
==================================================================

`elFinder`_ is a jQuery file manager providing standard features -such as 
uploading, moving, renaming files etc-, as well as a set of advanced features
such as image resizing/cropping/rotation and archive file creation.

yawd-elfinder provides a fully-featured python/django implementation for the 
elfinder connector v.2. A custom Model Field (tied to a nice form widget) 
is also provided. Therefore, you can manage your files through the Django admin 
interface and assign them to fields, all at once.

The implementation follows the original PHP connector logic, you have full 
control over the allowed mime types, hidding/locking specific folders etc. 
In future release we plan to implement an FTP volume driver.

.. _elfinder: http://elfinder.org

.. image: http://static.yawd.eu/www/yawd-elfinder-widget.jpg

.. image: http://static.yawd.eu/www/yawd-elfinder-rotate.jpg

Dependencies
============

yawd-elfinder is tested under Django 1.4. The PIL image library is also needed
for on-the-fly image manipulation. `python-magic`_ must also be installed - this
is used for mime type detection. Since yawd-elfinder deals with "expensive"
file operations (it reads a lot from  the disk!), the application uses 
django's caching framework to speed things up; therefore, using a django
cache backend is recommended but not required.

.. _python-magic: https://github.com/ahupp/python-magic/
