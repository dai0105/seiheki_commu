from django.shortcuts import render, redirect, get_object_or_404
import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
import uuid
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, ProfileForm, ContactForm
from .models import Profile
from community_app.models import Post, Room, Category, RoomMember
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.mail import send_mail
from .models import Contact
from django.contrib.auth.hashers import make_password
import boto3


stripe.api_key = settings.STRIPE_SECRET_KEY


def gender_select(request):
    print("METHOD:", request.method)
    if request.method == 'POST':
        gender = request.POST.get('gender')
        request.session['gender'] = gender
        return redirect('register')
    return render(request, 'accounts/gender_select.html')





# -------------------------
# ここから Stripe 決済用の処理
# -------------------------



def create_checkout_session(request):
    success_url = request.build_absolute_uri(
        reverse('payment_success')
    ) + '?session_id={CHECKOUT_SESSION_ID}'

    cancel_url = request.build_absolute_uri(
        reverse('payment_cancel')
    )

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': settings.STRIPE_PRICE_ID,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return redirect(session.url, code=303)


def payment_success(request):
    session_id = request.GET.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)

    customer_id = session.customer

    user = request.user
    profile = user.profile

    # Stripe Customer ID を保存
    profile.stripe_customer_id = customer_id

    # 新規登録の男性だけ gender をセット
    if not profile.gender:
        profile.gender = 'male'

    profile.save()

    # ここから分岐
    # プロフィール未設定なら setup へ
    if not profile.nickname or not profile.age_range:
        return redirect('/accounts/profile/setup/')

    # すでにプロフィールがある人は普通にログイン後の画面へ
    return redirect('room_list')




def payment_cancel(request):
    return render(request, 'accounts/payment_cancel.html')



def register(request):
    print("REGISTER VIEW CALLED")
    print("SESSION:", dict(request.session))
    print("GENDER:", request.session.get('gender'))

    if request.method == 'POST':
        # 年齢確認チェック（ここが追加部分）
        if not request.POST.get("age_confirm"):
            form = CustomUserCreationForm(request.POST)
            form.add_error(None, "18歳未満の方はご利用いただけません。")
            return render(request, 'accounts/register.html', {'form': form})

        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # login() の前に gender を退避
            gender = request.session.get('gender')

            user = form.save()
            login(request, user)

            profile, created = Profile.objects.get_or_create(user=user)
            profile.gender = gender
            profile.save()

            if gender == 'male':
                return redirect('payment_start')
            return redirect('/accounts/profile/setup/')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def payment_start(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'accounts/payment_start.html')


def profile_setup(request):
    profile = request.user.profile

    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        age_range = request.POST.get('age_range')

        # 必須チェック
        if not nickname or not age_range:
            return render(request, 'accounts/profile_setup.html', {
                'error': 'ニックネームと年齢は必須です。',
            })

        profile.nickname = nickname
        profile.age_range = age_range
        profile.save()

        return redirect(reverse('room_list'))

    return render(request, 'accounts/profile_setup.html')


stripe.api_key = settings.STRIPE_SECRET_KEY


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            profile = user.profile

            # ① 男性で決済していない（stripe_customer_id が無い）→ ログイン不可
            if profile.gender == "male" and not profile.stripe_customer_id:
                return render(request, 'accounts/login.html', {
                    'subscription_expired': True
                })

            # ② Stripe のサブスク状態チェック（男性のみ）
            if profile.gender == "male" and profile.stripe_customer_id:
                subscriptions = stripe.Subscription.list(
                    customer=profile.stripe_customer_id,
                    limit=1
                )

                if subscriptions.data:
                    sub = subscriptions.data[0]

                    # active 以外はログインさせない
                    if sub.status != "active":
                        return render(request, 'accounts/login.html', {
                            'subscription_expired': True
                        })

            # ③ ここまで来たらログインOK
            login(request, user)
            next_url = request.GET.get('next') or reverse('room_list')
            return redirect(next_url)

        else:
            # 認証失敗（パスワード間違い）
            return render(request, 'accounts/login.html', {
                'error': 'ユーザー名またはパスワードが違います。',
            })

    return render(request, 'accounts/login.html')



def profile_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    profile = user_obj.profile

    # 投稿一覧を取得
    posts = Post.objects.filter(user=user_obj).order_by('-created_at')

    return render(request, 'accounts/profile.html', {
        'user_obj': user_obj,
        'profile': profile,
        'posts': posts,
    })



@login_required
def profile_edit(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            icon_file = request.FILES.get("icon")

            # 画像がアップロードされた場合だけ R2 に保存
            if icon_file:
                s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name="auto",
                )

                filename = f"profile_icons/{uuid.uuid4()}_{icon_file.name}"

                try:
                    s3.upload_fileobj(
                        icon_file,
                        settings.AWS_STORAGE_BUCKET_NAME,
                        filename,
                        ExtraArgs={"ContentType": icon_file.content_type or "image/jpeg"},
                    )
                    # R2 の URL をフォームの保存対象にする
                    form.instance.icon = f"{settings.R2_BASE_URL}/{filename}"
                except Exception as e:
                    print("UPLOAD ERROR:", e)

            form.save()
            return redirect('profile', user_id=request.user.id)

    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def billing_portal(request):
    # Stripe の Customer ID をユーザーの Profile から取得
    customer_id = request.user.profile.stripe_customer_id

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=request.build_absolute_uri('/accounts/profile/')
    )

    return redirect(session.url)

@login_required
def cancel_subscription(request):
    customer_id = request.user.profile.stripe_customer_id

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=request.build_absolute_uri('/accounts/profile/'),
    )

    return redirect(session.url)

@login_required
def account_delete_confirm(request):
    return render(request, 'accounts/account_delete_confirm.html')




stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def account_delete(request):
    if request.method == "POST":
        user = request.user
        profile = user.profile

        # Stripe のサブスクをキャンセル
        if profile.stripe_customer_id:
            try:
                # customer に紐づく active な subscription を取得
                subscriptions = stripe.Subscription.list(
                    customer=profile.stripe_customer_id,
                    status="active"
                )

                # active なサブスクがあればキャンセル
                for sub in subscriptions.data:
                    stripe.Subscription.delete(sub.id)

            except Exception as e:
                print("Stripe cancel error:", e)

        # Django のユーザー削除
        user.delete()

        return redirect('login')  # 削除後はログイン画面へ

    return redirect('account_delete_confirm')



def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            Contact.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message']
            )
            return redirect('contact_done')
    else:
        form = ContactForm()

    return render(request, 'accounts/contact.html', {'form': form})

def contact_done(request):
    return render(request, 'accounts/contact_done.html')




def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(username=email)
            return redirect("password_reset_confirm", user_id=user.id)
        except User.DoesNotExist:
            return render(request, "accounts/password_reset_request.html", {
                "error": "このメールアドレスは登録されていません。"
            })

    return render(request, "accounts/password_reset_request.html")

def password_reset_confirm(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == "POST":
        new_password = request.POST.get("password")
        user.password = make_password(new_password)
        user.save()
        return redirect("password_reset_done")

    return render(request, "accounts/password_reset_confirm.html", {"user": user})

def password_reset_done(request):
    return render(request, "accounts/password_reset_done.html")

def terms(request):
    return render(request, "accounts/terms.html")