from django.contrib import admin
from .models import Post, Cooments, Like

# Register your models here.
admin.site.register(Post)
admin.site.register(Cooments)
admin.site.register(Like)