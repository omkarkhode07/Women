from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


class EmergencyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="emergency_profile")
    emergency_contact_count = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    family_mobile_numbers = models.TextField(default="", blank=True)
    share_live_location = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s emergency contacts: {self.emergency_contact_count}"


# Create your models here.
class contact(models.Model):

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="contact", null=True
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile_no = models.CharField(max_length=15)
    Father = "Father"
    Mother = "Mother"
    Brother = "Brother"
    Sister = "Sister"
    Husband = "Husband"
    Friend = "Friend"
    Relative = "Relative"
    Other = "Other"
    relations = (
        (Father, "Father"),
        (Mother, "Mother"),
        (Brother, "Brother"),
        (Sister, "Sister"),
        (Husband, "Husband"),
        (Friend, "Friend"),
        (Relative, "Relative"),
        (Other, "Other"),
    )
    relation = models.CharField(max_length=10, choices=relations, default=Other)

    def __str__(self):
        return self.name


class Login(models.Model):

    Username_or_Email = models.CharField(max_length=100)
    password = models.CharField(max_length=32)
