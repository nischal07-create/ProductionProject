from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()
def landing_page(request):
    return render(request, "core/landing.html")


def user_portal(request):
    return render(request, "core/index.html")

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return JsonResponse({"status": "ok"})

@api_view(["GET"])
@permission_classes([AllowAny])
def home(request):
    return JsonResponse({"message": "Welcome to TrailMate API"})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Register a new user with username and password."""
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "").strip()
    password_confirm = request.data.get("password_confirm", "").strip()
    
    # Validation
    if not username or not password or not password_confirm:
        return Response(
            {"error": "Username and passwords are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(username) < 3:
        return Response(
            {"error": "Username must be at least 3 characters"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(password) < 6:
        return Response(
            {"error": "Password must be at least 6 characters"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if password != password_confirm:
        return Response(
            {"error": "Passwords do not match"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    try:
        user = User.objects.create_user(username=username, password=password)
        return Response(
            {
                "message": "User registered successfully",
                "user_id": user.id,
                "username": user.username
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )