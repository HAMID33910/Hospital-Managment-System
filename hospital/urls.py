from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import frontend_views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'doctors', views.DoctorViewSet)
router.register(r'patients', views.PatientViewSet)
router.register(r'appointments', views.AppointmentViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'room-allocations', views.RoomAllocationViewSet)
router.register(r'medicines', views.MedicineViewSet)
router.register(r'prescriptions', views.PrescriptionViewSet)
router.register(r'bills', views.BillingViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/register/', views.RegisterView.as_view(), name='register'),
    path('api/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('api/dashboard/doctor/', views.doctor_dashboard_stats, name='doctor-dashboard'),
    path('api/profile/', views.profile_detail, name='profile-detail'),
    path('api/profile/update/', views.profile_update, name='profile-update'),
    path('', frontend_views.login_page, name='login'),
    path('dashboard/', frontend_views.dashboard_page, name='dashboard'),
]
