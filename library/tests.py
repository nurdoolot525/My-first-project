from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Author, Book, Loan


class LoanFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff = User.objects.create_user("librarian", password="pass", is_staff=True)
        self.reader = User.objects.create_user("ivan", password="pass")
        self.other_reader = User.objects.create_user("petr", password="pass")

        self.author = Author.objects.create(name="Author One")
        self.book = Book.objects.create(
            title="Django для профи",
            isbn="978-5-00000-000-0",
            total_copies=1,
            available_copies=1,
        )
        self.book.authors.add(self.author)

    def issue(self, user, book_id, reader_id):
        self.client.force_authenticate(user)
        return self.client.post("/api/loans/", {"book_id": book_id, "reader_id": reader_id})

    def test_issue_with_one_copy_then_unavailable(self):
        response = self.issue(self.staff, self.book.id, self.reader.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 0)

        response2 = self.issue(self.staff, self.book.id, self.other_reader.id)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_increments_copies_and_double_return_fails(self):
        response = self.issue(self.staff, self.book.id, self.reader.id)
        loan_id = response.data["id"]

        self.client.force_authenticate(self.staff)
        return_response = self.client.post(f"/api/loans/{loan_id}/return/")
        self.assertEqual(return_response.status_code, status.HTTP_200_OK)

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)

        second_return = self.client.post(f"/api/loans/{loan_id}/return/")
        self.assertEqual(second_return.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_staff_cannot_issue_or_return(self):
        self.client.force_authenticate(self.reader)
        response = self.client.post(
            "/api/loans/", {"book_id": self.book.id, "reader_id": self.reader.id}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        loan = Loan.objects.create(
            book=self.book, reader=self.reader, due_date=date.today() + timedelta(days=14)
        )
        return_response = self.client.post(f"/api/loans/{loan.id}/return/")
        self.assertEqual(return_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reader_sees_only_own_loans_staff_sees_all(self):
        Loan.objects.create(
            book=self.book, reader=self.reader, due_date=date.today() + timedelta(days=14)
        )
        Loan.objects.create(
            book=self.book, reader=self.other_reader, due_date=date.today() + timedelta(days=14)
        )

        self.client.force_authenticate(self.reader)
        response = self.client.get("/api/loans/")
        self.assertEqual(len(response.data), 1)

        self.client.force_authenticate(self.staff)
        response = self.client.get("/api/loans/")
        self.assertEqual(len(response.data), 2)

    def test_overdue_filter(self):
        Loan.objects.create(
            book=self.book, reader=self.reader, due_date=date.today() - timedelta(days=1)
        )
        Loan.objects.create(
            book=self.book, reader=self.other_reader, due_date=date.today() + timedelta(days=5)
        )

        self.client.force_authenticate(self.staff)
        response = self.client.get("/api/loans/?overdue=1")
        self.assertEqual(len(response.data), 1)

    def test_catalog_is_open_to_everyone(self):
        response = self.client.get("/api/books/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
