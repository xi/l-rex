from django.conf.urls import url
from django.conf.urls import include

from apps.response import urls as response_urls
from . import views

urlpatterns = [
    url(r'user-trial-create/$',
        views.UserTrialCreateView.as_view(),
        name='user-trial-create'),
    url(r'user-trials/$',
        views.UserTrialListView.as_view(),
        name='user-trials'),
    url(r'user-trial/(?P<slug>[-\w_]+)/response/',
        include(response_urls)),
    url(r'user-trial/(?P<slug>[-\w_]+)/$',
        views.UserTrialDetailView.as_view(),
        name='user-trial'),
    url(r'trials/$',
        views.TrialListView.as_view(),
        name='trials'),
]