from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .forms import NewCommentForm, NewPostForm
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Post, Cooments, Like
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

# Create your views here.

# PostListView — This view handles the display of all the posts in an order which puts newer posts first up. 
# Each page displays 10 posts and then we need to move to the next page to view more. 
class PostListView(ListView):
    model = Post
    template_name = 'feed/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginte_by = 10
    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            liked = [i for i in Post.objects.all() if Like.objects.filter(user= self.request.user, post=i)]
            context['liked_post'] = liked

        return context

# UserPostListView — This view is almost similar to the PostListView. Ordering and pagination are the same. 
# The only difference is that this page shows the posts by a certain user only.
class UserPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'feed/user_posts.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginte_by = 10

    def get_context_data(self, **kwargs):
        context = super(UserPostListView, self).get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        liked = [i for i in Post.objects.filter(user_name=user) if Like.objects.filter(user= self.request.user, post=i)]
        context['liked_post'] = liked

        return context

# post_detail — This view handles the display of a single post. 
# It also displays the comment form and lets a user comment on the post and also displays all the comments. It also shows like count and allows you to like or unlike
@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    user = request.user
    is_liked = Like.objects.filter(user=user, post=post)
    if request.method == 'POST':
            form = NewCommentForm(request.POST)
            if form.is_valid():
                    data = form.save(commit=False)
                    data.post = post
                    data.username = user
                    data.save()
                    return redirect('post-detail', pk=pk)

    else:
            form = NewCommentForm()
    return render(request, 'feed/post_detail.html', {'post':post, 'is_liked':is_liked, 'form':form})

# create_post — This view handles the creation of a new post. It saves the data and adds the current user as the user_name and commits it.
@login_required
def create_post(request):
        user = request.user
        if request.method == "POST":
                form = NewPostForm(request.POST, request.FILES)
                if form.is_valid():
                        data = form.save(commit=False)
                        data.user_name = user
                        data.save()
                        messages.success(request, f'Posted Successfuly')
                        return redirect('home')

        else:
                form = NewPostForm()
        return render(request, 'feed/create_post.html', {'form':form})


# PostUpdateView — This view handles the updating of the post. 
# We can edit our posts with the help of this view.
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['description', 'pic', 'tags']
    template_name = 'feed/create_post.html'

    def form_valid(self, form):
            form.instance.user_name = self.request.user
            return super().form_valid(form)

    def test_func(self):
            post = self.get_object()
            if self.request.user == post.user_name:
                   return True
            return False

# post_delete — This view handles the deletion of posts. It deletes the post when the user wants to.
@login_required 
def post_delete(request, pk):
        post = Post.objects.get(pk=pk)
        if request.user == post.user_name:
                Post.objects.get(pk=pk).delete()
        return redirect('home')

# search_posts — This works in a similar fashion to search_users which we did in the Users app backend (User). 
# It takes in the input and searches for posts considering the tags.
@login_required
def search_posts(request):
        query = request.GET.get('p')
        object_list = Post.objects.filter(tags__icontains=query)
        liked = [i for i in object_list if Like.objects.filter(user=request.user, post=i)]
        context = {
            'posts':object_list,
            'liked_post': liked
        }
        return render(request, 'feed/search_posts.html', context)

# ike — This view handles the like event for the posts. It is done with the help of AJAX requests so that the page does not refresh each time a user likes or unlikes. 
# It works in a way that if the post is already liked by the user, clicking on the like button would remove the like but if it is not already liked, 
# it will like the post. Then it dumps the response as JSON and passes it as an HTTP response.
@login_required
def like(request):
        post_id = request.GET.get("likeId", "")
        user = request.user
        post = Post.objects.get(pk=post_id)
        liked = False
        like = Like.objects.filter(user=user, post=post)
        if like:
                like.delete()
        else:
                liked = True
                Like.objects.create(user=user, post=post)
        resp = {
            'liked': liked
        }
        response = json.dumps(resp)
        return HttpResponse(response, content_type="application/json")