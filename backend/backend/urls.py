from django.urls import path, include
@@
 urlpatterns = [
     path('admin/', admin.site.urls),
     path('api/v1/auth/', include('users.urls')),
     path('api/v1/auth', include('rest_framework.urls', namespace='rest_framework')),
+    path('api/v1/', include('groups.urls')),
     path('api/v1/', include('members.urls')),
     path('api/v1/', include('accounts.urls')),
     path('api/v1/', include('loans.urls')),
@@
 ]
