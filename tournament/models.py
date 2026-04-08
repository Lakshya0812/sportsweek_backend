"""
Models for the Sports Week Tournament application.

Relationships:
  Galaxy   ─< Player  (each galaxy has many players)
  Galaxy   ─< Match   (as galaxy_1, galaxy_2, or winner)
  Sport    ─< Match
  Match    ─< SubMatch
  Player   ─< SubMatch (as player_1, player_2, or winner)
"""
from django.db import models
from django.conf import settings


class Galaxy(models.Model):
    """A competing team in the tournament, referred to as a 'Galaxy'."""
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='galaxy_logos/', blank=True, null=True)
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-total_points', 'name']
        verbose_name_plural = 'Galaxies'

    def __str__(self):
        return self.name

    def recalculate_points(self):
        """Recompute total_points from all won matches. Call after any result change."""
        from django.db.models import Sum
        won = Match.objects.filter(winner=self).aggregate(total=Sum('points_awarded'))
        self.total_points = won['total'] or 0
        self.save(update_fields=['total_points'])


class Player(models.Model):
    """An individual player who belongs to a Galaxy."""
    name = models.CharField(max_length=100)
    galaxy = models.ForeignKey(Galaxy, on_delete=models.CASCADE, related_name='players')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['galaxy', 'name']
        # A player name must be unique within a galaxy
        unique_together = [('name', 'galaxy')]

    def __str__(self):
        return f'{self.name} ({self.galaxy.name})'


class Sport(models.Model):
    """A sport category (e.g. Cricket, Football, Badminton)."""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Match(models.Model):
    """
    A top-level fixture between two galaxies within a sport.
    The overall match winner and points are set here.
    Individual player contests are recorded as SubMatch records.

    Business rules:
    - When winner is saved, points_awarded are added to the winner's total.
    - If is_final=True, FINAL_BONUS_POINTS (from settings) are added on top.
    """
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='matches')
    galaxy_1 = models.ForeignKey(
        Galaxy, on_delete=models.CASCADE, related_name='home_matches'
    )
    galaxy_2 = models.ForeignKey(
        Galaxy, on_delete=models.CASCADE, related_name='away_matches'
    )
    winner = models.ForeignKey(
        Galaxy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_matches',
    )
    points_awarded = models.PositiveIntegerField(
        default=3,
        help_text='Base points awarded to the winner of this match.',
    )
    is_final = models.BooleanField(
        default=False,
        help_text='Finals receive extra bonus points on top of base points.',
    )
    bonus_applied = models.BooleanField(default=False, editable=False)
    played_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        winner_name = self.winner.name if self.winner else 'TBD'
        return f'{self.sport.name}: {self.galaxy_1.name} vs {self.galaxy_2.name} (Winner: {winner_name})'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.galaxy_1_id and self.galaxy_2_id and self.galaxy_1_id == self.galaxy_2_id:
            raise ValidationError('A galaxy cannot play against itself.')
        if self.winner_id and self.winner_id not in (self.galaxy_1_id, self.galaxy_2_id):
            raise ValidationError('Winner must be one of the two competing galaxies.')

    def save(self, *args, **kwargs):
        """
        Override save to apply points to the winner automatically.
        Handles winner changes and removals correctly.
        """
        if self.pk:
            try:
                old = Match.objects.get(pk=self.pk)
            except Match.DoesNotExist:
                old = None
        else:
            old = None

        super().save(*args, **kwargs)

        affected = set()
        if old and old.winner_id:
            affected.add(old.winner_id)
        if self.winner_id:
            affected.add(self.winner_id)

        for galaxy_id in affected:
            from tournament.models import Galaxy as G
            g = G.objects.get(pk=galaxy_id)
            g.recalculate_points()


class SubMatch(models.Model):
    """
    An individual contest within a Match.

    Singles: one player from each galaxy face each other.
    Doubles: two players from each galaxy (a pair) face the opposing pair.
    Team:    multiple players per side (e.g. volleyball, kho kho).

    For singles/doubles the winner FK points to player_1 or player_2:
      winner == player_1  →  galaxy_1 side wins
      winner == player_2  →  galaxy_2 side wins

    For team matches player_1/player_2 are unused; rosters live in
    SubMatchTeamPlayer and the result is stored in winning_side_team (1 or 2).
    """
    TYPE_SINGLES = 'singles'
    TYPE_DOUBLES = 'doubles'
    TYPE_TEAM    = 'team'
    TYPE_CHOICES = [
        (TYPE_SINGLES, 'Singles'),
        (TYPE_DOUBLES, 'Doubles'),
        (TYPE_TEAM,    'Team'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='sub_matches')
    order = models.PositiveSmallIntegerField(
        default=1,
        help_text='Display order of this sub-match within the parent match.',
    )
    sub_match_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default=TYPE_SINGLES,
    )

    # ── Side 1 (galaxy_1) ────────────────────────────────────────────────
    player_1 = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='sub_matches_as_p1',
        help_text='Singles/doubles only — must belong to galaxy_1.',
    )
    player_1b = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='sub_matches_as_p1b',
        help_text='Doubles partner; must belong to galaxy_1 (≠ player_1).',
    )

    # ── Side 2 (galaxy_2) ────────────────────────────────────────────────
    player_2 = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='sub_matches_as_p2',
        help_text='Singles/doubles only — must belong to galaxy_2.',
    )
    player_2b = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='sub_matches_as_p2b',
        help_text='Doubles partner; must belong to galaxy_2 (≠ player_2).',
    )

    # singles/doubles: winner FK (player_1 → side 1 wins, player_2 → side 2 wins)
    winner = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='won_sub_matches',
    )
    # team: winning side (1 or 2)
    winning_side_team = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(1, 'Side 1 (Galaxy 1)'), (2, 'Side 2 (Galaxy 2)')],
        help_text='Team sub-matches only — which galaxy side won.',
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        help_text='Optional notes, e.g. score "21-18, 21-15" or remarks.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['match', 'order']

    def __str__(self):
        if self.sub_match_type == self.TYPE_TEAM:
            winner_str = f'Side {self.winning_side_team}' if self.winning_side_team else 'TBD'
            return f'Sub-match #{self.order} [team] (Winner: {winner_str})'
        is_doubles = self.sub_match_type == self.TYPE_DOUBLES
        if is_doubles and self.player_1b_id and self.player_2b_id:
            side1 = f'{self.player_1.name} & {self.player_1b.name}'
            side2 = f'{self.player_2.name} & {self.player_2b.name}'
        else:
            side1 = self.player_1.name if self.player_1 else '?'
            side2 = self.player_2.name if self.player_2 else '?'
        winner_name = self.winner.name if self.winner else 'TBD'
        return f'Sub-match #{self.order} [{self.sub_match_type}]: {side1} vs {side2} (Winner: {winner_name})'

    def clean(self):
        from django.core.exceptions import ValidationError
        is_doubles = self.sub_match_type == self.TYPE_DOUBLES
        is_team    = self.sub_match_type == self.TYPE_TEAM

        if is_team:
            if self.player_1_id or self.player_2_id or self.player_1b_id or self.player_2b_id:
                raise ValidationError('Team sub-matches must not set player fields; use team roster.')
            if self.winner_id:
                raise ValidationError('Team sub-matches use winning_side_team, not winner FK.')
            if self.winning_side_team is not None and self.winning_side_team not in (1, 2):
                raise ValidationError('winning_side_team must be 1 or 2.')
            return

        # ── Singles / Doubles ─────────────────────────────────────────────
        if self.match_id:
            if self.player_1_id and self.player_1.galaxy_id != self.match.galaxy_1_id:
                raise ValidationError(
                    f'player_1 must belong to {self.match.galaxy_1.name}.'
                )
            if self.player_2_id and self.player_2.galaxy_id != self.match.galaxy_2_id:
                raise ValidationError(
                    f'player_2 must belong to {self.match.galaxy_2.name}.'
                )
            if is_doubles:
                if self.player_1b_id and self.player_1b.galaxy_id != self.match.galaxy_1_id:
                    raise ValidationError(
                        f'player_1b must belong to {self.match.galaxy_1.name}.'
                    )
                if self.player_2b_id and self.player_2b.galaxy_id != self.match.galaxy_2_id:
                    raise ValidationError(
                        f'player_2b must belong to {self.match.galaxy_2.name}.'
                    )

        if is_doubles:
            if self.player_1b_id and self.player_1b_id == self.player_1_id:
                raise ValidationError('player_1b must be a different player from player_1.')
            if self.player_2b_id and self.player_2b_id == self.player_2_id:
                raise ValidationError('player_2b must be a different player from player_2.')
            if not self.player_1b_id or not self.player_2b_id:
                raise ValidationError(
                    'Doubles sub-matches require player_1b and player_2b.'
                )

        if not is_doubles and (self.player_1b_id or self.player_2b_id):
            raise ValidationError(
                'Singles sub-matches must not have player_1b or player_2b.'
            )

        if self.winner_id and self.winner_id not in (self.player_1_id, self.player_2_id):
            raise ValidationError(
                'Winner must be player_1 (galaxy_1 side wins) or player_2 (galaxy_2 side wins).'
            )


class SubMatchTeamPlayer(models.Model):
    """
    Roster entry for a team sub-match.
    One row per player — stores which side (1 = galaxy_1, 2 = galaxy_2) they play for.
    """
    SIDE_CHOICES = [(1, 'Side 1 (Galaxy 1)'), (2, 'Side 2 (Galaxy 2)')]

    sub_match = models.ForeignKey(
        SubMatch,
        on_delete=models.CASCADE,
        related_name='team_players',
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='team_sub_matches',
    )
    side = models.PositiveSmallIntegerField(choices=SIDE_CHOICES)

    class Meta:
        ordering = ['sub_match', 'side', 'player']
        unique_together = [('sub_match', 'player')]

    def __str__(self):
        return f'{self.player} — Side {self.side} of SubMatch #{self.sub_match_id}'
