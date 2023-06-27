import ddb_single
from setuptools import setup

with open("readme.md", "r") as fp:
    LONG_DESCRIPTION = fp.read()

with open("requirements.txt", "r") as fp:
    INSTALL_REQUIRES = fp.read().splitlines()


setup(
    name="ddb_single",
    version=ddb_single.__version__,
    description="Python DynamoDB interface, specialized in single-table design.",
    url="https://github.com/medaka0213/DynamoDB-SingleTable",
    author="medaka",
    license="MIT",
    keywords="aws dynamodb serverless",
    packages=[
        "ddb_single",
    ],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    install_requires=INSTALL_REQUIRES,
    classifiers=[
        "Programming Language :: Python :: 3.9",
    ],
)
