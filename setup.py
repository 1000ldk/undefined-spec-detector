from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="undefined-spec-detector",
    version="0.1.0",
    author="AI System Architect",
    description="自然言語で書かれた要件や仕様から未定義要素を検出するツール",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "spacy>=3.7.0",
        "ja-ginza>=5.1.0",
        "fugashi>=1.3.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "usd-cli=usd.cli:main",
        ],
    },
)


