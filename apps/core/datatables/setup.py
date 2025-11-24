"""
Setup configuration for django-datatables-server package.

A Django REST Framework package for server-side DataTable processing
with pagination, sorting, filtering, and export capabilities.

PRINCIPES:
- SOLID : Architecture modulaire et extensible
- KISS : Simplicité et facilité d'utilisation
- DRY : Réutilisation maximale du code
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README_PYPI.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version from __init__.py
version_file = Path(__file__).parent / "__init__.py"
version = "1.0.0"
if version_file.exists():
    for line in version_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

setup(
    name="django-datatables-server",
    version=version,
    author="InventaireModuleWMS Team",
    author_email="",
    description="Django REST Framework package for server-side DataTable processing with SOLID architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/InventaireModuleWMS/django-datatables-server",
    packages=find_packages(where=".", exclude=["tests", "tests.*", "*.tests", "*.tests.*", "__pycache__"]),
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=4.0,<6.0",
        "djangorestframework>=3.12.0",
        "django-filter>=2.0.0",
        "openpyxl>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-django>=4.5.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="django, rest-framework, datatable, pagination, filtering, sorting, export, solid, kiss, dry",
    project_urls={
        "Bug Reports": "https://github.com/InventaireModuleWMS/django-datatables-server/issues",
        "Source": "https://github.com/InventaireModuleWMS/django-datatables-server",
        "Documentation": "https://github.com/InventaireModuleWMS/django-datatables-server/blob/main/README.md",
    },
)

