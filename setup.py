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
)