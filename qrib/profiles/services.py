"""Business rules for worker profile completion."""

import re
from dataclasses import dataclass

from django.utils import timezone

from .models import WorkerProfile


FORBIDDEN_NAME_VALUES = {
    "casablanca",
    "rabat",
    "marrakech",
    "fes",
    "tangier",
    "agadir",
    "worker",
    "plumber",
    "electrician",
    "painter",
    "carpenter",
    "mason",
}


@dataclass(frozen=True)
class ProfileStatus:
    """Completion status for a worker profile."""

    can_complete: bool
    missing_required_fields: list[str]
    validation_errors: dict[str, str]


@dataclass(frozen=True)
class CompleteProfileResult:
    """Result from attempting to complete a worker profile."""

    completed: bool
    status: ProfileStatus
    redirect_to: str


def normalize_space(value):
    """Collapses repeated whitespace and trims a string."""
    return " ".join(value.strip().split())


def validate_full_name(value):
    """Returns an error message when a name is missing or implausible."""
    full_name = normalize_space(value)
    if not full_name:
        return "Full name is required."
    if len(full_name) < 2:
        return "Full name is too short."
    if len(full_name) > 150:
        return "Full name is too long."
    if not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", full_name):
        return "Full name must contain letters."
    if re.search(r"\d", full_name):
        return "Full name must not contain numbers."
    if full_name.lower() in FORBIDDEN_NAME_VALUES:
        return "Full name does not look like a person's name."
    return ""


def validate_location(profile):
    """Returns an error message when required location data is missing."""
    if not profile.location_permission_granted:
        return "Location permission is required."
    if profile.location_lat is None or profile.location_lng is None:
        return "Location coordinates are required."
    if not normalize_space(profile.location_city):
        return "Location city is required."
    return ""


def validate_skills_description(value):
    """Returns an error message when a skills description is insufficient."""
    description = normalize_space(value)
    if not description:
        return "Skills description is required."
    if len(description) < 10:
        return "Skills description is too short."
    if len(description.split()) < 3:
        return "Skills description needs more detail."
    return ""


def build_worker_profile_status(profile):
    """Builds profile completion status from persisted draft data."""
    validation_errors = {}
    missing_required_fields = []

    name_error = validate_full_name(profile.full_name)
    if name_error:
        validation_errors["full_name"] = name_error
        missing_required_fields.append("full_name")

    location_error = validate_location(profile)
    if location_error:
        validation_errors["location"] = location_error
        missing_required_fields.append("location")

    skills_error = validate_skills_description(profile.skills_description)
    if skills_error:
        validation_errors["skills_description"] = skills_error
        missing_required_fields.append("skills_description")

    return ProfileStatus(
        can_complete=not validation_errors,
        missing_required_fields=missing_required_fields,
        validation_errors=validation_errors,
    )


def get_worker_profile(user):
    """Returns the user's worker profile, creating a draft when needed."""
    profile, _ = WorkerProfile.objects.get_or_create(user=user)
    return profile


def complete_worker_profile(user, profile):
    """Completes a worker profile when all required fields are valid."""
    profile_status = build_worker_profile_status(profile)
    if not profile_status.can_complete:
        return CompleteProfileResult(
            completed=False,
            status=profile_status,
            redirect_to="",
        )

    user.full_name = profile.full_name
    user.profile_completed = True
    user.save(update_fields=("full_name", "profile_completed"))

    profile.completed_at = timezone.now()
    profile.save(update_fields=("completed_at", "updated_at"))

    return CompleteProfileResult(
        completed=True,
        status=profile_status,
        redirect_to="/worker/home",
    )
