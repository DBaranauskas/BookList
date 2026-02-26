from sqlite3 import IntegrityError

from django.contrib import messages
from django.shortcuts import redirect

from .models import CustomUser, Post, Bookshelf, Comment
from django import forms
from django.contrib.auth.forms import UserCreationForm

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'about_me', 'photo', 'is_profile_private']
        widgets = {'is_profile_private': forms.CheckboxInput,
                   'about_me': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell others about yourself...'})}

class CustomUserCreateForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class PostCreateUpdateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']

class BookshelfCreateUpdateForm(forms.ModelForm):
    class Meta:
        model = Bookshelf
        fields = ['book', 'type', 'comment', 'rating', 'status']

class FavoriteUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['favorite_books']
        widgets = {
            'favorite_books': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['favorite_books'].queryset = user.user_books.all()

class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 3,
        'placeholder': 'Write your comment...'
    }), label='')

    class Meta:
        model = Comment
        fields = ['content']