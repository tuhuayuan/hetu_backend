from setuptools import setup, find_packages

setup(
    name='hetu_backend',
    version='1.0.0',
    description='Hetu api server',
    author='Huayuan Tu',
    author_email='tuhuayuan@gmail.com',
    packages=find_packages(),
    install_requires=[
        'Django',
        'django-ninja',
        'click',
        'requests',
        'prometheus-client',
        'python-dateutil',
        'pyjwt',
        'captcha',
    ],
    entry_points={
        'console_scripts': [
            'exporter = apps.exporter.script.exporter:cli',
        ],
    },
)
