from setuptools import setup, find_packages

setup(
    name="codex",
    version="0.1",
    packages=find_packages(),
    entry_points={"console_scripts": ["codex = codex.cli:main"]},
    install_requires=["click == 7.*"],
)
