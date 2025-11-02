# setup.py

from setuptools import setup, find_packages

# Load required dependencies from requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='lastcron-sdk',
    version='0.1.0',
    description='SDK for orchestrating Python flows via the LastCron PHP platform.',
    author='AllanBR Creations',
    packages=find_packages(),
    install_requires=required,
    python_requires='>=3.8',
    keywords=['orchestration', 'workflow', 'cron', 'task-management'],
)