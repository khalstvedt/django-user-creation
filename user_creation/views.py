from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth import login, authenticate
from django.template.response import TemplateResponse
from django.contrib import messages

from forms import SetPasswordForm
from models import ActivationProfile

ACCOUNT_ACTIVATION_DAYS = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 30)

def activate(request, activation_key, template_name='user_creation/activate.html'):
    """
    Activates an account if the given key exists and if a password is given through the form.
    """
    activation_key = activation_key.lower() # Normalize before trying anything with it.
    if request.method == 'POST':
        form = SetPasswordForm('', request.POST)
        account = True
        if form.is_valid():
            account = ActivationProfile.objects.activate_user(form.cleaned_data['activation_key'])
            if account:
                form.user = account
                form.save(True)
                user = authenticate(username=account.username, password=form.cleaned_data['new_password1'])
                user.backend = settings.AUTHENTICATION_BACKENDS[0]
                login(request, user)
                messages.success(request, _("Your password has been set, \
                    please remember to remember it. You are now logged in."))
                return HttpResponseRedirect(getattr(settings, 'LOGIN_REDIRECT_URL','/'))
            else:
                form.error_messages={'error': _('Tampered activation key')}
    else:
        account = ActivationProfile.objects.check_key(activation_key)
        form = SetPasswordForm(account, initial={'activation_key':activation_key})
    return TemplateResponse(request, template_name,
                              { 'account': account,
                                'expiration_days': ACCOUNT_ACTIVATION_DAYS,
                                'set_password_form':form })