from django.contrib import admin

from .models import UserOpenID


class UserOpenIDAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserOpenID, UserOpenIDAdmin)
