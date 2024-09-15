from django.urls import path, include
from .views import RegisterView, LoginView, LogoutView, HomePageView, BorrowRequestHistoryView, BookViewSet, \
    AuthorViewSet, GenreViewSet, LibraryFundView, BorrowRequestViewSet, BookDetailView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'borrow-requests', BorrowRequestViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api_register'),
    path('login/', LoginView.as_view(), name='api_login'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
    path('home/', HomePageView.as_view(), name='api_home'),
    path('borrow-history/', BorrowRequestHistoryView.as_view(), name='api_borrow_history'),
    path('', include(router.urls)),
    path('library/', LibraryFundView.as_view(), name='api_library_fund'),
    path('bookdetail/<int:book_id>/', BookDetailView.as_view(), name='api_book-detail'),
]
