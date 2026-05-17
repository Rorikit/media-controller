from pathlib import Path
import shutil


def main():
    output_dir = Path('site')
    index_file = output_dir / 'index.html'
    fallback_file = output_dir / '404.html'
    if not index_file.exists():
        raise SystemExit('site/index.html was not found. Run export_static_site first.')
    shutil.copyfile(index_file, fallback_file)
    print('Created site/404.html')


if __name__ == '__main__':
    main()
