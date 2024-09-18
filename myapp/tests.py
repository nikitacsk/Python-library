from datetime import date

from django.test import TestCase
from django.urls import reverse
from .models import Author, Book, BorrowRequest
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission


class AuthorViewTests(TestCase):

    def setUp(self):
        self.author = Author.objects.create(name="Author One", bio="This is Author One's bio.")

        self.librarian_user = User.objects.create_user(username='librarian', password='password', is_staff=True)
        self.librarian_user.user_permissions.add(Permission.objects.get(codename='add_author'))
        self.librarian_user.user_permissions.add(Permission.objects.get(codename='change_author'))
        self.librarian_user.user_permissions.add(Permission.objects.get(codename='delete_author'))

        self.normal_user = User.objects.create_user(username='user', password='password')

    def test_author_list_view_status_code(self):
        self.client.login(username='librarian', password='password')
        response = self.client.get(reverse('author_list'))
        self.assertEqual(response.status_code, 200)

    def test_author_list_view_contains_authors(self):
        self.client.login(username='librarian', password='password')
        response = self.client.get(reverse('author_list'))
        self.assertContains(response, self.author.name)

    def test_author_create_view_by_librarian(self):
        self.client.login(username='librarian', password='password')
        response = self.client.post(reverse('author_create'), {
            'name': 'Author Two',
            'bio': 'This is Author Two’s bio.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Author.objects.filter(name="Author Two").exists())

    def test_author_create_view_by_normal_user(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('author_create'))
        self.assertEqual(response.status_code, 403)

    def test_author_update_view_by_librarian(self):
        self.client.login(username='librarian', password='password')
        response = self.client.post(reverse('author_update', args=[self.author.id]), {
            'name': 'Updated Author Name',
            'bio': 'Updated bio.'
        })
        self.assertEqual(response.status_code, 302)
        self.author.refresh_from_db()
        self.assertEqual(self.author.name, 'Updated Author Name')

    def test_author_update_view_by_normal_user(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('author_update', args=[self.author.id]))
        self.assertEqual(response.status_code, 403)

    def test_author_delete_view_by_librarian(self):
        self.client.login(username='librarian', password='password')
        response = self.client.post(reverse('author_delete', args=[self.author.id]))
        self.assertEqual(response.status_code, 403)

    def test_author_delete_view_by_normal_user(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('author_delete', args=[self.author.id]))
        self.assertEqual(response.status_code, 403)


class UserAuthTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_user_login_view_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpassword',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_login_view_failure(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "Please enter a correct username and password.")

    def test_user_logout_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Register")

    def test_register_view_post_success(self):

        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_view_post_failure(self):

        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())
        self.assertContains(response, "A user with that username already exists.")


class BorrowRequestTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.librarian = User.objects.create_user(username='librarian', password='password123', is_staff=True)

        librarians_group = Group.objects.create(name='librarians')
        self.librarian.groups.add(librarians_group)


        self.book = Book.objects.create(
            title='Test Book',
            summary='Test summary',
            isbn='1234567890123',
            available=True,
            published_date=date.today(),
            publisher='Test Publisher'
        )

        self.borrow_request = BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=1
        )

    def test_borrow_history_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('borrow_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')

    def test_borrow_history_view_unauthenticated(self):
        response = self.client.get(reverse('borrow_history'))
        self.assertEqual(response.status_code, 302)

    def test_borrow_request_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('borrow_request', args=[self.book.id]), {})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BorrowRequest.objects.filter(book=self.book, borrower=self.user).exists())

    def test_borrow_request_view_invalid(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('borrow_request', args=[999]), {})
        self.assertEqual(response.status_code, 404)

    def test_borrow_request_list_view_librarian(self):
        self.client.login(username='librarian', password='password123')
        response = self.client.get(reverse('borrow_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')

    def test_borrow_request_list_view_unauthenticated(self):
        response = self.client.get(reverse('borrow_history'))
        self.assertEqual(response.status_code, 302)

    def test_borrow_request_update_view_librarian(self):
        self.client.login(username='librarian', password='password123')
        response = self.client.post(reverse('borrow_request_update', args=[self.borrow_request.id, "approve"]))
        self.assertEqual(response.status_code, 302)
        self.borrow_request.refresh_from_db()
        self.assertEqual(self.borrow_request.status, 2)

    def test_borrow_request_update_view_non_librarian(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('borrow_request_update', args=[self.borrow_request.id, 'approve']))
        self.assertEqual(response.status_code, 403)


class BookDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

        self.book = Book.objects.create(
            title='Test Book',
            summary='This is a test book summary',
            isbn='1234567890123',
            available=True,
            published_date=date.today(),
            publisher='Test Publisher'
        )

    def test_book_detail_view_authenticated(self):
        self.client.login(username='testuser', password='password123')

        response = self.client.get(reverse('book_detail', args=[self.book.pk]))

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Test Book')
        self.assertContains(response, 'This is a test book summary')
        self.assertContains(response, '1234567890123')
        self.assertContains(response, 'Test Publisher')

        self.assertContains(response, 'Request to Borrow')

    def test_book_detail_view_unauthenticated(self):
        response = self.client.get(reverse('book_detail', args=[self.book.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_create_borrow_request(self):
        self.client.login(username='testuser', password='password123')

        response = self.client.post(reverse('book_detail', args=[self.book.pk]), {'borrow': True})

        self.assertEqual(response.status_code, 302)

        borrow_request = BorrowRequest.objects.filter(book=self.book, borrower=self.user).first()
        self.assertIsNotNone(borrow_request)
        self.assertEqual(borrow_request.status, BorrowRequest.PENDING)

        self.book.refresh_from_db()
        self.assertFalse(self.book.available)

    def test_create_duplicate_borrow_request(self):
        self.client.login(username='testuser', password='password123')

        BorrowRequest.objects.create(book=self.book, borrower=self.user, status=BorrowRequest.PENDING)

        response = self.client.post(reverse('book_detail', args=[self.book.pk]), {'borrow': True})

        self.assertEqual(response.status_code, 302)

        borrow_requests = BorrowRequest.objects.filter(book=self.book, borrower=self.user)
        self.assertEqual(borrow_requests.count(), 1)

    def test_collect_book(self):
        self.client.login(username='testuser', password='password123')

        borrow_request = BorrowRequest.objects.create(book=self.book, borrower=self.user, status=BorrowRequest.APPROVED)

        response = self.client.post(reverse('book_detail', args=[self.book.pk]), {'collect': True})

        self.assertEqual(response.status_code, 302)

        borrow_request.refresh_from_db()
        self.assertEqual(borrow_request.status, BorrowRequest.COMPLETE)
        self.assertIsNotNone(borrow_request.complete_date)

        self.book.refresh_from_db()
        self.assertTrue(self.book.available)
