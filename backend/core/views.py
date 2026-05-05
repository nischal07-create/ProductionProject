from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import JsonResponse

User = get_user_model()
def landing_page(request):
    return render(request, "core/landing.html")


def user_portal(request):
    return render(request, "core/index.html")


def operator_portal(request):
    return render(request, "core/operator.html")


def forgot_password_page(request):
    return render(request, "core/forgot_password.html")

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
    email = request.data.get("email", "").strip()
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
        user = User.objects.create_user(username=username, password=password, email=email or "")
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


@api_view(["POST"])
@permission_classes([AllowAny])
def request_password_reset(request):
    identifier = (request.data.get("identifier") or request.data.get("username") or request.data.get("email") or "").strip()

    if not identifier:
        return Response({"error": "Username or email is required"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(username__iexact=identifier).first() or User.objects.filter(email__iexact=identifier).first()
    if not user or not user.email:
        return Response({"error": "We could not find an account with a resettable email address."}, status=status.HTTP_404_NOT_FOUND)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_path = reverse("forgot-password")
    reset_link = request.build_absolute_uri(f"{reset_path}?uid={uid}&token={token}")

    subject = "TrailMate password reset"
    body = (
        f"Hello {user.username},\n\n"
        f"Use this link to reset your TrailMate password:\n{reset_link}\n\n"
        f"If you did not request this, you can ignore this message.\n"
    )
    send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@trailmate.local"), [user.email], fail_silently=True)

    return Response(
        {"message": "If the account exists, a reset link has been sent to the registered email address."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    uid = request.data.get("uid", "").strip()
    token = request.data.get("token", "").strip()
    new_password = request.data.get("new_password", "").strip()
    confirm_password = request.data.get("confirm_password", "").strip()

    if not uid or not token or not new_password or not confirm_password:
        return Response({"error": "All reset fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except Exception:
        return Response({"error": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "Reset link has expired or is invalid"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save(update_fields=["password"])
    return Response({"message": "Password reset successfully. You can now sign in."}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def session_status(request):
    """Return whether the current request has an authenticated Django session.

    This allows client-side JS to detect server-side (session) authentication
    after OAuth login flows (django-allauth) which do not set the local JWT.
    """
    user = request.user
    return JsonResponse({
        "authenticated": bool(user and user.is_authenticated),
        "username": user.username if (user and user.is_authenticated) else "",
    })