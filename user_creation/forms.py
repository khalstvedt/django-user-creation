from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _
from models import ActivationProfile

class AccountCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and password.
    """
    username = forms.RegexField(label=_("Username"), max_length=30, regex=r'^\w+$',
        help_text = _("Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores)."),
        error_message = _("This value must contain only letters, numbers and underscores."))
    email = forms.EmailField(label=_("Email address"))
    password1 = forms.CharField(label=_("Password"), 
                                widget=forms.PasswordInput,
                                required=False,
                                help_text = _("Leave blank to create a user with "
                                "a random password and an activation profile. Only "
                                "use this if you want to set up an account with a "
                                "known password"))
    password2 = forms.CharField(label=_("Password confirmation"), 
                                widget=forms.PasswordInput,
                                required=False,
                                help_text = _("Enter the same password as above, "
                                "for verification."))
    email_user = forms.BooleanField(initial=True, label=_("Send the user a notification email"), required=False,
        help_text = _("If you generate a random password, this will be an email with an activation link. Otherwise it will contain the users login credentials"))

    class Meta:
        model = User
        fields = ("username", "email", "email_user")
        
    def clean_username(self):
        """ Validates that the username is alphanumeric and not already in use. """
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_("A user with that username already exists."))
        
    def clean_email(self):
        """ Validates that the email address is not already in use. """
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(_("A user with that email address already exists."))
        
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
        
    def save(self, *args, **kwargs):
        """ Creates a normal new user and return that, or creates an inactive user with an activation profile. """ 
        user = super(AccountCreationForm, self).save(*args, **kwargs)
        user.save()
        new_user = ActivationProfile.objects.create_profile(user, 
                            password=self.cleaned_data["password1"], 
                            send_email=self.cleaned_data["email_user"])
        return user
        
class EmailAccountCreationForm(AccountCreationForm):
    """
    A form for using this app in conjunction with django-email-login.
    """
    def __init__(self, *args, **kwargs):
        super(EmailAccountCreationForm, self).__init__(*args, **kwargs)
        del self.fields['username']

class SetPasswordForm(forms.Form):
    """
    A form that lets a user change or set his/her password without entering
    the old password
    """
    new_password1 = forms.CharField(label=_("New password"), widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("New password confirmation"), widget=forms.PasswordInput)
    activation_key = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user