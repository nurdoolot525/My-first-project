from django.contrib import admin

from .models import Author, Book, Loan

# Register your models here.


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "isbn", "total_copies", "available_copies")
    search_fields = ("title", "isbn")
    list_filter = ("authors",)
    filter_horizontal = ("authors",)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("id", "book", "reader", "status", "issued_at", "due_date")
    list_filter = ("status",)
    search_fields = ("book__title", "reader__username")
