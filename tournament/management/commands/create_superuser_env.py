import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create superuser from environment variables'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = 'auriga-sports'
        email = 'admin@auriga.com'
        password = 'aurigasports@123'

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" password updated.'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
