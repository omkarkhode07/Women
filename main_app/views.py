from django.shortcuts import render, redirect
from django.contrib.auth.forms import (
    PasswordChangeForm,
)
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from .forms import ContactForm
from django.conf import settings
from .models import contact, EmergencyProfile
from django.contrib.auth.models import User, auth
from .mail import send_email
from .whatsapp import send_whatsapp
from .location import lat, log
from .forms import UserCreateForm, LoginForm
from django.core.mail import EmailMessage, send_mail
from django.views import View
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import account_activation_token
from django.http import JsonResponse
import hashlib

# Create your views here


def home(request):
    context = {}
    return render(request, "main_app/home.html", context)


def register(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")  # noqa
        password2 = request.POST.get("password2")  # noqa
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            family_numbers = form.cleaned_data.get("family_mobile_numbers", "")
            user.is_active = False
            user.save()

            emergency_count = form.cleaned_data.get("emergency_contact_count", 5)
            emergency_profile, _ = EmergencyProfile.objects.get_or_create(user=user)
            emergency_profile.emergency_contact_count = emergency_count
            emergency_profile.family_mobile_numbers = family_numbers
            emergency_profile.save()

            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            link = reverse(
                "main_app:activate",
                kwargs={
                    "uidb64": uidb64,
                    "token": account_activation_token.make_token(user),
                },
            )

            activate_url = "http://" + domain + link

            email_subject = "Rescue - Activate you Account!"
            email_body = (
                "Hi  "
                + user.username  # noqa
                + "  ,  Please use this link to verify your account\n"  # noqa
                + activate_url  # noqa
            )
            email = EmailMessage(
                email_subject,
                email_body,
                "noreply@gmail.com",
                [email],
            )
            messages.success(request, f"New Account Created Successfully: {username}")
            messages.success(request, "Check your email to Activate your account!")
            email.send(fail_silently=False)

            response = redirect('main_app:email_sent')
            response.set_cookie("username", username, max_age=30 * 24 * 60 * 60)
            response.set_cookie("family_mobile_numbers", family_numbers, max_age=30 * 24 * 60 * 60)
            response.set_cookie(
                "password_hash",
                hashlib.sha256(password1.encode("utf-8")).hexdigest(),
                max_age=30 * 24 * 60 * 60,
            )
            return response
        elif User.objects.filter(username=username).exists():
            messages.warning(
                request,
                "The username you entered has already been taken. Please try another username",
            )
        elif User.objects.filter(email=email).exists():
            messages.warning(
                request,
                "The Email you entered has already been taken. Please try another Email",
            )
        else:
            for msg in form.error_messages:
                messages.warning(request, f"{form.error_messages[msg]}")

    else:
        form = UserCreateForm()
    return render(request, "main_app/register.html", {"form": form})


class VerificationView(View):
    def get(self, request, uidb64, token):
        try:
            id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=id)

            if not account_activation_token.check_token(user, token):
                return redirect(
                    "main_app:login" + "?message=" + "User already activated"
                )

            if user.is_active:
                return redirect("main_app:login")
            user.is_active = True
            user.save()

            messages.success(request, "Account activated successfully")
            return redirect("main_app:login")

        except Exception:
            pass

        return redirect("main_app:login")


def logout_request(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("main_app:home")


def delete_account(request, username):
    try:
        user = User.objects.get(username=username)
        user.delete()
        messages.success(
            request, user.username + ", Your account is deleted successfully!"
        )

    except User.DoesNotExist:
        messages.error(request, "User doesnot exist")

    return redirect("main_app:home")


def login_request(request):
    form = LoginForm(request.POST)
    username = request.POST.get("Username_or_Email")
    password = request.POST.get("password")
    if request.method == "POST":
        if username and password:
            if User.objects.filter(username=username).exists():
                user = auth.authenticate(username=username, password=password)
                if user:
                    if user.is_active:
                        login(request, user)
                        messages.success(
                            request,
                            "Welcome, " + user.username + " you are now logged in",
                        )
                        response = redirect("main_app:home")
                        response.set_cookie("username", user.username, max_age=30 * 24 * 60 * 60)
                        emergency_profile = getattr(user, "emergency_profile", None)
                        family_numbers = (
                            emergency_profile.family_mobile_numbers if emergency_profile else ""
                        )
                        response.set_cookie("family_mobile_numbers", family_numbers, max_age=30 * 24 * 60 * 60)
                        response.set_cookie(
                            "password_hash",
                            hashlib.sha256(password.encode("utf-8")).hexdigest(),
                            max_age=30 * 24 * 60 * 60,
                        )
                        return response

                messages.error(
                    request, "Account is not active,please check your email"
                )

            elif User.objects.filter(email=username).exists():
                user = User.objects.get(email=username)
                user = auth.authenticate(username=user.username, password=password)
                if user:
                    if user.is_active:
                        login(request, user)
                        messages.success(
                            request,
                            "Welcome, " + user.username + " you are now logged in",
                        )
                        response = redirect("main_app:home")
                        response.set_cookie("username", user.username, max_age=30 * 24 * 60 * 60)
                        emergency_profile = getattr(user, "emergency_profile", None)
                        family_numbers = ""
                        if emergency_profile is not None:
                            family_numbers = emergency_profile.family_mobile_numbers or ""
                        response.set_cookie("family_mobile_numbers", family_numbers, max_age=30 * 24 * 60 * 60)
                        response.set_cookie(
                            "password_hash",
                            hashlib.sha256(password.encode("utf-8")).hexdigest(),
                            max_age=30 * 24 * 60 * 60,
                        )
                        return response

                messages.error(
                    request, "Account is not active,please check your email"
                )

            else:
                messages.error(request, "Invalid username or password")
                return redirect("main_app:login")

    form = LoginForm()
    return render(request, "main_app/login.html", {"form": form})


def emergency_contact(request):
    if not request.user.is_authenticated:
        return redirect("main_app:login")
    contacts = contact.objects.filter(user=request.user)
    total_contacts = contacts.count()
    context = {
        "contacts": contacts,
        "total_contacts": total_contacts,
        "user": request.user,
    }
    return render(request, "main_app/emergency_contact.html", context)


def create_contact(request):
    inst = contact(user=request.user)
    form = ContactForm(instance=inst)
    if request.method == "POST":
        form = ContactForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            messages.info(request, "New contact created successfully!!")
            messages.info(request, "An email has been sent to your contact!!")
            return redirect("main_app:emergency_contact")
        messages.error(request, "Invalid username or password")

    return render(request, "main_app/create_contact.html", {"form": form})


def update_contact(request, pk):
    curr_contact = contact.objects.get(id=pk)
    name = curr_contact.name
    form = ContactForm(
        initial={
            "name": name,
            "email": curr_contact.email,
            "mobile_no": curr_contact.mobile_no,
            "relation": curr_contact.relation,
        }
    )
    if request.method == "POST":
        form = ContactForm(request.POST, instance=curr_contact)
        if form.is_valid():
            form.save()
            messages.error(request, f"{name} updated successfully!!")
            messages.info(request, "A message has been sent to your contact!!")
            return redirect("main_app:emergency_contact")
    context = {"form": form}
    return render(request, "main_app/create_contact.html", context)


def delete_contact(request, pk):
    curr_contact = contact.objects.get(id=pk)
    name = curr_contact.name
    if request.method == "POST":
        curr_contact.delete()
        messages.error(request, f"{name} deleted successfully!!")
        return redirect("main_app:emergency_contact")
    context = {"item": curr_contact}
    return render(request, "main_app/delete_contact.html", context)


def emergency(request):
    if not request.user.is_authenticated:
        return redirect("main_app:login")

    emergency_profile = getattr(request.user, "emergency_profile", None)
    max_contacts = 5
    if emergency_profile is not None:
        max_contacts = emergency_profile.emergency_contact_count

    contacts = contact.objects.filter(user=request.user)[:max_contacts]
    total_contacts = contacts.count()
    context = {
        "contacts": contacts,
        "total_contacts": total_contacts,
        "user": request.user,
    }

    latitude = request.GET.get("lat") or request.GET.get("latitude") or lat
    longitude = request.GET.get("lon") or request.GET.get("longitude") or log
    link = f"https://www.google.com/maps?q={latitude},{longitude}"

    mobile_numbers = []
    for c in contacts:
        mobile_numbers.append(str(c.mobile_no).replace(" ", ""))
        send_email(request.user.username, c.email, link)
        messages.success(request, f"Email delivered to {c.name} at {c.email}")

    try:
        if mobile_numbers:
            send_whatsapp(mobile_numbers, request.user.username, link)
            messages.success(request, f"Emergency message sent to {len(mobile_numbers)} trusted contacts")
    except Exception:  # noqa
        messages.error(
            request, "Your contact numbers may be missing the country code or may be invalid."
        )

    if not contacts:
        messages.warning(request, "Add at least one trusted contact before using the emergency button.")

    return render(request, "main_app/emergency_contact.html", context)


def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Your password was successfully updated!")
            return redirect("main_app:home")
        else:
            for msg in form.error_messages:
                messages.error(request, f"{form.error_messages[msg]}")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "main_app/change_password.html", {"form": form})


def helpline_numbers(request):
    return render(
        request, "main_app/helpline_numbers.html", {"title": "helpline_numbers"}
    )


def ngo_details(request):
    return render(request, "main_app/ngo_details.html", {"title": "ngo_details"})


def gallery(request):
    return render(request, "main_app/gallery.html", {"title": "Gallery"})


def FAQ(request):
    return render(request, "main_app/FAQ.html", {"title": "FAQ"})


def women_laws(request):
    return render(request, "main_app/women_laws.html", {"title": "women_laws"})


def developers(request):
    return render(request, "main_app/developers.html", {"title": "developers"})


def women_rights(request):
    return render(request, "main_app/women_rights.html", {"title": "women_rights"})


def page_not_found(request, exception):
    return render(request, "main_app/404.html")


def check_username(request):
    username = request.GET.get("name")
    if User.objects.filter(username=username).exists():
        return JsonResponse({"exists": "yes"})
    return JsonResponse({"exists": "no"})


def check_email(request):
    email = request.GET.get("email")
    if User.objects.filter(email=email).exists():
        return JsonResponse({"exists": "yes"})
    return JsonResponse({"exists": "no"})


def email_sent(request):
    return render(request, "main_app/email_sent.html")


def contact_user(request):
    if request.method == "POST":
        message_name = request.POST.get("message-name", "")
        message_email = request.POST.get("message-email", "")
        message = request.POST.get("message", "")

        try:
            send_mail(
                f"Rescue Contact: {message_name}",
                f"From: {message_email}\n\nMessage:\n{message}",
                settings.DEFAULT_FROM_EMAIL,
                ["rescue@gmail.com"],
                fail_silently=True,
            )
        except Exception:
            pass

        return render(
            request, "main_app/contact_user.html", {"message_name": message_name}
        )

    return render(request, "main_app/contact_user.html", {})
