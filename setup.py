from setuptools import setup, find_packages

setup(
    name="llm-machine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "rich>=13.7.0",
        "pyyaml>=6.0",
        "prompt-toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "llm-machine=src.main:main",
        ],
    },
    python_requires=">=3.10",
)
