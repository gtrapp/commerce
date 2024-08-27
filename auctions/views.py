from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid

def listing(request, id):
    listing_data = Listing.objects.get(pk=id)
    in_watchlist = request.user in listing_data.watchlist.all()
    all_comments = Comment.objects.filter(listing=listing_data)
    is_owner = request.user.username == listing_data.user.username
    
    print(f"hello {is_owner}")
    
    return render(request, "auctions/listing.html", {
        "listing": listing_data,
        "in_watchlist": in_watchlist,
        "all_comments": all_comments,
        "is_owner": is_owner
    })

def close_auction(request, id):
    listing_data = Listing.objects.get(pk=id)
    in_watchlist = request.user in listing_data.watchlist.all()
    all_comments = Comment.objects.filter(listing=listing_data)
    listing_data.is_active = False
    listing_data.save()
    is_owner = request.user.username == listing_data.user.username
    return render(request, "auctions/listing.html", {
        "listing": listing_data,
        "in_watchlist": in_watchlist,
        "all_comments": all_comments,
        "is_owner": is_owner,
        "update": True,
        "message": "Congratulations, your item has been sold!"
    })


def add_bid(request, id):
    new_bid = request.POST['new_bid']
    listing_data = Listing.objects.get(pk=id)
    in_watchlist = request.user in listing_data.watchlist.all()
    all_comments = Comment.objects.filter(listing=listing_data)
    is_owner = request.user.username == listing_data.user.username ##
    if int(new_bid) > listing_data.price.bid:
        update_bid = Bid(user=request.user, bid=int(new_bid))
        update_bid.save()
        listing_data.price = update_bid
        listing_data.save()
        return render(request, "auctions/listing.html", {
            "listing": listing_data,
            "message": "Thank you for your bid!",
            "update": True,
            "in_watchlist": in_watchlist,
            "all_comments": all_comments,
            "is_owner": is_owner ##
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listing_data,
            "message": "Please try again and enter a higher bid",
            "update": False,
            "in_watchlist": in_watchlist,
            "all_comments": all_comments,
            "is_owner": is_owner
        })
        # return HttpResponseRedirect(reverse("listing", args=(id, ), kwargs=(message="Didn't win")))

def add_comment(request, id):
    current_user = request.user
    listing_data = Listing.objects.get(pk=id)
    message = request.POST['new_comment']

    new_comment = Comment(
        author=current_user,
        listing=listing_data,
        message=message
    )
    new_comment.save()

    return HttpResponseRedirect(reverse("listing", args=(id, )))


def watchlist(request):
    current_user = request.user
    listings = current_user.listing_watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def remove_watchlist(request, id):
    listing_data = Listing.objects.get(pk=id)
    current_user = request.user
    listing_data.watchlist.remove(current_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def add_watchlist(request, id):
    listing_data = Listing.objects.get(pk=id)
    current_user = request.user
    listing_data.watchlist.add(current_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))


def index(request):
    active_listings = Listing.objects.filter(is_active=True)
    all_categories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": active_listings,
        "categories": all_categories
    })


def display_category(request):
    if request.method == "POST":
        category_from_form = request.POST['category']
        category = Category.objects.get(category_name=category_from_form)
        active_listings = Listing.objects.filter(is_active=True, category=category)
        all_categories = Category.objects.all()
        return render(request, "auctions/index.html", {
            "listings": active_listings,
            "categories": all_categories
        })


def create_listing(request):
    if request.method == "GET":
        all_categories = Category.objects.all()
        return render(request, "auctions/create_listing.html", {
            "categories": all_categories
        })
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        image = request.POST["image"]
        price = request.POST["price"]
        category = request.POST["category"]
        current_user = request.user
        category_data = Category.objects.get(category_name=category)
        bid = Bid(bid=int(price), user=current_user) # Bid(bid=float(price)
        bid.save()
        new_listing = Listing(
            title=title,
            description=description,
            image=image,
            price=bid,
            category=category_data,
            user=current_user
        )
        new_listing.save()
        return HttpResponseRedirect(reverse(index))


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
