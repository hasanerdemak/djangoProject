from http.client import HTTPResponse

from django.shortcuts import render, redirect

# Create your views here.

from django.http import HttpResponse

from user.models import UserProfile


def index(request):
    return HttpResponse("user")
