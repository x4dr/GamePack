from setuptools import setup

setup(
    name="gamepack",
    version="0.2",
    description="factored out game related stuff from NossiNet",
    url="https://github.com/x4dr/gamepack",
    author="Maric",
    author_email="x4dr@hotmail.com",
    license="GPLv3",
    packages=["gamepack"],
    package_data={"gamepack": ["data/*"]},
    install_requires=[
        "numpy",
        "matplotlib",
        "requests",
        "antlr4-python3-runtime==4.9.2",
    ],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Internal",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
    ],
)
