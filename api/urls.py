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
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('home/', HomePageView.as_view(), name='home'),
    path('borrow-history/', BorrowRequestHistoryView.as_view(), name='borrow_history'),
    path('', include(router.urls)),
    path('library/', LibraryFundView.as_view(), name='library_fund'),
    path('bookdetail/<int:book_id>/', BookDetailView.as_view(), name='book-detail'),
]
