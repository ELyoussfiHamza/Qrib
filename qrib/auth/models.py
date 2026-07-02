"""Authentication models."""

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager for phone-number based users."""

    def create_user(self, phone_number, password=None, **extra_fields):
        """Creates and saves a user with the given phone number."""
        if not phone_number:
            raise ValueError("The phone number must be set.")

        user = self.model(
            phone_number=self.normalize_phone_number(phone_number),
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        """Creates and saves a superuser with the given phone number."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)

    @staticmethod
    def normalize_phone_number(phone_number):
        """Normalizes phone numbers for storage."""
        return phone_number.strip().replace(" ", "")


class User(AbstractBaseUser, PermissionsMixin):
    """Application user authenticated primarily by phone number."""

    phone_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    profile_completed = models.BooleanField(default=False)
    otp_code_hash = models.CharField(max_length=128, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    otp_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.phone_number

    def set_otp_code(self, code, expires_at):
        """Stores a hashed OTP code and its expiry."""
        self.otp_code_hash = make_password(code)
        self.otp_expires_at = expires_at

    def verify_otp_code(self, code):
        """Returns whether the supplied OTP is valid and unexpired."""
        if not self.otp_code_hash or not self.otp_expires_at:
            return False
        if timezone.now() > self.otp_expires_at:
            return False
        return check_password(code, self.otp_code_hash)

    def mark_otp_verified(self):
        """Marks OTP verification and clears the stored OTP challenge."""
        self.otp_verified_at = timezone.now()
        self.otp_code_hash = ""
        self.otp_expires_at = None
