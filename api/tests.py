from datetime import timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from myapp.models import Book, BorrowRequest
from django.utils import timezone
from rest_framework.authtoken.models import Token


class UserAuthenticationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_register_view(self):
        url = reverse('api_register')

        data = {
            'username': 'newuser',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_view_password_mismatch(self):
        url = reverse('api_register')

        data = {
            'username': 'newuser',
            'password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_view(self):
        url = reverse('api_login')

        data = {
            'username': 'testuser',
            'password': 'password123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('token', response.data)

    def test_login_view_invalid_credentials(self):
        url = reverse('api_login')

        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view(self):
        login_url = reverse('api_login')
        logout_url = reverse('api_logout')

        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        login_response = self.client.post(login_url, data, format='json')

        token = login_response.data.get('token')

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.post(logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        protected_url = reverse('api_library_fund')
        protected_response = self.client.get(protected_url)

        self.assertEqual(protected_response.status_code, status.HTTP_401_UNAUTHORIZED)


class LibraryFundViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.token = Token.objects.create(user=self.user)

        self.superuser = User.objects.create_superuser(username='admin', password='admin123')
        self.superuser_token = Token.objects.create(user=self.superuser)

        self.book1 = Book.objects.create(
            title='Book One',
            summary='A long summary of book one that exceeds thirty words for testing purposes.fd g dfg dfg dg dg df '
                    'gd g dg d gf d dg gf d gdg  ' * 2,
            isbn='1234567890123',
            available=True,
            published_date='2023-01-01',
            publisher='Publisher One'
        )
        self.book2 = Book.objects.create(
            title='Book Two',
            summary='A short summary of book two.',
            isbn='1234567890124',
            available=False,
            published_date='2023-02-01',
            publisher='Publisher Two'
        )

    def authenticate(self, user_type='regular'):
        """Helper method to authenticate with a token."""
        if user_type == 'regular':
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        elif user_type == 'superuser':
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.superuser_token.key)

    def test_get_library_fund(self):
        url = reverse('api_library_fund')

        self.authenticate()

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 2)

        for book in response.data:
            if book['available']:
                self.assertEqual(book['availability_status'], 'Available')
            else:
                self.assertEqual(book['availability_status'], 'Not Available')

        book1_response = next(book for book in response.data if book['title'] == 'Book One')
        self.assertTrue(book1_response['summary'].endswith('...'))

    def test_post_borrow_request_authenticated(self):
        url = reverse('api_library_fund')

        self.authenticate()

        response = self.client.post(url, {'book_id': self.book1.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(BorrowRequest.objects.filter(book=self.book1, borrower=self.user).exists())

        self.book1.refresh_from_db()
        self.assertFalse(self.book1.available)

        self.assertIn('borrow_request_id', response.data)

    def test_post_borrow_request_unauthenticated(self):
        url = reverse('api_library_fund')

        response = self.client.post(url, {'book_id': self.book1.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertFalse(BorrowRequest.objects.filter(book=self.book1).exists())

    def test_post_borrow_request_book_not_available(self):
        url = reverse('api_library_fund')

        self.authenticate()

        response = self.client.post(url, {'book_id': self.book2.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(BorrowRequest.objects.filter(book=self.book2, borrower=self.user).exists())

    def test_post_borrow_request_book_not_found(self):
        url = reverse('api_library_fund')

        self.authenticate()

        response = self.client.post(url, {'book_id': 9999}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_token_expiration(self):
        self.token.created = timezone.now() - timedelta(minutes=2)
        self.token.save()

        self.authenticate()

        url = reverse('api_library_fund')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Token has expired')

    def test_superuser_token_not_expire(self):
        self.superuser_token.created = timezone.now() - timedelta(minutes=2)
        self.superuser_token.save()

        self.authenticate(user_type='superuser')

        url = reverse('api_library_fund')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BookDetailViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.token = Token.objects.create(user=self.user)

        self.book = Book.objects.create(
            title='Test Book',
            summary='This is a test summary for the book.',
            isbn='1234567890123',
            available=True,
            published_date='2023-01-01',
            publisher='Test Publisher'
        )

        self.url = reverse('api_book-detail', kwargs={'book_id': self.book.id})

    def authenticate(self):
        """Helper method to set up token authentication for the user."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_get_book_detail_unauthenticated(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('book', response.data)
        self.assertIsNone(response.data['borrow_request'])

    def test_get_book_detail_authenticated(self):
        self.authenticate()

        BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('book', response.data)
        self.assertIn('borrow_request', response.data)
        self.assertIsNotNone(response.data['borrow_request'])

    def test_get_book_detail_not_found(self):
        url = reverse('api_book-detail', kwargs={'book_id': 9999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Book not found.')

    def test_post_borrow_book_authenticated(self):
        self.authenticate()

        response = self.client.post(self.url, {'action': 'borrow'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'Borrow request created.')
        self.assertIn('request_id', response.data)

        self.assertTrue(BorrowRequest.objects.filter(book=self.book, borrower=self.user).exists())

        self.book.refresh_from_db()
        self.assertFalse(self.book.available)

    def test_post_borrow_book_unauthenticated(self):
        response = self.client.post(self.url, {'action': 'borrow'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Authentication credentials were not provided.')

    def test_post_borrow_book_already_requested(self):
        self.authenticate()

        BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )

        response = self.client.post(self.url, {'action': 'borrow'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'You already have a pending or approved request for this book.')

    def test_post_collect_book_no_approved_request(self):
        self.authenticate()

        response = self.client.post(self.url, {'action': 'collect'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'No approved request found for this book.')

    def test_post_collect_book_success(self):
        self.authenticate()

        borrow_request = BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.APPROVED,
            request_date=timezone.now()
        )

        response = self.client.post(self.url, {'action': 'collect'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Book collected successfully.')

        borrow_request.refresh_from_db()
        self.assertEqual(borrow_request.status, BorrowRequest.COLLECTED)

    def test_post_invalid_action(self):
        self.authenticate()

        response = self.client.post(self.url, {'action': 'invalid_action'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Invalid action.')


class BorrowRequestViewSetTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.staff_user = User.objects.create_user(username='staffuser', password='password123', is_staff=True)
        self.user_token = Token.objects.create(user=self.user)
        self.staff_token = Token.objects.create(user=self.staff_user)

        # Create a book instance
        self.book = Book.objects.create(
            title='Test Book',
            summary='This is a test summary for the book.',
            isbn='1234567890123',
            available=True,
            published_date='2023-01-01',
            publisher='Test Publisher'
        )

        self.url_list = reverse('borrowrequest-list')
        self.url_detail = lambda pk: reverse('borrowrequest-detail', kwargs={'pk': pk})

    def authenticate(self, user):
        """Helper method to set up token authentication for a user."""
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_create_borrow_request_authenticated(self):
        self.authenticate(self.user)

        response = self.client.post(self.url_list, {'book': self.book.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['book'], self.book.id)
        self.assertEqual(response.data['borrower'], self.user.id)

        self.assertTrue(BorrowRequest.objects.filter(book=self.book, borrower=self.user).exists())

    def test_create_borrow_request_unauthenticated(self):
        response = self.client.post(self.url_list, {'book': self.book.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_borrow_requests_authenticated_user(self):
        self.authenticate(self.user)

        BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )

        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['borrower'], self.user.id)

    def test_get_borrow_requests_authenticated_staff(self):
        self.authenticate(self.staff_user)

        BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )
        BorrowRequest.objects.create(
            book=self.book,
            borrower=self.staff_user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )

        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_borrow_request_approve(self):
        self.authenticate(self.staff_user)

        borrow_request = BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )

        response = self.client.put(self.url_detail(borrow_request.id),
                                   {'action': 'approve', 'due_date': '2024-01-01'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], BorrowRequest.APPROVED)

        self.book.refresh_from_db()
        self.assertFalse(self.book.available)

    def test_update_borrow_request_collect(self):
        self.authenticate(self.staff_user)

        borrow_request = BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.APPROVED,
            request_date=timezone.now()
        )

        response = self.client.put(self.url_detail(borrow_request.id), {'action': 'collect'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], BorrowRequest.COLLECTED)

    def test_update_borrow_request_complete(self):
        self.authenticate(self.staff_user)

        borrow_request = BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.COLLECTED,
            request_date=timezone.now()
        )

        response = self.client.put(self.url_detail(borrow_request.id), {'action': 'complete'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], BorrowRequest.COMPLETE)

        self.book.refresh_from_db()
        self.assertTrue(self.book.available)

    def test_update_borrow_request_decline(self):
        self.authenticate(self.staff_user)

        borrow_request = BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )

        response = self.client.put(self.url_detail(borrow_request.id), {'action': 'decline'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], BorrowRequest.DECLINED)

    def test_update_borrow_request_invalid_action(self):
        self.authenticate(self.staff_user)

        borrow_request = BorrowRequest.objects.create(
            book=self.book,
            borrower=self.user,
            status=BorrowRequest.PENDING,
            request_date=timezone.now()
        )

        response = self.client.put(self.url_detail(borrow_request.id), {'action': 'invalid_action'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
