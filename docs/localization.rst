************
Localization
************

yawd-elfinder automatically detects the current locale using
`Django's internationalization mechanism <https://docs.djangoproject.com/en/dev/topics/i18n/>`_.
If an elFinder translation file is found, it loads the file and displays
elFinder in the current language.

For a list of the available languages see :ref:`setting-ELFINDER_LANGUAGES`.

To provide an additional translation, first copy 
`all existing translation files <https://github.com/yawd/yawd-elfinder/tree/master/elfinder/static/elfinder/js/i18n>`_ 
under a directory of your own. Copy ``elfinder.LANG.js`` to
a new file, provide the translation strings and rename appropriately. Override 
the :ref:`setting-ELFINDER_LANGUAGES` setting to reflect your changes (i.e
add your locale to the list; locale name must conform to _localename).
Finally, override the :ref:`setting-ELFINDER_LANGUAGES_ROOT_URL` setting
to point to your translation directory.
 
**Do not forget** to contribute your translations to the original 
`elfinder <https://github.com/Studio-42/elFinder>`_ project.

.. _localename : https://docs.djangoproject.com/en/dev/topics/i18n/#term-locale-name