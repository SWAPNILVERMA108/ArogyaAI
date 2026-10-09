from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .models import User


class AccountService:
    @staticmethod
    def register_user(validated_data):
        return User.objects.create_user(
            name=validated_data["name"],
            email=validated_data["email"],
            phone=validated_data.get("phone", ""),
            password=validated_data["password"],
            role=User.Role.PATIENT,
        )

    @staticmethod
    def issue_tokens(user):
        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    @staticmethod
    def update_profile(user, validated_data):
        for field, value in validated_data.items():
            setattr(user, field, value)
        user.save(update_fields=[*validated_data.keys(), "updated_at"])
        return user

    @staticmethod
    def revoke_refresh_token(refresh_token):
        token = RefreshToken(refresh_token)
        token.blacklist()

    @staticmethod
    def refresh_tokens(refresh_token):
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
