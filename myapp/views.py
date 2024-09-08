from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserRegistrationForm
from django.views.generic import TemplateView


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
