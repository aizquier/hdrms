"""hdrms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from repository import views

urlpatterns = [
    url(r'^$', views.issue_csrf_key),
    url(r'^set/$', views.hdrms_sets_level_one, name="hdrms_sets_level_one"),
    url(r'^set/(id\.[A-Fa-f0-9]+)$', views.hdrms_sets_level_two, name="hdrms_sets_level_two"),
    url(r'^set/(id\.[A-Fa-f0-9]+)/(resid\.[A-Fa-f0-9]+)$', views.hdrms_sets_level_three, name="hdrms_sets_level_three"),
    url(r'^admin/', admin.site.urls),
]
