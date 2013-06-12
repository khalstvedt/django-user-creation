"""
Based on James Bennett's django-registration 
(http://bitbucket.org/ubernostrum/django-registration).
"""

import datetime
import random
import re

from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.hashcompat import sha_constructor
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail


SHA1_RE = re.compile('^[a-f0-9]{40}$')

ACCOUNT_ACTIVATION_DAYS = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 30)


class ActivationManager(models.Manager):
    """
    Custom manager for the ``ActivationProfile`` model.
    
    The methods defined here provide shortcuts for account creation
    and activation (including generation and emailing of activation
    keys), and for cleaning out expired inactive accounts.
    
    """
    
    def check_key(self, activation_key):
        """
        Checks to see if the activation_key exists.
        """
        
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not profile.activation_key_expired():
                return profile.user
        return False
        
    def activate_user(self, activation_key):
        """
        Validate an activation key and activate the corresponding
        ``User`` if valid.
        
        If the key is valid and has not expired, return the ``User``
        after activating.
        
        If the key is not valid or has expired, return ``False``.
        
        If the key is valid but the ``User`` is already active,
        return ``False``.
        
        To prevent reactivation of an account which has been
        deactivated by site administrators, the activation key is
        reset to the string ``ALREADY_ACTIVATED`` after successful
        activation.
        
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                user.save()
                profile.delete()
                return user
        return False
    
    def create_profile(self, user, password='', send_email=True, 
        profile_callback=None):
        """
        Create an ``ActivationProfile`` for a given ``User`` if no
        ``password`` is given. Email its activation key to the ``User`` if
        ``send_email`` is ``True``. It will also set the ``user.is_active`` to
        True, and set an invalid password.
        
         If a password is given, the username and password will be mailed to
        the user.
        
         The activation key for the ``ActivationProfile`` will be a SHA1 hash,
        generated from a combination of the ``User``'s username and a random
        salt.
        
         To enable creation of a custom user profile along with the ``User``
        (e.g., the model specified in the ``AUTH_PROFILE_MODULE`` setting),
        define a function which knows how to create and save an instance of
        that model with appropriate default values, and pass it as the keyword
        argument ``profile_callback``. This function should accept one keyword
        argument:

        ``user``
            The ``User`` to relate the profile to.
        
        """
        if password == '':
            user.set_unusable_password()
            user.is_active = True
            user.save()
            salt = sha_constructor(str(random.random())).hexdigest()[:5]
            activation_key = sha_constructor(salt+user.username).hexdigest()
            activation_profile = self.create(user=user, activation_key=activation_key)
            if send_email:
                self.mail_activation_link(user, activation_profile)
        else:
            user.set_password(password)
            user.save()
            if send_email:
                self.mail_credentials(user, password)
            else:
                activation_profile = False
        if profile_callback is not None:
            profile_callback(user=new_user)
        
        return activation_profile
    
    def delete_expired_users(self):
        """
        Remove expired instances of ``ActivationProfile``.
        
        Profiles older than ``ACTIVATION_KEY_EXPIRY`` setting will be removed.
        """
        oldest = datetime.datetime.now() - \
            datetime.timedelta(days=ACCOUNT_ACTIVATION_DAYS)
        self.filter(creation_date__lt=oldest).delete()
                
    def mail_activation_link(self, user, activation_profile):
        """
        Sends the activation link to the users email.
        """
        current_site = Site.objects.get_current()
        
        subject = render_to_string('accounts/activation_email_subject.txt',
                                   { 'site': current_site })
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        message = render_to_string('accounts/activation_email.txt',
                                   { 'activation_profile': activation_profile,
                                     'expiration_days': ACCOUNT_ACTIVATION_DAYS,
                                     'site': current_site })
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    
    def mail_credentials(self, user, password):
        """
        Sends the credentials to the users email.
        """
        current_site = Site.objects.get_current()
        
        subject = render_to_string('accounts/activation_email_subject.txt',
                                   { 'site': current_site })
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        message = render_to_string('accounts/credentials_email.txt',
                                   { 'username' : user.username,
                                     'password': password,
                                     'site': current_site })
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

class ActivationProfile(models.Model):
    """
    A simple profile which stores an activation key for use during
    user account activation.
    
    Generally, you will not want to interact directly with instances
    of this model; the provided manager includes methods
    for creating and activating new accounts, as well as for cleaning
    out accounts which have never been activated.
    
    While it is possible to use this model as the value of the
    ``AUTH_PROFILE_MODULE`` setting, it's not recommended that you do
    so. This model's sole purpose is to store data temporarily during
    account registration and activation, and a mechanism for
    automatically creating an instance of a site-specific profile
    model is provided via the ``create_inactive_user`` on
    ``RegistrationManager``.
    
    """
    user = models.ForeignKey(User, unique=True, verbose_name=_('user'))
    activation_key = models.CharField(_('activation key'), max_length=40)
    creation_date = models.DateField(default=datetime.datetime.now)
    
    objects = ActivationManager()
    
    class Meta:
        verbose_name = _('activation profile')
        verbose_name_plural = _('activation profiles')
    
    def __unicode__(self):
        return u"Activation information for %s" % self.user
    
    def activation_key_expired(self):
        """
        Determine whether this ``ActivationProfile``'s activation
        key has expired, returning a boolean -- ``True`` if the key
        has expired.
        
        The date the user signed up is incremented by
        the number of days specified in the setting
        ``ACTIVATION_KEY_EXPIRY`` (which should be the number of
        days after signup during which a user is allowed to
        activate their account); if the result is less than or
        equal to the current date, the key has expired and this
        method returns ``True``.
        
        """
        expiration_date = datetime.timedelta(days=ACCOUNT_ACTIVATION_DAYS)
        return self.creation_date + expiration_date <= datetime.date.today()
    activation_key_expired.boolean = True
