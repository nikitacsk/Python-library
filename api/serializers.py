from datetime import date

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers
from myapp.models import BorrowRequest, Book, Genre, Author


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password', 'confirm_password', 'is_staff']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data['password'] = make_password(validated_data['password'])  # Хешуємо пароль
        return User.objects.create(**validated_data)


class BorrowRequestHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowRequest
        fields = ['book', 'borrower', 'status', 'request_date', 'approval_date', 'due_date', 'complete_date', 'overdue']


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'summary', 'isbn', 'available', 'published_date', 'publisher', 'genres', 'authors']

    def validate_published_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("Publication date cannot be in the future.")
        return value


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'bio']


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class BookStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'authors', 'summary', 'available']


class BorrowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowRequest
        fields = ['id', 'book', 'borrower', 'status', 'overdue', 'request_date', 'approval_date', 'due_date', 'complete_date']
        read_only_fields = ['borrower', 'request_date', 'overdue']

    def validate(self, data):
        if data.get('status') == BorrowRequest.APPROVED and not data.get('approval_date'):
            raise serializers.ValidationError("Approval date is required when status is 'Approved'.")
        if data.get('status') == BorrowRequest.COMPLETE and not data.get('complete_date'):
            raise serializers.ValidationError("Complete date is required when status is 'Complete'.")
        return data
