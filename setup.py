from setuptools import setup

DEV = ["pre-commit", "black", "isort", "flake8"]
DOCS = [
    "sphinx==6.2.1",
    "sphinx_rtd_theme==1.2.2",
    "sphinx-autobuild",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "myst_parser",
]

setup(
    name='Minetester',
    version='0.0.1',
    description='Complex environments based on Minetest.',
    author='EleutherAI',
    author_email='',
    packages=['minetester'],
    install_requires=[
        'gym',
        'numpy',
        'matplotlib',
        'zmq',
        'protobuf==3.20.1',
        'psutil',
    ],
    extras_require={"dev": DEV, "docs": DOCS}
)
