from django.urls import path

from .views import UserLoginView, RegisterView, HomePageView, UserLogoutView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]