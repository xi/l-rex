from django.conf.urls import url
from django.conf.urls import include

from apps.item import urls as item_urls
from . import views

urlpatterns = [
    url(r'^(?P<slug>[-\w_]+)/item/', include(item_urls)),
    url(r'^create/$',
        views.ExperimentCreateView.as_view(),
        name='experiment-create'),
    url(r'^update/(?P<slug>[-\w_]+)/$',
        views.ExperimentUpdateView.as_view(),
        name='experiment-update'),
    url(r'^delete/(?P<slug>[-\w_]+)/$',
        views.ExperimentDeleteView.as_view(),
        name='experiment-delete'),
    url(r'^results/$',
        views.ExperimentResultListView.as_view(),
        name='experiment-result-list'),
    url(r'^results/(?P<slug>[-\w_]+)/$',
        views.ExperimentResultsView.as_view(),
        name='experiment-results'),
    url(r'^results/(?P<slug>[-\w_]+)/csv/$',
        views.ExperimentResultsCSVDownloadView.as_view(),
        name='experiment-results-csv'),
    url(r'^(?P<slug>[-\w_]+)/$',
        views.ExperimentDetailView.as_view(),
        name='experiment'),
    url(r'^$',
        views.ExperimentListView.as_view(),
        name='experiments'),
]