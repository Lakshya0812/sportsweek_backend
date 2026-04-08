"""URL configuration for the tournament app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    GalaxyViewSet,
    PlayerViewSet,
    SportViewSet,
    MatchViewSet,
    SubMatchViewSet,
    SubMatchTeamPlayerViewSet,
    DashboardView,
)

router = DefaultRouter()
router.register(r'galaxies', GalaxyViewSet, basename='galaxy')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'sports', SportViewSet, basename='sport')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'sub-matches', SubMatchViewSet, basename='submatch')
router.register(r'sub-match-team-players', SubMatchTeamPlayerViewSet, basename='submatch-team-player')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', include(router.urls)),
]
