from django.http.request import validate_host
from django.urls import path
from myprofile import views

urlpatterns = [
    path("createdata", views.createdata),
    path("runsimulation", views.runsimulation),
]
