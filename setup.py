import ddb_single
import os
from setuptools import setup

DESCRIPTION = "Python DynamoDB interface, specialized in single-table design."
LONG_DESCRIPTION = DESCRIPTION
if os.path.exists("readme.md"):
    with open("readme.md", "r") as fp:
        LONG_DESCRIPTION = fp.read()

setup(
    name="ddb_single",
    version=ddb_single.__VERSION__,
    description=DESCRIPTION,
    url="https://github.com/medaka0213/DynamoDB-SingleTable",
    author="medaka",
    license="MIT",
    keywords="aws dynamodb serverless",
    packages=[
        "ddb_single",
    ],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    install_requires=["boto3"],
    classifiers=[
        "Programming Language :: Python :: 3.9",
    ],
)
