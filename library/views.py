from datetime import date

from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import Author, Book, Loan
from .permissions import IsAdminUserOrReadOnly
from .serializers import (
    AuthorSerializer,
    BookSerializer,
    LoanCreateSerializer,
    LoanSerializer,
)

ALLOWED_ORDERING_FIELDS = {"title","-title","isbn","-isbn","available_copies","-available_copies","total_copies","total_copies"}


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]

    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, description="Поиск по title, authors__name"),
            OpenApiParameter("available", str, description="1 — только книги с available_copies > 0"),
            OpenApiParameter("ordering", str, description="Сортировка: title, isbn, available_copies"),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(authors__name__icontains=search)
            ).distinct()

        if self.request.query_params.get("available") == "1":
            queryset = queryset.filter(available_copies__gt=0)

        ordering = self.request.query_params.get("ordering")
        if ordering and ordering in ALLOWED_ORDERING_FIELDS:
            queryset = queryset.order_by(ordering)

        return queryset


class AuthorViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class LoanViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    queryset = Loan.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return LoanCreateSerializer
        return LoanSerializer

    def get_permissions(self):
        if self.action in ("create", "return_loan"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @extend_schema(
        parameters=[
            OpenApiParameter("overdue", str, description="1 — только просроченные выдачи (staff)"),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_staff:
            queryset = queryset.filter(reader=self.request.user)

        if self.request.query_params.get("overdue") == "1":
            if not self.request.user.is_staff:
                return queryset.none()
            queryset = queryset.filter(status="issued", due_date__lt=date.today())

        return queryset

    @extend_schema(request=LoanCreateSerializer, responses=LoanSerializer)
    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        book = write_serializer.validated_data["book_id"]

        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=book.pk)

            if book.available_copies == 0:
                return Response(
                    {"detail": "Нет доступных экземпляров книги."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            loan = write_serializer.save()
            Book.objects.filter(pk=book.pk).update(
                available_copies=F("available_copies") - 1
            )

        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=LoanSerializer)
    @action(detail=True, methods=["post"], url_path="return")
    def return_loan(self, request, pk=None):
        get_object_or_404(Loan, pk=pk)

        with transaction.atomic():
            loan = Loan.objects.select_for_update().get(pk=pk)

            if loan.status != "issued":
                return Response(
                    {"detail": "Эта выдача уже возвращена."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            loan.status = "returned"
            loan.returned_at = timezone.now()
            loan.save(update_fields=["status", "returned_at"])

            Book.objects.filter(pk=loan.book_id).update(
                available_copies=F("available_copies") + 1
            )

        return Response(LoanSerializer(loan).data, status=status.HTTP_200_OK)