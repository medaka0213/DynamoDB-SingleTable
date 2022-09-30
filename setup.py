from setuptools import setup
import ddb_single

setup(
    name='ddb_single',
    version=ddb_single.__version__,
    description='Python DynamoDB interface, specialized in single-table design.',
    url='https://github.com/medaka0213/DynamoDB-SingleTable',
    author='medaka',
    license='MIT',
    keywords='aws dynamodb serverless',
    packages=[
        "ddb_single",
    ],
    install_requires=["boto3"],
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
)