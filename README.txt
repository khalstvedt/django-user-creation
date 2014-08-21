====================
django-user-creation
====================

by Tino de Bruijn (https://bitbucket.org/tino/django-user-creation)

django-user-creation is an app that overrides the admin so that when you create users, you can easily email them a link to activate their account, or their credentials, if you choose to provide those for them.

Usage
=====

1. Install ``django-user-creation`` into your python path.
#. Copy the contents of ``templates`` to a template folder in your project
#. Adjust the activation_subject.txt and activation_email.txt to your wishes
#. Append ``'user_creation'`` to your ``INSTALLED_APPS`` setting
#. Add ``from user_creation import useradmin`` in you root urls.py **after** 
   ``admin.autodiscover()``
#. Add::

	    # user_creation
	    (r'^accounts/', include('user_creation.urls', 'user_creation', 'user_creation')),``
   
   to your root urls.py. You can change the base url ('accounts/') to 
   something different if you want. Note that it only contains a suburl 
   'activate/', so even if you have other stuff included at 'accounts/', you 
   should be fine.
#. If your templates don't extend a main template called ``base_site.html``, adjust ``activate.html`` accordingly.
