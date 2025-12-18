"""
URL configuration for MHOERS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import user_login  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('referral/', include(('referrals.urls', 'referrals'), namespace='referrals')),
    path('', user_login, name='root_login'),
    path('patients/', include(('patients.urls', 'patients'), namespace='patients')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('facilities/', include('facilities.urls')),
    path('analytics/', include('analytics.urls')),
    path('chat/', include('chat.urls', namespace='chat')),

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
