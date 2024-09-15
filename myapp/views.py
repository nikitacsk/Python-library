from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserRegistrationForm, AuthorForm, GenreForm, BookForm
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from .models import Author, Genre, BorrowRequest, Book
from .permissions import LibrarianOrAdminMixin, AdminOnlyMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class UserLoginView(LoginView):
    template_name = 'login.html'
    form_class = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('home')


class RegisterView(View):

    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Username is already taken.')
            else:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data.get('password'))
                user.save()
                messages.success(request, 'Registration successful!')
                return redirect('login')
        return render(request, 'register.html', {'form': form})


class UserLogoutView(View):
    template_name = 'logout.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        return LogoutView.as_view(next_page=reverse_lazy('login'))(request)


class HomePageView(TemplateView):
    template_name = 'home.html'


class BorrowHistoryView(LoginRequiredMixin, ListView):
    model = BorrowRequest
    template_name = 'borrow_history.html'
    context_object_name = 'borrow_requests'

    def get_queryset(self):
        if self.request.user.is_staff:
            return BorrowRequest.objects.all()
        return BorrowRequest.objects.filter(borrower=self.request.user)


class AuthorListView(LibrarianOrAdminMixin, ListView):
    model = Author
    template_name = 'authors/author_list.html'
    context_object_name = 'authors'


class AuthorCreateView(LibrarianOrAdminMixin, CreateView):
    model = Author
    form_class = AuthorForm
    template_name = 'authors/author_form.html'
    success_url = reverse_lazy('author_list')


class AuthorUpdateView(LibrarianOrAdminMixin, UpdateView):
    model = Author
    form_class = AuthorForm
    template_name = 'authors/author_form.html'
    success_url = reverse_lazy('author_list')


class AuthorDeleteView(AdminOnlyMixin, DeleteView):
    model = Author
    template_name = 'authors/author_confirm_delete.html'
    success_url = reverse_lazy('author_list')


class GenreListView(LibrarianOrAdminMixin, ListView):
    model = Genre
    template_name = 'genres/genre_list.html'
    context_object_name = 'genres'


class GenreCreateView(LibrarianOrAdminMixin, CreateView):
    model = Genre
    form_class = GenreForm
    template_name = 'genres/genre_form.html'
    success_url = reverse_lazy('genre_list')


class GenreUpdateView(LibrarianOrAdminMixin, UpdateView):
    model = Genre
    form_class = GenreForm
    template_name = 'genres/genre_form.html'
    success_url = reverse_lazy('genre_list')


class GenreDeleteView(AdminOnlyMixin, DeleteView):
    model = Genre
    template_name = 'genres/genre_confirm_delete.html'
    success_url = reverse_lazy('genre_list')


class BookCreateUpdateMixin(LoginRequiredMixin, UserPassesTestMixin):
    model = Book
    form_class = BookForm
    template_name = 'book_form.html'

    def test_func(self):
        return self.request.user.is_staff


class BookCreateView(BookCreateUpdateMixin, CreateView):
    success_url = reverse_lazy('book_list')


class BookUpdateView(BookCreateUpdateMixin, UpdateView):
    success_url = reverse_lazy('book_list')


class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    template_name = 'book_confirm_delete.html'
    success_url = reverse_lazy('book_list')

    def test_func(self):
        return self.request.user.is_staff


class BookListView(ListView):
    model = Book
    template_name = 'book_list.html'
    context_object_name = 'books'

    def get_queryset(self):
        return Book.objects.all()


@method_decorator(login_required, name='dispatch')
class BookDetailView(View):
    def get(self, request, pk):
        # Get the specific book by ID
        book = get_object_or_404(Book, pk=pk)
        user_borrow_request = None

        # Check if the user already has a borrow request for this book
        if request.user.is_authenticated:
            user_borrow_request = BorrowRequest.objects.filter(book=book, borrower=request.user).first()

        context = {
            'book': book,
            'user_borrow_request': user_borrow_request
        }
        return render(request, 'book_detail.html', context)

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        user_borrow_request = BorrowRequest.objects.filter(book=book, borrower=request.user).first()

        if 'borrow' in request.POST:
            if not user_borrow_request:
                BorrowRequest.objects.create(book=book, borrower=request.user, status=BorrowRequest.PENDING)
                book.available = False
                book.save()
                messages.success(request, 'Your borrow request has been submitted.')
            else:
                messages.error(request, 'You already have a borrow request for this book.')

        elif 'collect' in request.POST and user_borrow_request and user_borrow_request.status == BorrowRequest.APPROVED:
            user_borrow_request.status = BorrowRequest.COMPLETE
            user_borrow_request.complete_date = timezone.now()
            user_borrow_request.save()
            book.available = True
            book.save()
            messages.success(request, 'You have collected the book.')

        return redirect('book_detail', pk=book.pk)


class BorrowRequestView(View):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)

        if not BorrowRequest.objects.filter(book=book, borrower=request.user).exists():
            BorrowRequest.objects.create(book=book, borrower=request.user)
            messages.success(request, f"You have successfully requested to borrow '{book.title}'.")
        else:
            messages.warning(request, f"You have already requested to borrow '{book.title}'.")

        return redirect('book_list')


class BorrowRequestListView(View):
    def get(self, request):
        if not request.user.is_staff:
            return redirect('home')

        borrow_requests = BorrowRequest.objects.all()
        return render(request, 'borrow_requests.html', {'borrow_requests': borrow_requests})


class BorrowRequestUpdateView(View):
    def post(self, request, pk, action):
        borrow_request = get_object_or_404(BorrowRequest, pk=pk)

        if action == 'approve':
            if borrow_request.book.available:
                borrow_request.status = BorrowRequest.APPROVED
                borrow_request.approval_date = timezone.now()
                borrow_request.book.available = False
                borrow_request.book.save()
                messages.success(request, 'The borrow request has been approved.')
            else:
                messages.error(request, 'The book is not available.')

        elif action == 'decline':
            borrow_request.status = BorrowRequest.DECLINED
            messages.success(request, 'The borrow request has been declined.')

        elif action == 'complete':
            borrow_request.status = BorrowRequest.COMPLETE
            borrow_request.complete_date = timezone.now()
            borrow_request.book.available = True
            borrow_request.book.save()
            messages.success(request, 'The borrow request has been completed.')

        borrow_request.save()
        return redirect('borrow_requests')
