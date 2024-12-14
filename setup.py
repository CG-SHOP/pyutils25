from pathlib import Path

from setuptools import find_packages
from skbuild_conan import setup


def readme():
    """
    :return: Content of README.md
    """

    with Path("README.md").open() as file:
        return file.read()


setup(  # https://scikit-build.readthedocs.io/en/latest/usage.html#setup-options
    name="cgshop2025_pyutils",
    version="0.0.9",
    author="Dominik Krupke",
    license="LICENSE",
    description="Utilities for verifying solutions of the CG:SHOP 2025 Competition.",
    long_description=readme(),
    long_description_content_type="text/markdown",
    packages=find_packages("src"),  # Include all packages in `./src`.
    package_dir={"": "src"},  # The root for our python package is in `./src`.
    python_requires=">=3.10",  # lowest python version supported.
    install_requires=[  # Python Dependencies
        "matplotlib",
        "numpy",
        "chardet>=4.0.0",
        "networkx>=2.0.0",
        "pydantic>=2.0.0",
    ],
    conan_requirements=["fmt/[>=10.0.0]", "cgal/[>=6.0]"],  # C++ Dependencies
    conan_profile_settings={"compiler.cppstd": 17},
    cmake_minimum_required_version="3.23",
)
