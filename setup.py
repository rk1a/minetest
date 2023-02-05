from setuptools import setup

setup(
    name='Minetests',
    version='0.0.1',
    description='Complex environments based on Minetest.',
    author='EleutherAI',
    author_email='',
    packages=['minetests'],
    install_requires=[
        'gym',
        'numpy',
        'matplotlib',
        'zmq',
    ],
)
