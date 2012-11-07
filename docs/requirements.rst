************
Requirements
************

yawd-elfinder needs the following packages to be included in your ``PYTHONPATH``.
You don't have to manually install these packages; the setup script 
checks for dependencies.  

* **Django**: yawd-elfinder is developed & tested under Django 1.4.
   
* **PIL**: To generate image thumbnails and allow for on the fly image manipulation we use the PIL imaging library.
   
* **python-magic**: This is a pyton module used for mime-type detection.

* Cache: Although not required, you could use a django cache backend to improve the  yawd-elfinder performance. yawd-elfinder uses the caching framework to store file information and directory listings. For more information on how to configure a Django cache backend see the `official Django documentation <https://docs.djangoproject.com/en/1.4/topics/cache/#setting-up-the-cache>`_