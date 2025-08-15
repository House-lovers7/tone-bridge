"""
Setup configuration for ToneBridge Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tonebridge",
    version="1.0.0",
    author="ToneBridge Team",
    author_email="sdk@tonebridge.io",
    description="Official Python SDK for ToneBridge API - AI-powered text transformation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tonebridge/python-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/tonebridge/python-sdk/issues",
        "Documentation": "https://docs.tonebridge.io/sdk/python",
        "Source Code": "https://github.com/tonebridge/python-sdk",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.28.0",
        "websocket-client>=1.4.0",
        "typing-extensions>=4.0.0;python_version<'3.8'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "async": [
            "aiohttp>=3.8.0",
            "asyncio>=3.4.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "tonebridge=tonebridge.cli:main",
        ],
    },
    keywords=[
        "tonebridge",
        "api",
        "sdk",
        "nlp",
        "text-transformation",
        "ai",
        "communication",
    ],
)