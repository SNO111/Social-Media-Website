from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib import messages
from .models import Profile, FriendRequest
from feed.models import Post
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
import random

# Create your views here.

# users_list — This view will form the user list to be recommended to any user to help them discover new users to make friends with
# first adding our friend’s friends who are not our friends.
# Then if our user list has still low members, we will add random people to recommend (mostly for a user with no friends).

User = get_user_model()

@login_required
def users_list(request):
    users = Profile.objects.exclude(user=request.user)
    sent_friend_requests = FriendRequest.objects.filter(from_user=request.user)
    sent_to = []
    friends = []
    for user in users:
            friend = user.friends.all()
            for f in friend:
                if f in friends:
                    friend = friend.exclude(user=f.user)

            friends+=friend
    my_friends = request.user.profile.friends.all()
    for i in my_friends:
            if i in friends:
                friends.remove(i)
    if request.user.profile in friends:
            friends.remove(request.user.profile)
    random_list = random.sample(list(users), min(len(list(users)), 10))
    for r in random_list:
            if r in friends:
                random_list.remove(r)
    friends+=random_list
    for i in my_friends:
            if i in friends:
                friends.remove(i)
    for se in sent_friend_requests:
            sent_to.append(se.to_user)
    context = {
            'users': friends,
            'sent': sent_to
    }
    
    return render(request, "users/users_list.html", context)

# Friend_list — This view will display all the friends of the user.
def friend_list(request):
    p = request.user.profile
    friends = p.friends.all()
    context = {
        'friends': friends
    }
    return render(request, "users/friend_list.html", context)

# Send_friend_request — This will help us create a friend request instance and will send a request to the user.
@login_required
def send_friend_request(request, id):
        user = get_object_or_404(User, id=id)
        frequest, created  = FriendRequest.objects.get_or_create(
                from_user = request.user,
                to_user = request.user)
        return HttpResponseRedirect('/users/{}'.format(user.profile.slug))

# Cancel_friend_request — It will cancel the friend request we sent to the user.
@login_required
def cancel_friend_request(request, id):
        user = get_object_or_404(User, id=id)
        frequest = FriendRequest.objects.filter(
                from_user=request.user,
                to_user=user).first()

        frequest.delete()
        return HttpResponseRedirect('/users/{}'.format(user.profile.slug))


# Accept_friend_request — It will be used to accept the friend request of the user and we add user1 to user2’s friend list and vice versa. Also, we will delete the friend request.
@login_required
def accept_friend_request(request, id):
        from_user = get_object_or_404(User, id=id)
        frequest = FriendRequest.objects.filter(from_user=from_user, to_user=request.user).first()
        user1 = frequest.to_user
        user2 = from_user
        user1.profile.friends.add(user2.profile)
        user2.profile.friends.add(user1.profile)
        if(FriendRequest.objects.filter(from_user=request.user, to_user=from_user).first()):
                request_rev = FriendRequest.objects.filter(from_user=request.user, to_user=from_user).first()
                request_rev.delete()

        frequest.delete()
        return HttpResponseRedirect('/users/{}'.format(request.user.profile.slug))

# Delete_friend_request — It will allow the user to delete any friend request he/she has received.
@login_required
def delete_friend_request(request, id):
        from_user = get_object_or_404(User, id=id)
        frequest = FriendRequest.objects.filter(from_user=from_user, to_user=request.user).first()
        frequest.delete()

        return HttpResponseRedirect('/users/{}'.format(request.user.profile.slug))

# Delete_friend — This will delete the friend of that user i.e. we would remove user1 from user2 friend list and vice versa.
@login_required
def delete_friend(request, id):
        user_profile = request.user.profile
        friend_profile = get_object_or_404(Profile, id=id)
        user_profile.friends.remove(friend_profile)
        friend_profile.friends.remove(user_profile)
        return HttpResponseRedirect('/users/{}'.format(friend_profile.slug))

# Profile_view — This will be the profile view of any user. It will showcase the friend's count and posts count of the user and their friend list. Also, it would showcase the friend request received and sent by the user and can accept, decline or cancel the request>
@login_required
def profile_view(request, slug):
        p = Profile.objects.filter(slug=slug).first()
        u = p.user
        sent_friend_requests = FriendRequest.objects.filter(from_user=p.user)
        rec_friend_requests = FriendRequest.objects.filter(to_user=p.user)
        user_posts = Post.objects.filter(user_name=u)

        freinds = p.friends.all()

        # is this user our friend
        button_status = 'more'
        if p not in request.user.profile.friends.all():
                button_status = 'not_friend'

                # if we have sent a friend request
                if len(FriendRequest.objects.filter(
                        from_user=request.user).filter(to_user=p.user)) == 1:
                        button_status = 'friend_request_sent'

                # if we have received a friend request
                if len(FriendRequest.objects.filter(
                        from_user=p.user).filter(to_user=request.user)) == 1:
                        button_status = 'friend_request_received'
                        
        context = {
                'u': u,
                'button_status': button_status,
                'friend_list': freinds,
                'sent_friend_requests': sent_friend_requests,
                'rec_friend_requests': rec_friend_requests,
                'post_count': user_posts.count
        }
        return render(request, "users/profile.html", context)

# Register — This will let users register on our website. It will render the registration form we created in forms.py file.
def register(request):
        if request.method == 'POST':
                form = UserRegisterForm(request.POST)
                if form.is_valid():
                        form.save()
                        username = form.cleaned_data.get('username')
                        messages.success(request, f"Your account has been created! You can now login!")
                        return redirect('login')
        else:
                form = UserRegisterForm()
        return render(request, "users/register.html/", {'form':form})

# edit_profile — This will let the users edit their profile with help of the forms we created.
@login_required
def edit_profile(request):
        if request.method == 'POST':
                u_form = UserUpdateForm(request.POST, instance=request.user)
                p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
                if u_form.is_valid() and p_form.is_valid():
                        u_form.save()
                        p_form.save()
                        messages.success(request, f"Your account has been updated")
                        return redirect('my_profile')
        else:
                u_form = UserUpdateForm(instance=request.user)
                p_form = ProfileUpdateForm(instance=request.user.profile)
        
        context = {
                'u_form': u_form,
                'p_form': p_form,
        }
        return render(request, 'users/edit_profile.html', context)

# my_profile — This is same as profile_view but it will render your profile only.
@login_required
def my_profile(request):
        p = request.user.profile
        you = p.user
        sent_friend_requests = FriendRequest.objects.filter(from_user=you)
        rec_friend_requests = FriendRequest.objects.filter(to_user=you)
        user_posts = Post.objects.filter(user_name=you)
        friends = p.friends.all()

        # is this our friend
        button_status = 'more'
        if p not in request.user.profile.friends.all():
                button_status = 'not_friend'

                 # if we have sent a friend request
                if len(FriendRequest.objects.filter(
                        from_user=request.user).filter(to_user=you)) == 1:
                        button_status = 'friend_request_sent'

                # if we have received a friend request
                if len(FriendRequest.objects.filter(
                        from_user=p.user).filter(to_user=request.user)) == 1:
                        button_status = 'friend_request_received'
                        
        context = {
                'u': you,
                'button_status': button_status,
                'friend_list': friends,
                'sent_friend_requests': sent_friend_requests,
                'rec_friend_requests': rec_friend_requests,
                'post_count': user_posts.count
        }

        return render(request, "users/profile.html", context)

# Search_users — This will handle the search function of the users. It takes in the query and then filters out relevant users.
@login_required
def search_users(request):
        query = request.GET.get('q')
        object_list = User.objects.filter(username__icontains=query)

        context = {
                'users': object_list
        }
        return render(request, "users/search_users.html", context)