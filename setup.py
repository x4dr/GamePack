from setuptools import setup

setup(
    name="gamepack",
    version="0.1.0",
    description="factored out game related stuff from NossiNet",
    url="https://github.com/x4dr/gamepack",
    author="Maric",
    author_email="x4dr@hotmail.de",
    license="GPLv3",
    packages=["gamepack"],
    install_requires=["numexpr"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Internal",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
    ],
)
