from django.contrib import admin
from .models import Galaxy, Player, Sport, Match, SubMatch


@admin.register(Galaxy)
class GalaxyAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_points', 'created_at')
    search_fields = ('name',)
    ordering = ('-total_points',)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'galaxy', 'created_at')
    list_filter = ('galaxy',)
    search_fields = ('name', 'galaxy__name')
    autocomplete_fields = ('galaxy',)


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


class SubMatchInline(admin.TabularInline):
    model = SubMatch
    extra = 1
    autocomplete_fields = ('player_1', 'player_2', 'winner')
    fields = ('order', 'player_1', 'player_2', 'winner', 'notes')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'sport', 'winner', 'points_awarded', 'is_final', 'played_at')
    list_filter = ('sport', 'is_final', 'winner')
    search_fields = ('galaxy_1__name', 'galaxy_2__name')
    autocomplete_fields = ('sport', 'galaxy_1', 'galaxy_2', 'winner')
    inlines = [SubMatchInline]


@admin.register(SubMatch)
class SubMatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'match', 'winner', 'notes')
    list_filter = ('match__sport',)
    search_fields = ('player_1__name', 'player_2__name')
