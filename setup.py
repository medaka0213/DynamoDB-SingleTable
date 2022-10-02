from setuptools import setup
import ddb_single

with open('readme.md', 'r', encoding='utf-8') as fp:
    LONG_DESCRIPTION = fp.read()

setup(
    name='ddb_single',
    version="0.2.2",
    description='Python DynamoDB interface, specialized in single-table design.',
    url='https://github.com/medaka0213/DynamoDB-SingleTable',
    author='medaka',
    license='MIT',
    keywords='aws dynamodb serverless',
    packages=[
        "ddb_single",
    ],
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    install_requires=["boto3"],
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
)