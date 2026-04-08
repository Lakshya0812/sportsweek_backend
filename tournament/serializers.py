"""
Serializers for the tournament app.
"""
from django.conf import settings
from rest_framework import serializers
from .models import Galaxy, Player, Sport, Match, SubMatch, SubMatchTeamPlayer


class GalaxySerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Galaxy
        fields = ['id', 'name', 'logo', 'logo_url', 'total_points', 'created_at']
        read_only_fields = ['total_points', 'created_at']
        extra_kwargs = {'logo': {'write_only': True, 'required': False}}

    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class PlayerSerializer(serializers.ModelSerializer):
    galaxy_name = serializers.CharField(source='galaxy.name', read_only=True)

    class Meta:
        model = Player
        fields = ['id', 'name', 'galaxy', 'galaxy_name', 'created_at']
        read_only_fields = ['created_at']


class SportSerializer(serializers.ModelSerializer):
    match_count = serializers.SerializerMethodField()

    class Meta:
        model = Sport
        fields = ['id', 'name', 'match_count', 'created_at']
        read_only_fields = ['created_at']

    def get_match_count(self, obj):
        return obj.matches.count()


class SubMatchTeamPlayerSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.name', read_only=True)
    galaxy_name = serializers.CharField(source='player.galaxy.name', read_only=True)

    class Meta:
        model = SubMatchTeamPlayer
        fields = ['id', 'player', 'player_name', 'galaxy_name', 'side']


class SubMatchSerializer(serializers.ModelSerializer):
    """Full sub-match serializer — handles singles, doubles, and team."""
    player_1_name   = serializers.CharField(source='player_1.name', read_only=True, default=None)
    player_1_galaxy = serializers.CharField(source='player_1.galaxy.name', read_only=True, default=None)
    player_1b_name  = serializers.CharField(source='player_1b.name', read_only=True, default=None)

    player_2_name   = serializers.CharField(source='player_2.name', read_only=True, default=None)
    player_2_galaxy = serializers.CharField(source='player_2.galaxy.name', read_only=True, default=None)
    player_2b_name  = serializers.CharField(source='player_2b.name', read_only=True, default=None)

    winner_name  = serializers.CharField(source='winner.name', read_only=True, default=None)
    winning_side = serializers.SerializerMethodField()

    # Team support
    team_players      = SubMatchTeamPlayerSerializer(many=True, read_only=True)
    side_1_player_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=list,
    )
    side_2_player_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=list,
    )

    class Meta:
        model = SubMatch
        fields = [
            'id', 'match', 'order', 'sub_match_type',
            'player_1', 'player_1_name', 'player_1_galaxy',
            'player_1b', 'player_1b_name',
            'player_2', 'player_2_name', 'player_2_galaxy',
            'player_2b', 'player_2b_name',
            'winner', 'winner_name', 'winning_side',
            'winning_side_team',
            'team_players', 'side_1_player_ids', 'side_2_player_ids',
            'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'player_1': {'required': False, 'allow_null': True},
            'player_2': {'required': False, 'allow_null': True},
        }

    def get_winning_side(self, obj):
        """Return 1 if galaxy_1 side won, 2 if galaxy_2 side won, None if TBD."""
        if obj.sub_match_type == SubMatch.TYPE_TEAM:
            return obj.winning_side_team
        if not obj.winner_id:
            return None
        return 1 if obj.winner_id == obj.player_1_id else 2

    def validate(self, data):
        match   = data.get('match',          getattr(self.instance, 'match',          None))
        stype   = data.get('sub_match_type', getattr(self.instance, 'sub_match_type', SubMatch.TYPE_SINGLES))
        is_team    = stype == SubMatch.TYPE_TEAM
        is_doubles = stype == SubMatch.TYPE_DOUBLES

        if is_team:
            if data.get('player_1') or data.get('player_2'):
                raise serializers.ValidationError(
                    'Team sub-matches must not set player_1 or player_2.'
                )
            if data.get('winner'):
                raise serializers.ValidationError(
                    'Team sub-matches use winning_side_team, not the winner field.'
                )
            wst = data.get('winning_side_team')
            if wst is not None and wst not in (1, 2):
                raise serializers.ValidationError('winning_side_team must be 1 or 2.')
            # Validate team rosters belong to correct galaxy
            if match:
                for pid in data.get('side_1_player_ids', []):
                    try:
                        p = Player.objects.get(pk=pid)
                    except Player.DoesNotExist:
                        raise serializers.ValidationError(f'Player id {pid} does not exist.')
                    if p.galaxy_id != match.galaxy_1_id:
                        raise serializers.ValidationError(
                            f'{p.name} must belong to {match.galaxy_1.name} for side 1.'
                        )
                for pid in data.get('side_2_player_ids', []):
                    try:
                        p = Player.objects.get(pk=pid)
                    except Player.DoesNotExist:
                        raise serializers.ValidationError(f'Player id {pid} does not exist.')
                    if p.galaxy_id != match.galaxy_2_id:
                        raise serializers.ValidationError(
                            f'{p.name} must belong to {match.galaxy_2.name} for side 2.'
                        )
            overlap = set(data.get('side_1_player_ids', [])) & set(data.get('side_2_player_ids', []))
            if overlap:
                raise serializers.ValidationError('A player cannot be on both sides.')
            data['player_1'] = None
            data['player_2'] = None
            data['player_1b'] = None
            data['player_2b'] = None
            return data

        # ── Singles / Doubles ─────────────────────────────────────────────
        player_1  = data.get('player_1',  getattr(self.instance, 'player_1',  None))
        player_1b = data.get('player_1b', getattr(self.instance, 'player_1b', None))
        player_2  = data.get('player_2',  getattr(self.instance, 'player_2',  None))
        player_2b = data.get('player_2b', getattr(self.instance, 'player_2b', None))
        winner    = data.get('winner',    getattr(self.instance, 'winner',    None))

        if match and player_1 and player_1.galaxy_id != match.galaxy_1_id:
            raise serializers.ValidationError(
                f'player_1 must belong to {match.galaxy_1.name}.'
            )
        if match and player_2 and player_2.galaxy_id != match.galaxy_2_id:
            raise serializers.ValidationError(
                f'player_2 must belong to {match.galaxy_2.name}.'
            )

        if is_doubles:
            if not player_1b or not player_2b:
                raise serializers.ValidationError('Doubles requires player_1b and player_2b.')
            if match and player_1b and player_1b.galaxy_id != match.galaxy_1_id:
                raise serializers.ValidationError(
                    f'player_1b must belong to {match.galaxy_1.name}.'
                )
            if match and player_2b and player_2b.galaxy_id != match.galaxy_2_id:
                raise serializers.ValidationError(
                    f'player_2b must belong to {match.galaxy_2.name}.'
                )
            if player_1 and player_1b and player_1 == player_1b:
                raise serializers.ValidationError('player_1b must differ from player_1.')
            if player_2 and player_2b and player_2 == player_2b:
                raise serializers.ValidationError('player_2b must differ from player_2.')
        else:
            data['player_1b'] = None
            data['player_2b'] = None

        if winner and player_1 and player_2 and winner not in (player_1, player_2):
            raise serializers.ValidationError(
                'winner must be player_1 (galaxy_1 side) or player_2 (galaxy_2 side).'
            )
        return data

    def create(self, validated_data):
        side_1_ids = validated_data.pop('side_1_player_ids', [])
        side_2_ids = validated_data.pop('side_2_player_ids', [])
        sub_match = super().create(validated_data)
        for pid in side_1_ids:
            SubMatchTeamPlayer.objects.create(sub_match=sub_match, player_id=pid, side=1)
        for pid in side_2_ids:
            SubMatchTeamPlayer.objects.create(sub_match=sub_match, player_id=pid, side=2)
        return sub_match


class SubMatchResultSerializer(serializers.ModelSerializer):
    """Lightweight PATCH serializer — update result and notes only."""
    class Meta:
        model = SubMatch
        fields = ['winner', 'notes', 'winning_side_team']

    def validate(self, data):
        is_team = self.instance and self.instance.sub_match_type == SubMatch.TYPE_TEAM
        if is_team:
            if data.get('winner'):
                raise serializers.ValidationError(
                    'Team sub-matches use winning_side_team, not the winner field.'
                )
            wst = data.get('winning_side_team')
            if wst is not None and wst not in (1, 2):
                raise serializers.ValidationError('winning_side_team must be 1 or 2.')
        else:
            winner = data.get('winner', self.instance.winner if self.instance else None)
            if winner and self.instance:
                if winner not in (self.instance.player_1, self.instance.player_2):
                    raise serializers.ValidationError(
                        'winner must be player_1 (galaxy_1 side) or player_2 (galaxy_2 side).'
                    )
        return data


class MatchSerializer(serializers.ModelSerializer):
    """Full match serializer — includes nested sub-matches."""
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    galaxy_1_name = serializers.CharField(source='galaxy_1.name', read_only=True)
    galaxy_2_name = serializers.CharField(source='galaxy_2.name', read_only=True)
    winner_name = serializers.CharField(source='winner.name', read_only=True)
    bonus_points = serializers.SerializerMethodField()
    sub_matches = SubMatchSerializer(many=True, read_only=True)
    sub_match_count = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            'id', 'sport', 'sport_name',
            'galaxy_1', 'galaxy_1_name',
            'galaxy_2', 'galaxy_2_name',
            'winner', 'winner_name',
            'points_awarded', 'bonus_points',
            'is_final', 'played_at',
            'sub_match_count', 'sub_matches',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_bonus_points(self, obj):
        if obj.is_final:
            return getattr(settings, 'FINAL_BONUS_POINTS', 5)
        return 0

    def get_sub_match_count(self, obj):
        return obj.sub_matches.count()

    def validate(self, data):
        galaxy_1 = data.get('galaxy_1', getattr(self.instance, 'galaxy_1', None))
        galaxy_2 = data.get('galaxy_2', getattr(self.instance, 'galaxy_2', None))
        winner = data.get('winner', getattr(self.instance, 'winner', None))

        if galaxy_1 and galaxy_2 and galaxy_1 == galaxy_2:
            raise serializers.ValidationError('A galaxy cannot play against itself.')
        if winner and galaxy_1 and galaxy_2:
            if winner not in (galaxy_1, galaxy_2):
                raise serializers.ValidationError(
                    'Winner must be one of the two competing galaxies.'
                )
        return data


class MatchResultSerializer(serializers.ModelSerializer):
    """Lightweight PATCH serializer — update winner/points/final only."""
    class Meta:
        model = Match
        fields = ['winner', 'points_awarded', 'is_final', 'played_at']

    def validate(self, data):
        winner = data.get('winner', self.instance.winner if self.instance else None)
        galaxy_1 = self.instance.galaxy_1 if self.instance else None
        galaxy_2 = self.instance.galaxy_2 if self.instance else None

        if winner and galaxy_1 and galaxy_2:
            if winner not in (galaxy_1, galaxy_2):
                raise serializers.ValidationError(
                    'Winner must be one of the two competing galaxies.'
                )
        return data


class DashboardSerializer(serializers.Serializer):
    """Aggregated stats for the admin dashboard."""
    total_matches = serializers.IntegerField()
    completed_matches = serializers.IntegerField()
    pending_matches = serializers.IntegerField()
    total_galaxies = serializers.IntegerField()
    total_sports = serializers.IntegerField()
    total_players = serializers.IntegerField()
    total_sub_matches = serializers.IntegerField()
    points_distribution = GalaxySerializer(many=True)
