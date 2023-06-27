import os
from setuptools import setup
import ddb_single

with open("readme.md", "r") as fp:
    LONG_DESCRIPTION = fp.read()

with open("requirements.txt", "r") as fp:
    INSTALL_REQUIRES = fp.read().splitlines()

RELEASE_VERSION = (
    os.environ.get("RELEASE_VERSION", "").split("/")[-1].replace("v", "") or "0.0.0"
)

setup(
    name="ddb_single",
    version=RELEASE_VERSION,
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
