"""
Override the account creation form in the admin.
"""
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from forms import AccountCreationForm

class UserCreationAdmin(UserAdmin):
    add_form = AccountCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'email_user')}
        ),
    )
    
admin.site.unregister(User)
admin.site.register(User, UserCreationAdmin)