"""iamdc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
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
from dashboard import views as dashboard_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$',dashboard_views.index),
    url(r'^login/',dashboard_views.login),
    url(r'^logout/',dashboard_views.logout),
    url(r'^users/',dashboard_views.usercenter),
    url(r'^department/',dashboard_views.departmentmanage),
    url(r'^tickettype/',dashboard_views.tickettype),
    url(r'^project/',dashboard_views.tickettype),
    url(r'^ticketadd/',dashboard_views.ticketadd),
    url(r'^mytask/',dashboard_views.mytask), 
    url(r'^myticket/$',dashboard_views.myticket),
    url(r'^mycheck/',dashboard_views.mycheck),
    url(r'^tickethistory/',dashboard_views.tickethistory),
    url(r'^servertype/',dashboard_views.servertype),
]
