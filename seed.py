"""
Seed script — populates the database with:
  - 8 Galaxies
  - 5 Sports
  - Players per galaxy (3–4 per galaxy)
  - Sample matches (some with results)
  - Sub-matches with player matchups
  - A Django superuser (admin / admin123)

Usage:
  python manage.py shell < seed.py
  # OR run standalone:
  python seed.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sports_backend.settings')
django.setup()

from django.contrib.auth.models import User
from tournament.models import Galaxy, Player, Sport, Match, SubMatch

# ── Superuser ─────────────────────────────────────────────────────────────────
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Created superuser: admin / admin123')
else:
    print('Superuser already exists.')

# ── Galaxies ──────────────────────────────────────────────────────────────────
GALAXY_NAMES = [
    'Andromeda', 'Milky Way', 'Triangulum', 'Whirlpool',
    'Sombrero', 'Pinwheel', 'Black Eye', 'Cartwheel',
]

galaxies = {}
for name in GALAXY_NAMES:
    obj, created = Galaxy.objects.get_or_create(name=name)
    galaxies[name] = obj
    if created:
        print(f'  Galaxy created: {name}')

# ── Players (3–4 per galaxy) ──────────────────────────────────────────────────
GALAXY_PLAYERS = {
    'Andromeda': ['Arjun Sharma', 'Priya Nair', 'Kiran Das', 'Ravi Menon'],
    'Milky Way':  ['Amit Patel',  'Sunita Rao', 'Deepak Iyer', 'Kavya Singh'],
    'Triangulum': ['Rohan Gupta', 'Ananya Bose', 'Vikram Joshi', 'Sneha Pillai'],
    'Whirlpool':  ['Sanjay Kumar', 'Meera Nambiar', 'Aditya Shah', 'Pooja Reddy'],
    'Sombrero':   ['Nikhil Verma', 'Divya Krishnan', 'Suresh Patil', 'Lakshmi Raj'],
    'Pinwheel':   ['Rahul Mehta', 'Swati Desai', 'Manoj Nair', 'Ishita Ghosh'],
    'Black Eye':  ['Varun Aggarwal', 'Anjali Mishra', 'Tushar Yadav', 'Priti Dube'],
    'Cartwheel':  ['Sandeep Roy', 'Nisha Pillai', 'Gaurav Sinha', 'Bhavna Tiwari'],
}

players = {}  # { galaxy_name: [Player, ...] }
for galaxy_name, player_names in GALAXY_PLAYERS.items():
    galaxy = galaxies[galaxy_name]
    players[galaxy_name] = []
    for pname in player_names:
        p, created = Player.objects.get_or_create(name=pname, galaxy=galaxy)
        players[galaxy_name].append(p)
        if created:
            print(f'  Player created: {pname} ({galaxy_name})')

# ── Sports ────────────────────────────────────────────────────────────────────
SPORT_NAMES = ['Cricket', 'Football', 'Badminton', 'Table Tennis', 'Basketball']

sports = {}
for name in SPORT_NAMES:
    obj, created = Sport.objects.get_or_create(name=name)
    sports[name] = obj
    if created:
        print(f'  Sport created: {name}')

# ── Matches + Sub-Matches ─────────────────────────────────────────────────────
# Format: (sport, g1, g2, winner_or_None, base_pts, is_final,
#           [ (p1_idx, p2_idx, winner_side_or_None, notes), ... ])
# winner_side: 'p1' | 'p2' | None
MATCH_DATA = [
    # ── Cricket ──────────────────────────────────────────────────────────────
    ('Cricket', 'Andromeda', 'Milky Way', 'Andromeda', 3, False, [
        (0, 0, 'p1', 'Arjun 45 runs vs Amit 30 runs'),
        (1, 1, 'p2', 'Sunita 52 runs vs Priya 40 runs'),
        (2, 2, 'p1', 'Kiran took 3 wickets'),
    ]),
    ('Cricket', 'Triangulum', 'Whirlpool', 'Whirlpool', 3, False, [
        (0, 0, 'p2', 'Sanjay 60 runs vs Rohan 45 runs'),
        (1, 1, 'p1', 'Ananya 38 runs vs Meera 25 runs'),
        (2, 2, 'p2', 'Aditya 4 wickets'),
    ]),
    ('Cricket', 'Sombrero', 'Pinwheel', 'Sombrero', 3, False, [
        (0, 0, 'p1', 'Nikhil 70 runs vs Rahul 50 runs'),
        (1, 1, 'p1', 'Divya 44 runs vs Swati 30 runs'),
    ]),
    ('Cricket', 'Black Eye', 'Cartwheel', 'Black Eye', 3, False, [
        (0, 0, 'p1', 'Varun 55 runs vs Sandeep 40 runs'),
        (1, 1, 'p2', 'Nisha 48 runs vs Anjali 35 runs'),
        (2, 2, 'p1', 'Tushar took 5 wickets'),
    ]),
    # Cricket Final
    ('Cricket', 'Andromeda', 'Black Eye', 'Andromeda', 5, True, [
        (0, 0, 'p1', 'Final: Arjun 80 runs vs Varun 60 runs'),
        (1, 1, 'p1', 'Priya 55 runs vs Anjali 42 runs'),
        (3, 2, 'p2', 'Tushar 65 runs vs Ravi 50 runs'),
    ]),

    # ── Football ──────────────────────────────────────────────────────────────
    ('Football', 'Milky Way', 'Triangulum', 'Milky Way', 3, False, [
        (0, 0, 'p1', 'Amit scored 2 goals'),
        (1, 1, 'p1', 'Sunita scored 1 goal vs Ananya'),
    ]),
    ('Football', 'Whirlpool', 'Sombrero', 'Whirlpool', 3, False, [
        (0, 0, 'p1', 'Sanjay hat-trick'),
        (1, 1, 'p2', 'Divya scored 2 goals'),
    ]),
    ('Football', 'Pinwheel', 'Cartwheel', None, 3, False, []),   # pending
    # Football Final
    ('Football', 'Milky Way', 'Whirlpool', 'Milky Way', 5, True, [
        (0, 0, 'p1', 'Amit scored the winning goal'),
        (1, 1, 'p2', 'Meera equalised — penalty shootout'),
    ]),

    # ── Badminton ─────────────────────────────────────────────────────────────
    ('Badminton', 'Andromeda', 'Triangulum', 'Triangulum', 3, False, [
        (0, 0, 'p2', 'Rohan won 21-15, 21-18'),
        (1, 1, 'p1', 'Priya won 21-19, 21-16'),
        (2, 2, 'p2', 'Vikram won 21-10, 21-14 — decisive'),
    ]),
    ('Badminton', 'Sombrero', 'Cartwheel', 'Sombrero', 3, False, [
        (0, 0, 'p1', 'Nikhil won 21-18, 21-20'),
        (1, 1, 'p2', 'Nisha won 21-13, 21-15'),
        (2, 2, 'p1', 'Suresh won 21-17, 21-19'),
    ]),
    # Badminton Final — pending
    ('Badminton', 'Triangulum', 'Sombrero', None, 5, True, []),

    # ── Table Tennis ──────────────────────────────────────────────────────────
    ('Table Tennis', 'Pinwheel', 'Andromeda', 'Pinwheel', 3, False, [
        (0, 0, 'p1', 'Rahul won 11-8, 11-6, 11-9'),
        (1, 3, 'p1', 'Swati won 11-7, 11-10, 11-8'),
    ]),
    ('Table Tennis', 'Black Eye', 'Milky Way', None, 3, False, []),  # pending

    # ── Basketball ────────────────────────────────────────────────────────────
    ('Basketball', 'Cartwheel', 'Whirlpool', 'Cartwheel', 3, False, [
        (0, 0, 'p1', 'Sandeep scored 24 pts vs Sanjay 18 pts'),
        (1, 1, 'p2', 'Meera 16 pts vs Nisha 12 pts'),
    ]),
    ('Basketball', 'Andromeda', 'Sombrero', 'Andromeda', 3, False, [
        (0, 0, 'p1', 'Arjun 28 pts vs Nikhil 22 pts'),
        (2, 2, 'p2', 'Suresh 18 pts vs Kiran 14 pts — close game'),
    ]),
]

for entry in MATCH_DATA:
    sport_name, g1_name, g2_name, winner_name, pts, is_final, subs = entry

    sport  = sports[sport_name]
    g1     = galaxies[g1_name]
    g2     = galaxies[g2_name]
    winner = galaxies[winner_name] if winner_name else None

    match, created = Match.objects.get_or_create(
        sport=sport, galaxy_1=g1, galaxy_2=g2,
        defaults=dict(winner=winner, points_awarded=pts, is_final=is_final),
    )
    if created:
        lbl = f'Winner: {winner_name}' if winner_name else 'Pending'
        print(f'  Match: {sport_name} | {g1_name} vs {g2_name} | {lbl}')

    # Seed sub-matches only for newly created matches to avoid dupes
    if created and subs:
        g1_players = players[g1_name]
        g2_players = players[g2_name]
        for order, (p1_idx, p2_idx, win_side, notes) in enumerate(subs, start=1):
            p1 = g1_players[p1_idx]
            p2 = g2_players[p2_idx]
            sub_winner = (p1 if win_side == 'p1' else p2) if win_side else None
            SubMatch.objects.create(
                match=match, order=order,
                player_1=p1, player_2=p2,
                winner=sub_winner, notes=notes,
            )
        print(f'    └─ {len(subs)} sub-matches added')

print('\nSeeding complete!')
print('Login with: admin / admin123')
