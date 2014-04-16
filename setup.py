from distutils.core import setup

setup(name='stormdrain',
    version='0.1',
    description='Python pipeline for evented multidimensional data processing',
    author='Eric Bruning',
    author_email='eric.bruning@gmail.com',
    url='https://github.com/deeplycloudy/stormdrain/',
    package_dir={'stormdrain': ''}, # wouldn't be necessary if we reorganized to traditional package layout with stormdrain at the same directory level as the setup.py script.
    packages=['stormdrain', 
        'stormdrain.support', 
        'stormdrain.support.matplotlib', 
        'stormdrain.support.coords'],
    )