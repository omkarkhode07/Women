from django.forms import ModelForm
from .models import contact, Login, EmergencyProfile
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class ContactForm(ModelForm):
    class Meta:
        model = contact
        fields = ["name", "email", "mobile_no", "relation"]
        widgets = {
            "relation": forms.Select(
                choices=contact.relations, attrs={"class": "form-control"}
            ),
        }


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
        error_messages={"exists": "This Email already exists!"},
    )
    emergency_contact_count = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        initial=5,
        widget=forms.HiddenInput(),
    )
    family_mobile_numbers = forms.CharField(
        required=True,
        label="Family mobile numbers",
        help_text="Enter the mobile numbers separated by commas. Example: +919999999999, +919988888888",
        widget=forms.TextInput(attrs={"placeholder": "+919999999999, +919988888888"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "emergency_contact_count",
            "family_mobile_numbers",
        )

    def clean_family_mobile_numbers(self):
        raw_numbers = self.cleaned_data.get("family_mobile_numbers", "")
        numbers = [n.strip() for n in raw_numbers.split(",") if n.strip()]

        if not numbers:
            raise forms.ValidationError("Please enter at least one family mobile number.")

        if len(numbers) > 5:
            raise forms.ValidationError("You can add up to 5 family mobile numbers only.")

        for number in numbers:
            if not number.startswith("+"):
                raise forms.ValidationError(
                    "Each family mobile number must include the country code, for example +91..."
                )

        count = len(numbers)
        self.cleaned_data["emergency_contact_count"] = count
        return ", ".join(numbers)

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()

        numbers = [n.strip() for n in self.cleaned_data.get("family_mobile_numbers", "").split(",") if n.strip()]
        emergency_profile, _ = EmergencyProfile.objects.get_or_create(user=user)
        emergency_profile.emergency_contact_count = min(len(numbers), 5) or 1
        emergency_profile.share_live_location = True
        emergency_profile.family_mobile_numbers = ", ".join(numbers)
        emergency_profile.save()
        return user

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data["email"]).exists():
            raise forms.ValidationError(self.fields["email"].error_messages["exists"])
        return self.cleaned_data["email"]


class LoginForm(ModelForm):
    class Meta:
        model = Login
        fields = ["Username_or_Email", "password"]
        widgets = {
            "password": forms.PasswordInput,
        }
