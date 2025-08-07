copilot/fix-63aa93a4-72a5-471a-a5ef-b3c5a75cd0ff
from setuptools import setup, find_packages

setup(
    name="meta-trader-bot",
    version="1.0.0",
    description="KAIZEN - Advanced Trading Bot with Trap Analysis and Risk Management",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "scipy>=1.7.0",
        "ta>=0.10.0",
        "python-dotenv>=0.19.0",
        "dataclasses>=0.6",
        "typing-extensions>=4.0.0",
    ],
    python_requires=">=3.8",

"""
Setup configuration for Meta Trading Bot
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="meta-trading-bot",
    version="1.0.0",
    author="Trading Bot Team",
    description="Advanced Meta Trading Bot with trap identification and risk management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "meta-trading-bot=run_bot:main",
        ],
    },
    include_package_data=True,
main
)