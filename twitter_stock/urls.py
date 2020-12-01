from django.urls import path
from django.conf.urls import url

from .utils import my_request as my


urlpatterns = [
    url(r"^$", my.my_page),
    path("loadingData/", my.loadingData),
    path("predict/", my.predict),
    path("mygraph/", my.mygraph),
    path("share/", my.share),
]
