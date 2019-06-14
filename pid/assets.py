# -*- coding: utf-8 -*-
"""Application assets."""
from flask_assets import Bundle, Environment

css = Bundle(
    'libs/bootstrap-3.3.0/css/bootstrap.min.css',
    'libs/bootflat-2.0.4/css/bootflat.min.css',
    'libs/photoswipe-4.1.2/css/photoswipe.css',
    'libs/photoswipe-4.1.2/default-skin/default-skin.css',
    'libs/bootstrap3-editable-5d8ecf3/css/bootstrap-editable.css',
    'libs/bootstrap-datepicker-1.7.0/css/bootstrap-datepicker3.min.css',
    'libs/jasny-bootstrap-3.1.3/css/jasny-bootstrap.min.css',
    'libs/jBox-0.4.8/jBox.css',
    'libs/jquery-typeahead-2.8.0/css/jquery.typeahead.min.css',
    'libs/DataTables-1.10.15/css/datatables.css',
    'libs/trumbowyg-2.7.0/ui/trumbowyg.min.css',
    'libs/trumbowyg-2.7.0/plugins/colors/ui/trumbowyg.colors.min.css',
    'css/fonts.css',
    'css/code-blocks.css',
    'css/pri-icons.css',
    'css/header.css',
    'css/footer.css',
    'css/navbar.css',
    'css/typeahead.css',
    'css/style.css',
    filters='cssmin',
    output='public/css/common.css'
)

js = Bundle(
    'libs/jquery-3.2.1/jquery.min.js',
    'libs/jqueryrotate-2.3/jqueryrotate.min.js',                        # For rotating spacecraft only at this point
    'libs/form-4.2.1/jquery.form.min.js',                               # For easy submitting HTML forms via AJAX
    'libs/bootstrap-3.3.0/js/bootstrap.min.js',
    'libs/bootstrap-datepicker-1.7.0/js/bootstrap-datepicker.min.js',
    'libs/dropzone-4.3.0/js/dropzone.min.js',                           # For document/image drag and drops
    'libs/photoswipe-4.1.2/js/photoswipe.min.js',                       # For image galleries
    'libs/photoswipe-4.1.2/js/photoswipe-ui-default.min.js',
    'libs/jquery.photoswipe-global.js',                                 # Makes photoswipe easier. From https://github.com/yaquawa/jquery.photoswipe
    'libs/bootstrap3-editable-5d8ecf3/js/bootstrap-editable.min.js',    # For inline editing
    'libs/bootstrap-notify-7b4711e/bootstrap-notify.min.js',            # For success/error alerts with AJAX calls
    'libs/jasny-bootstrap-3.1.3/js/jasny-bootstrap.min.js',             # For entire table rows to act as clickable links
    'libs/jBox-0.4.8/jBox.min.js',                                      # For modals
    'libs/jquery-typeahead-2.8.0/js/jquery.typeahead.min.js',           # For typeahead searches
    'libs/jquery-treetable-3.2.0/jquery.treetable.js',
    'libs/garand-sticky-5cfc20c/jquery.sticky.js',                      # For sticky header row
    'libs/DataTables-1.10.15/js/datatables.js',
    'libs/trumbowyg-2.7.0/trumbowyg.min.js',                            # WYSIWYG editor
    'libs/trumbowyg-2.7.0/plugins/colors/trumbowyg.colors.min.js',
    'libs/trumbowyg-2.7.0/plugins/preformatted/trumbowyg.preformatted.min.js',
    'libs/trumbowyg-2.7.0/plugins/base64/trumbowyg.base64.min.js',
    'libs/velocity-1.5.0/velocity.min.js',                              # Effects library
    'libs/konami-js-1.4.6/konami.js',
    'js/globals.js',                                                    # Default settings for various JS libs
    'js/jquery-plugins.js',                                             # Various small jQuery helper scripts
    'js/functions.js',                                                  # Our own JS functions
    'js/modals.js',                                                     # Global modals
    filters='jsmin',
    output='public/js/common.js'
)

assets = Environment()

assets.register('js_all', js)
assets.register('css_all', css)

css_dev = Bundle(
    'libs/bootstrap-3.3.0/css/bootstrap.css',
    'libs/bootflat-2.0.4/css/bootflat.css',
    'libs/photoswipe-4.1.2/css/photoswipe.css',
    'libs/photoswipe-4.1.2/default-skin/default-skin.css',
    'libs/bootstrap3-editable-5d8ecf3/css/bootstrap-editable.css',
    'libs/bootstrap-datepicker-1.7.0/css/bootstrap-datepicker3.css',
    'libs/jasny-bootstrap-3.1.3/css/jasny-bootstrap.css',
    'libs/jBox-0.4.8/jBox.css',
    'libs/jquery-typeahead-2.8.0/css/jquery.typeahead.css',
    'libs/DataTables-1.10.15/css/datatables.css',
    'libs/trumbowyg-2.7.0/ui/trumbowyg.css',
    'libs/trumbowyg-2.7.0/plugins/colors/ui/trumbowyg.colors.css',
    'css/fonts.css',
    'css/code-blocks.css',
    'css/pri-icons.css',
    'css/header.css',
    'css/footer.css',
    'css/navbar.css',
    'css/typeahead.css',
    'css/style.css',
    filters='cssmin',
    output='public/css/common.css'
)

js_dev = Bundle(
    'libs/jquery-3.2.1/jquery.js',
    'libs/jqueryrotate-2.3/jqueryrotate.js',                        # For rotating spacecraft only at this point
    'libs/form-4.2.1/jquery.form.js',                               # For easy submitting HTML forms via AJAX
    'libs/bootstrap-3.3.0/js/bootstrap.js',
    'libs/bootstrap-datepicker-1.7.0/js/bootstrap-datepicker.js',
    'libs/dropzone-4.3.0/js/dropzone.js',                           # For document/image drag and drops
    'libs/photoswipe-4.1.2/js/photoswipe.js',                       # For image galleries
    'libs/photoswipe-4.1.2/js/photoswipe-ui-default.js',
    'libs/jquery.photoswipe-global.js',                             # Makes photoswipe easier. From https://github.com/yaquawa/jquery.photoswipe
    'libs/bootstrap3-editable-5d8ecf3/js/bootstrap-editable.js',    # For inline editing
    'libs/bootstrap-notify-7b4711e/bootstrap-notify.js',            # For success/error alerts with AJAX calls
    'libs/jasny-bootstrap-3.1.3/js/jasny-bootstrap.js',             # For entire table rows to act as clickable links
    'libs/jBox-0.4.8/jBox.js',                                      # For modals
    'libs/jquery-typeahead-2.8.0/js/jquery.typeahead.js',           # For typeahead searches
    'libs/jquery-treetable-3.2.0/jquery.treetable.js',
    'libs/garand-sticky-5cfc20c/jquery.sticky.js',                  # For sticky header row
    'libs/DataTables-1.10.15/js/datatables.js',                     # For sortable tables etc on dashboard
    'libs/trumbowyg-2.7.0/trumbowyg.js',                            # WYSIWYG editor
    'libs/trumbowyg-2.7.0/plugins/colors/trumbowyg.colors.js',
    'libs/trumbowyg-2.7.0/plugins/preformatted/trumbowyg.preformatted.js',
    'libs/trumbowyg-2.7.0/plugins/base64/trumbowyg.base64.js',
    'libs/trumbowyg-2.7.0/plugins/cleanpaste/trumbowyg.cleanpaste.js',
    'libs/velocity-1.5.0/velocity.js',                              # Effects library
    'libs/konami-js-1.4.6/konami.js',
    'js/globals.js',                                                # Default settings for various JS libs
    'js/jquery-plugins.js',                                         # Various small jQuery helper scripts
    'js/functions.js',                                              # Our own JS functions
    'js/modals.js',                                                 # Global modals
    filters='jsmin',
    output='public/js/common.js'
)

assets.register('js_dev', js_dev)
assets.register('css_dev', css_dev)
