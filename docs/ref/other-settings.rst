.. _other-settings:

**************
Other settings
**************

Below is a list of project settings defined by yawd-elfinder. 

.. note::

   You can override all of them in your project's settings file.

.. _setting-ELFINDER_JS_URLS:

ELFINDER_JS_URLS
----------------

Default::

   {
      'a_jquery' : '//ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js',
      'b_jqueryui' : '//ajax.googleapis.com/ajax/libs/jqueryui/1.8.22/jquery-ui.min.js',
      'c_elfinder' : '%selfinder/js/elfinder.full.js' % settings.STATIC_URL
   }

A dictionary containing the location of javascript files needed by 
yawd-elfinder. 

.. hint::

   Say, for any example, that your project already containts a 
   copy of jquery or query. You could use these settings to avoid loading 
   the google-hosted versions and use your own copies.
   
.. _setting-ELFINDER_CSS_URLS:

ELFINDER_CSS_URLS
-----------------

Default::

   {
    'a_jqueryui' : '//ajax.googleapis.com/ajax/libs/jqueryui/1.8.22/themes/smoothness/jquery-ui.css',
    'b_elfinder' : '%selfinder/css/elfinder.min.css' % settings.STATIC_URL
   }
   
A dictionary containing the css files included by yawd-elfinder.

.. _setting-ELFINDER_LANGUAGES_ROOT_URL:

ELFINDER_LANGUAGES_ROOT_URL
---------------------------

Default:: ``'%selfinder/js/i18n/' % settings.STATIC_URL``

The root url under which elfinder translation files are available. You can
override this in your project's root settings 

.. _setting-ELFINDER_LANGUAGES:

ELFINDER_LANGUAGES
------------------

Default::
   ['ar', 'bg', 'ca', 'cs', 'de', 'el', 'es', 'fa', 'fr', 'hu', 'it', 'jp', 'ko', 'nl', 'no', 'pl', 'pt_BR', 'ru', 'tr', 'zh_CN']
   
A list of the available locales. For each one of these locales, a 
`valid elfinder translation file <https://github.com/Studio-42/elFinder/tree/2.x/js/i18n>`_ 
must exist under the :ref:`setting-ELFINDER_LANGUAGES_ROOT_URL` url. You can
override this setting in your project's main setting file.