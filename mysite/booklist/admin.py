from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Book, Bookshelf, CustomUser, Author, Category, Post, Comment
# Register your models here.

class BookAdmin(admin.ModelAdmin):
    list_display = ['display_authors', 'title', 'display_categories', 'overall_rating']

class BookshelfAdmin(admin.ModelAdmin):
    list_display = ['book', 'rating', 'type', 'status', 'star_display']

class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'title', 'content', 'created_at', 'updated_at']

class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'content', 'created_at']

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('photo', 'is_profile_private', 'favorite_books', 'about_me', 'friends')}),
    )

admin.site.register(Book, BookAdmin)
admin.site.register(Bookshelf, BookshelfAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CustomUser, CustomUserAdmin)