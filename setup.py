from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="bo2-emblem-studio",
    version="1.0.0",
    author="BO2 Emblem Studio",
    author_email="",
    description="Complete toolkit for BO2/Plutonium T6 emblem editing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bo2-emblem-studio",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "gui": ["PySide6>=6.4.0"],
        "dev": ["pytest>=7.0", "black", "mypy"],
    },
    entry_points={
        "console_scripts": [
            "bo2-emblem-studio=bo2_emblem.gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "bo2_emblem": ["database/*.json"],
    },
)