from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from .permissions import IsAdminOrReadOnly
from .serializers import RegisterSerializer, BorrowRequestSerializer, BookSerializer, AuthorSerializer, GenreSerializer, BookStockSerializer, BorrowRequestHistorySerializer
from rest_framework import generics, status, viewsets
from myapp.models import BorrowRequest, Book, Author, Genre
from rest_framework.response import Response


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({'token': token.key, 'user_id': token.user_id})


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class HomePageView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        return Response({'message': 'Welcome to the home page!'}, status=status.HTTP_200_OK)


class BorrowRequestHistoryView(generics.ListAPIView):
    serializer_class = BorrowRequestHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return BorrowRequest.objects.all()
        else:
            return BorrowRequest.objects.filter(borrower=user)


class LibraryFundView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        books = Book.objects.all()
        serialized_books = BookStockSerializer(books, many=True)

        for book in serialized_books.data:
            if book['available']:
                book['availability_status'] = 'Available'
            else:
                book['availability_status'] = 'Not Available'

            book['summary'] = ' '.join(book['summary'].split()[:30]) + '...' if len(book['summary'].split()) > 30 else book['summary']

        return Response(serialized_books.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        book_id = request.data.get('book_id')

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        if not book.available:
            return Response({"detail": "Book is not available right now."}, status=status.HTTP_400_BAD_REQUEST)

        borrow_request = BorrowRequest.objects.create(
            book=book,
            borrower=request.user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )

        book.available = False
        book.save()

        return Response({
            "detail": "Borrow request created.",
            "borrow_request_id": borrow_request.id
        }, status=status.HTTP_201_CREATED)


class BookDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        book_serializer = BookSerializer(book)

        user_borrow_request = None
        if request.user.is_authenticated:
            borrow_request = BorrowRequest.objects.filter(book=book, borrower=request.user).first()
            if borrow_request:
                user_borrow_request = BorrowRequestSerializer(borrow_request).data

        response_data = {
            'book': book_serializer.data,
            'borrow_request': user_borrow_request,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        action = request.data.get('action')

        if action == 'borrow':
            existing_request = BorrowRequest.objects.filter(book=book, borrower=request.user, status__in=[BorrowRequest.PENDING, BorrowRequest.APPROVED]).first()
            if existing_request:
                return Response({"detail": "You already have a pending or approved request for this book."}, status=status.HTTP_400_BAD_REQUEST)

            borrow_request = BorrowRequest.objects.create(
                book=book,
                borrower=request.user,
                status=BorrowRequest.PENDING,
                request_date=timezone.now()
            )
            book.available = False
            book.save()

            return Response({"detail": "Borrow request created.", "request_id": borrow_request.id}, status=status.HTTP_201_CREATED)

        elif action == 'collect':
            borrow_request = BorrowRequest.objects.filter(book=book, borrower=request.user, status=BorrowRequest.APPROVED).first()
            if not borrow_request:
                return Response({"detail": "No approved request found for this book."}, status=status.HTTP_400_BAD_REQUEST)

            borrow_request.status = BorrowRequest.COLLECTED
            borrow_request.save()

            return Response({"detail": "Book collected successfully."}, status=status.HTTP_200_OK)

        else:
            return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]


class BorrowRequestViewSet(viewsets.ModelViewSet):
    queryset = BorrowRequest.objects.all()
    serializer_class = BorrowRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return BorrowRequest.objects.all()
        return BorrowRequest.objects.filter(borrower=self.request.user)

    def perform_create(self, serializer):
        serializer.save(borrower=self.request.user)

    def update(self, request, *args, **kwargs):
        borrow_request = self.get_object()
        action = request.data.get('action')

        if action == 'approve':
            if borrow_request.status != BorrowRequest.PENDING:
                return Response({"error": "Only pending requests can be approved."}, status=status.HTTP_400_BAD_REQUEST)
            borrow_request.status = BorrowRequest.APPROVED
            borrow_request.approval_date = timezone.now()
            borrow_request.due_date = request.data.get('due_date')
            borrow_request.book.available = False
            borrow_request.book.save()

        elif action == 'collect':
            if borrow_request.status != BorrowRequest.APPROVED:
                return Response({"error": "Only approved requests can be collected."},
                                status=status.HTTP_400_BAD_REQUEST)
            borrow_request.status = BorrowRequest.COLLECTED

        elif action == 'complete':
            if borrow_request.status != BorrowRequest.COLLECTED:
                return Response({"error": "Only collected requests can be completed."},
                                status=status.HTTP_400_BAD_REQUEST)
            borrow_request.status = BorrowRequest.COMPLETE
            borrow_request.complete_date = timezone.now()
            borrow_request.book.available = True
            borrow_request.book.save()

        elif action == 'decline':
            if borrow_request.status != BorrowRequest.PENDING:
                return Response({"error": "Only pending requests can be declined."}, status=status.HTTP_400_BAD_REQUEST)
            borrow_request.status = BorrowRequest.DECLINED
        else:
            return Response({"error": "Unknown action."}, status=status.HTTP_400_BAD_REQUEST)

        borrow_request.save()
        return Response(BorrowRequestSerializer(borrow_request).data, status=status.HTTP_200_OK)
