from paver.setuputils import setup
from setuptools import find_packages
from utilities import VERSION
setup(
    name='srccheck',
    description='Source code KALOI (using Understand).',
    packages=find_packages(),
    version=VERSION,
    url='https://github.com/sglebs/srccheck',
    author='Marcio Marchini',
    author_email='marcio@betterdeveloper.net',
    install_requires=[
        'docopt==0.6.2',
        'requests==2.10.0',
        'matplotlib==1.5.3',
        'Jinja2==2.8',
        'mpld3==0.3'
    ],
    entry_points={
        'console_scripts': [
            'srccheck = utilities.srccheck:main',
            'srchistplot = utilities.srchistplot:main',
            'srcscatterplot = utilities.srcscatterplot:main',
            'srcinstplot = utilities.srcinstplot:main',
            'srcdiffplot = utilities.srcdiffplot:main',
        ],
    }
)
