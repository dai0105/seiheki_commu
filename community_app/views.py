from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PostForm, RoomForm
from .models import Post, Room, Category, Message, RoomMember, DMRoom, DMMessage, Block
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse
import boto3
import uuid
from django.conf import settings


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)  # ← image/video は form で扱わない
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user

            # boto3 クライアント
            s3 = boto3.client(
                "s3",
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name="auto",
            )

            # 画像アップロード
            if "image" in request.FILES:
                file = request.FILES["image"]
                filename = f"post_images/{uuid.uuid4()}_{file.name}"

                s3.upload_fileobj(
                    file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    filename,
                    ExtraArgs={"ContentType": file.content_type},
                )

                post.image = str(
                    f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{filename}"
                )

            # 動画アップロード
            if "video" in request.FILES:
                file = request.FILES["video"]
                filename = f"post_videos/{uuid.uuid4()}_{file.name}"

                s3.upload_fileobj(
                    file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    filename,
                    ExtraArgs={"ContentType": file.content_type},
                )

                post.video = str(
                    f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{filename}"
                )

            post.save()
            form.save_m2m()

            return redirect('profile', user_id=request.user.id)

    else:
        form = PostForm()

    return render(request, 'community_app/post_create.html', {'form': form})


def timeline(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'community_app/timeline.html', {'posts': posts})



@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # 投稿者本人かチェック
    if post.user != request.user:
        return redirect('timeline')  # 他人の投稿は削除不可

    post.delete()
    return redirect('timeline')

def room_list(request):
    category_id = request.GET.get('category')

    filter_type = request.GET.get('filter')

    if category_id:
        rooms = Room.objects.filter(category_id=category_id)
    else:
        rooms = Room.objects.all().order_by('-created_at')

    if filter_type == "joined":
        joined_room_ids = RoomMember.objects.filter(user=request.user).values_list('room_id', flat=True)
        rooms = rooms.filter(id__in=joined_room_ids)

    categories = Category.objects.all()

    # 入室しているかどうかを判定してまとめる
    room_status = []
    for room in rooms:
        is_member = RoomMember.objects.filter(room=room, user=request.user).exists()
        room_status.append({
            "room": room,
            "is_member": is_member,
        })

    # ★ 追加：現在入室している部屋数（5部屋制限のため）
    current_count = RoomMember.objects.filter(user=request.user).count()

    return render(request, 'community_app/room_list.html', {
        'room_status': room_status,
        'categories': categories,
        'selected_category': category_id,
        'current_count': current_count,   # ★ 追加
    })



def room_create(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            room.description = form.cleaned_data['description']  # ★これが必要
            room.save()
            RoomMember.objects.create(room=room, user=request.user)
            return redirect('room_list')
    else:
        form = RoomForm()

    return render(request, "community_app/room_create.html", {
        "form": form
    })

def room_detail(request, room_id):
    room = Room.objects.get(id=room_id)

    if request.method == "POST":
        Message.objects.create(
            room=room,
            user=request.user,
            content=request.POST.get("message"),  # ← ここを message に！
            image=request.FILES.get("image"),
            video=request.FILES.get("video"),
        )
        return redirect("room_detail", room_id=room_id)

    messages = room.messages.all().order_by("created_at")

    return render(request, "community_app/room_detail.html", {
        "room": room,
        "messages": messages,
    })



@login_required
def join_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # すでに入室している場合はスキップ
    if RoomMember.objects.filter(room=room, user=request.user).exists():
        return redirect('room_detail', room_id=room_id)

    # 5部屋までの制限
    if RoomMember.objects.filter(user=request.user).count() >= 5:
        return redirect('room_list')

    # 人数上限チェック
    if room.members.count() >= room.max_members:
        return redirect('room_list')

    # 入室
    RoomMember.objects.create(room=room, user=request.user)
    return redirect('room_detail', room_id=room_id)

@login_required
def leave_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    RoomMember.objects.filter(room=room, user=request.user).delete()
    return redirect('room_list')



@login_required
def room_delete(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # ★ 作成者以外は削除禁止
    if room.created_by != request.user:
        return redirect('room_list')

    room.delete()
    return redirect('room_list')

User = get_user_model()
@login_required
def dm_start(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if request.user == target_user:
        return redirect('profile', user_id=user_id)

    # 自分と相手の順番を固定する（重複DMを防ぐ）
    user1 = min(request.user, target_user, key=lambda u: u.id)
    user2 = max(request.user, target_user, key=lambda u: u.id)

    room, created = DMRoom.objects.get_or_create(
        user1=user1,
        user2=user2
    )

    return redirect('dm_detail', room_id=room.id)

@login_required
def dm_detail(request, room_id):
    room = get_object_or_404(DMRoom, id=room_id)

    # 自分がこのDMの当事者でなければ入れない
    if request.user not in [room.user1, room.user2]:
        return redirect('home')
    
    partner = room.get_partner(request.user)

    # ブロックチェック
    if Block.objects.filter(blocker=partner, blocked=request.user).exists():
        return HttpResponse("相手にブロックされています。")

    if Block.objects.filter(blocker=request.user, blocked=partner).exists():
        return HttpResponse("あなたはこのユーザーをブロックしています。")


    # メッセージ送信
    if request.method == "POST":
        content = request.POST.get("message", "")
        image = request.FILES.get("image")
        video = request.FILES.get("video")

        DMMessage.objects.create(
            room=room,
            sender=request.user,
            content=content,
            image=image,
            video=video
        )

        return redirect('dm_detail', room_id=room_id)

    # メッセージ一覧（正しい related_name を使う）
    messages = room.messages.all().order_by('created_at')

    return render(request, "community_app/dm_detail.html", {
        "room": room,
        "messages": messages,
    })


@login_required
def dm_list(request):
    rooms = DMRoom.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    )

    room_data = []
    for room in rooms:
        partner = room.get_partner(request.user)
        room_data.append({
            'room': room,
            'partner': partner,
        })

    return render(request, 'community_app/dm_list.html', {
        'room_data': room_data
    })

def block_user(request, user_id):
    partner = get_object_or_404(User, id=user_id)

    # ブロック登録
    Block.objects.get_or_create(
        blocker=request.user,
        blocked=partner
    )

    # DMRoom を削除（両方向に対応）
    DMRoom.objects.filter(
        Q(user1=request.user, user2=partner) |
        Q(user1=partner, user2=request.user)
    ).delete()

    return redirect('dm_list')

def qa_page(request):
    return render(request, 'community_app/qa_page.html')



@login_required
@login_required
def post_delete(request, post_id):
    print("=== DELETE VIEW CALLED ===", post_id)

    post = get_object_or_404(Post, id=post_id)

    if post.user != request.user:
        print("=== NOT OWNER ===")
        return redirect('timeline')

    print("=== DELETING ===")
    post.delete()
    return redirect('profile', user_id=request.user.id)