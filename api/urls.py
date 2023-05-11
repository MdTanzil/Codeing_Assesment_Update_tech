from django.urls import include, path
from rest_framework import routers
from .views import OrderViewSet
from .views import GeneratePDFView


router = routers.DefaultRouter()
router.register(r"orders", OrderViewSet)

urlpatterns = [
    path("sales/", include(router.urls)),
    path('report/', GeneratePDFView.as_view(), name='generate_pdf'),
]
