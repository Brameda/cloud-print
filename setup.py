from setuptools import setup, find_packages

setup(
    name='cloudprint',
    description='Google Cloud Print API client',
    version='0.0.1dev',
    author='Mikhail Lukyanchenko',
    author_email='ml@akabos.com',
    url='https://github.com/Brameda/cloud-print',
    packages=find_packages(),
    zip_safe=True,
    install_requires=[
        'requests',
    ],
    tests_require=[
        'nose',
    ],
    entry_points={
        'console_scripts': [
            'cloudprint = cloudprint.cli:main',
        ]
    }
)