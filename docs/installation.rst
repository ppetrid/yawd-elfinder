********************
Installation & Setup
********************

.. _install:

Installation
============

You can install yawd-elfinder either by using the python package index or 
the source code.

.. note::

	Since yawd-elfinder is being actively developed, for the time being you should
	better use the source code installation method to ensure that all latest bug fixes 
	and patches are included.  

Python package
++++++++++++++

This is the easiest, one-step installation process::

   pip install yawd-elfinder
    

From source
+++++++++++ 

Alternatively, you can install yawd-elfinder from the source code 
(visit the github page `here <https://github.com/yawd/yawd-elfinder>`_)::

   git clone https://github.com/yawd/yawd-elfinder
   cd yawd-elfinder
   python setup.py install

.. _config:

Setup
=====

.. highlight:: python

* Add ``elfinder`` to your ``settings.INSTALLED_APPS``.

* For elfinder to interact with the server-side connector you must add the yawd-elfinder ``urls`` module in your project's urls.

.. code-block:: django
   
   from django.conf.urls import patterns, include, url

   urlpatterns = patterns('',
      ...
      url(r'^elfinder/', include('elfinder.urls')),
      ...
   )

* **Optionally**, configure yawd-efinder :ref:`settings`

Example project
===============

Use the provided example project for a quick demo of yawd-elfinder. 
You can install it on an isolated environment using virtualenv. Firstly, 
install virtualenv::

   apt-get-install virtualenv
   
Create a new environment named *elfinder* and activate it::

   virtualenv /www/elfinder
   source /www/elfinder/bin/activate
   
Download and install yawd-elfinder::

   git clone https://github.com/yawd/yawd-elfinder
   cd yawd-elfinder
   python setup.py install
   
At this point, yawd-elfinder will be in your ``PYTHONPATH``. Now initialize 
the example project::
   
   cd example_project
   python manage.py syncdb
   
When promted, create an admin account. Finally, start the web server::

   python manage.py runserver
   
...and visit *http://localhost:8000/admin/test_app/yawdelfindertestmodel/1/*
to see the admin widget and interact with the elfinder connector. A quick 
index view example is available at *http://localhost:8000/*.
Once you are done, you can deactivate the virtual environment::

   deactivate elfinder