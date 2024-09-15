from django.urls import path

from .views import UserLoginView, RegisterView, HomePageView, UserLogoutView, AuthorListView, AuthorCreateView, \
    AuthorUpdateView, AuthorDeleteView, GenreListView, GenreCreateView, GenreUpdateView, GenreDeleteView, \
    BorrowHistoryView, BookCreateView, BookUpdateView, BookDeleteView, BookListView, BorrowRequestView, \
    BorrowRequestListView, BorrowRequestUpdateView, BookDetailView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('authors/', AuthorListView.as_view(), name='author_list'),
    path('authors/create/', AuthorCreateView.as_view(), name='author_create'),
    path('authors/<int:pk>/update/', AuthorUpdateView.as_view(), name='author_update'),
    path('authors/<int:pk>/delete/', AuthorDeleteView.as_view(), name='author_delete'),
    path('genres/', GenreListView.as_view(), name='genre_list'),
    path('genres/create/', GenreCreateView.as_view(), name='genre_create'),
    path('genres/<int:pk>/update/', GenreUpdateView.as_view(), name='genre_update'),
    path('genres/<int:pk>/delete/', GenreDeleteView.as_view(), name='genre_delete'),
    path('books/create/', BookCreateView.as_view(), name='book_create'),
    path('books/<int:pk>/update/', BookUpdateView.as_view(), name='book_update'),
    path('books/<int:pk>/delete/', BookDeleteView.as_view(), name='book_delete'),
    path('books/', BookListView.as_view(), name='book_list'),
    path('borrow/<int:pk>/', BorrowRequestView.as_view(), name='borrow_request'),
    path('borrow-requests/', BorrowRequestListView.as_view(), name='borrow_requests'),
    path('borrow-request/<int:pk>/<str:action>/', BorrowRequestUpdateView.as_view(), name='borrow_request_update'),
    path('borrow-history/', BorrowHistoryView.as_view(), name='borrow_history'),
    path('book/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
]
