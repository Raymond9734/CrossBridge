from django.http import HttpRequest
from django.shortcuts import render
from inertia import (
    render as inertia_render,
)  # So that we can keep using django's default render() for non Inertia/React pages
from time import sleep


def index(request):
    return inertia_render(request, "Index", props={"name": "World"})


def about(request):
    sleep(
        2.5
    )  # This is to show the loading progress indicator on the front-end using the @inertiajs/progress package
    return inertia_render(request, "About", props={"pageName": "About"})
