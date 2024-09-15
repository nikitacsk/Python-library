from django import forms
from django.contrib.auth.models import User
from .models import Author, Genre, Book
from django.utils import timezone


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password', 'is_staff']

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'bio']


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name']


class BookForm(forms.ModelForm):
    published_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Book
        fields = [
            'title', 'summary', 'isbn', 'available', 'published_date', 'publisher',
            'genres', 'authors',
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'genres': forms.CheckboxSelectMultiple(),
            'authors': forms.CheckboxSelectMultiple(),
        }

    def clean_published_date(self):
        published_date = self.cleaned_data.get('published_date')
        if published_date > timezone.now().date():
            raise forms.ValidationError("The published date cannot be in the future.")
        return published_date
