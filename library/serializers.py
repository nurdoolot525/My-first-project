from datetime import date, timedelta

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Author, Book, Loan

LOAN_PERIOD_DAYS = 14


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio"]


class BookSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), many=True
    )

    class Meta:
        model = Book
        fields = ["id", "title", "authors", "isbn", "total_copies", "available_copies"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["authors"] = [author.name for author in instance.authors.all()]
        return data


class LoanSerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()
    reader = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = ["id", "book", "reader", "issued_at", "due_date", "returned_at", "status"]
        read_only_fields = ["issued_at", "due_date", "returned_at", "status"]

    def get_book(self, obj):
        return obj.book.title

    def get_reader(self, obj):
        return obj.reader.username


class LoanCreateSerializer(serializers.Serializer):
    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    reader_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def create(self, validated_data):
        loan = Loan.objects.create(
            book=validated_data["book_id"],
            reader=validated_data["reader_id"],
            due_date=date.today() + timedelta(days=LOAN_PERIOD_DAYS),
        )
        return loan
