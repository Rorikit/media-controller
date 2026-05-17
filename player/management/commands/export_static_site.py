import re
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.test import Client

from player.models import Playlist


class Command(BaseCommand):
    help = 'Export Django templates, static files and media as a GitHub Pages ready site.'

    def add_arguments(self, parser):
        parser.add_argument('--output', default='site', help='Output directory for static site.')
        parser.add_argument('--base-path', default=settings.PAGES_BASE_PATH, help='GitHub Pages base path, e.g. /repo/.')

    def handle(self, *args, **options):
        output_dir = settings.BASE_DIR / options['output']
        base_path = self.normalize_base_path(options['base_path'])

        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

        call_command('collectstatic', interactive=False, clear=True, verbosity=0)
        self.copy_directory(settings.STATIC_ROOT, output_dir / 'static')
        self.copy_directory(settings.MEDIA_ROOT, output_dir / 'media')

        client = Client()
        self.export_page(client, '/', output_dir / 'index.html', base_path)
        for playlist in Playlist.objects.all():
            self.export_page(
                client,
                f'/playlist/{playlist.pk}/',
                output_dir / 'playlist' / str(playlist.pk) / 'index.html',
                base_path,
            )

        # GitHub Pages serves 404.html for unknown deep links; index keeps the app usable.
        shutil.copyfile(output_dir / 'index.html', output_dir / '404.html')
        (output_dir / '.nojekyll').write_text('', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Static site exported to {output_dir}'))

    def export_page(self, client, path, destination, base_path):
        response = client.get(path)
        if response.status_code != 200:
            raise RuntimeError(f'Could not export {path}: HTTP {response.status_code}')

        html = response.content.decode('utf-8')
        html = self.rewrite_paths(html, base_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(html, encoding='utf-8')

    def rewrite_paths(self, html, base_path):
        # Django renders app links as root-relative URLs. GitHub Pages needs /REPOSITORY/.
        replacements = {
            'data-src="/': f'data-src="{base_path}',
            'data-cover="/': f'data-cover="{base_path}',
            'href="/': f'href="{base_path}',
            'action="/': f'action="{base_path}',
        }
        for old, new in replacements.items():
            html = html.replace(old, new)

        html = re.sub(r'(?<!data-)src="/', f'src="{base_path}', html)
        # STATIC_URL and MEDIA_URL are relative during local development; make them repository-rooted.
        html = re.sub(r'(href|src)="static/', rf'\1="{base_path}static/', html)
        html = re.sub(r'(href|src|data-src|data-cover)="media/', rf'\1="{base_path}media/', html)
        html = html.replace('href="playlist/', f'href="{base_path}playlist/')
        html = html.replace('<body ', '<body data-static-export="true" ', 1)
        return html

    def copy_directory(self, source, destination):
        source = Path(source)
        if not source.exists():
            return
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)

    def normalize_base_path(self, base_path):
        if not base_path:
            return '/'
        base_path = base_path.strip()
        if not base_path.startswith('/'):
            base_path = '/' + base_path
        if not base_path.endswith('/'):
            base_path += '/'
        return base_path
