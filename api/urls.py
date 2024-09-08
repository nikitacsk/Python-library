from django.urls import path
from .views import HomePageView, RegisterView, LoginView, LogoutView

urlpatterns = [
    path('/', HomePageView.as_view(), name='home'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
