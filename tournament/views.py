"""
Views for the Sports Week Tournament API.
"""
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_filters.rest_framework import DjangoFilterBackend

from .models import Galaxy, Player, Sport, Match, SubMatch, SubMatchTeamPlayer
from .serializers import (
    GalaxySerializer,
    PlayerSerializer,
    SportSerializer,
    MatchSerializer,
    MatchResultSerializer,
    SubMatchSerializer,
    SubMatchResultSerializer,
    SubMatchTeamPlayerSerializer,
    DashboardSerializer,
)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['username'] = self.user.username
        data['is_staff'] = self.user.is_staff
        return data


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


# ---------------------------------------------------------------------------
# Galaxy
# ---------------------------------------------------------------------------

class GalaxyViewSet(viewsets.ModelViewSet):
    queryset = Galaxy.objects.all()
    serializer_class = GalaxySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['total_points', 'name']
    ordering = ['-total_points']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

class PlayerViewSet(viewsets.ModelViewSet):
    """
    GET  /api/players/           — public (filter by ?galaxy=<id>)
    POST /api/players/           — admin only
    PATCH/DELETE /api/players/{id} — admin only
    """
    queryset = Player.objects.select_related('galaxy').all()
    serializer_class = PlayerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['galaxy']
    search_fields = ['name', 'galaxy__name']
    ordering_fields = ['name', 'galaxy']
    ordering = ['galaxy', 'name']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]


# ---------------------------------------------------------------------------
# Sport
# ---------------------------------------------------------------------------

class SportViewSet(viewsets.ModelViewSet):
    queryset = Sport.objects.all()
    serializer_class = SportSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]


# ---------------------------------------------------------------------------
# Match
# ---------------------------------------------------------------------------

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.select_related(
        'sport', 'galaxy_1', 'galaxy_2', 'winner'
    ).prefetch_related(
        'sub_matches__player_1__galaxy',
        'sub_matches__player_2__galaxy',
        'sub_matches__winner',
        'sub_matches__team_players__player__galaxy',
    ).all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['sport', 'is_final', 'winner']
    ordering_fields = ['created_at', 'played_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return MatchResultSerializer
        return MatchSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# SubMatch
# ---------------------------------------------------------------------------

class SubMatchViewSet(viewsets.ModelViewSet):
    """
    GET    /api/sub-matches/           — public (filter by ?match=<id>)
    POST   /api/sub-matches/           — admin: create sub-match
    PATCH  /api/sub-matches/{id}       — admin: update winner/notes
    DELETE /api/sub-matches/{id}       — admin
    """
    queryset = SubMatch.objects.select_related(
        'match__galaxy_1', 'match__galaxy_2',
        'player_1__galaxy', 'player_2__galaxy', 'winner',
    ).prefetch_related(
        'team_players__player__galaxy',
    ).all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['match', 'winner']
    ordering_fields = ['match', 'order']
    ordering = ['match', 'order']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return SubMatchResultSerializer
        return SubMatchSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# SubMatch Team Players
# ---------------------------------------------------------------------------

class SubMatchTeamPlayerViewSet(viewsets.ModelViewSet):
    """
    GET    /api/sub-match-team-players/?sub_match=<id>  — public
    POST   /api/sub-match-team-players/                 — admin
    DELETE /api/sub-match-team-players/{id}/            — admin
    """
    queryset = SubMatchTeamPlayer.objects.select_related(
        'player__galaxy', 'sub_match__match__galaxy_1', 'sub_match__match__galaxy_2'
    ).all()
    serializer_class = SubMatchTeamPlayerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sub_match', 'side']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]


# ---------------------------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------------------------

class DashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total = Match.objects.count()
        completed = Match.objects.filter(winner__isnull=False).count()
        data = {
            'total_matches': total,
            'completed_matches': completed,
            'pending_matches': total - completed,
            'total_galaxies': Galaxy.objects.count(),
            'total_sports': Sport.objects.count(),
            'total_players': Player.objects.count(),
            'total_sub_matches': SubMatch.objects.count(),
            'points_distribution': Galaxy.objects.all(),
        }
        serializer = DashboardSerializer(data, context={'request': request})
        return Response(serializer.data)
