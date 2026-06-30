from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=300)
    authors = models.ManyToManyField(Author, related_name="books")
    isbn = models.CharField(max_length=20, unique=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    def clean(self):
        if self.available_copies < 0 or self.available_copies > self.total_copies:
            raise ValidationError(
                "available_copies должен быть в диапазоне от 0 до total_copies."
            )

    def __str__(self):
        return self.title


class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="loans")
    reader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(verbose_name="срок возврата")
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("issued", "Issued"), ("returned", "Returned")],
        default="issued",
    )

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.book} -> {self.reader} ({self.status})"


# Create your models here.
