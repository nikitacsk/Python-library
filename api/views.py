from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import RegisterSerializer


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
