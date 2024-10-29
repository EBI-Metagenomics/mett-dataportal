from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Compile SCSS files"

    def handle(self, *args, **options):
        call_command("collectstatic", "--noinput")
