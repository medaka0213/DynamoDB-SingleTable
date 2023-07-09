import os
from setuptools import setup

DESCRIPTION = "Python DynamoDB interface, specialized in single-table design."
LONG_DESCRIPTION = DESCRIPTION
if os.path.exists("readme.md"):
    with open("readme.md", "r") as fp:
        LONG_DESCRIPTION = fp.read()

# インポートは延期されるので、この時点では'__version__'はまだ未知です
version = "unknown"
try:
    # インポートはここで行われ、'__version__'が利用可能になります
    import ddb_single

    version = ddb_single.__VERSION__
except Exception:
    pass  # パッケージがまだインストールされていない場合に備えて例外を無視します


setup(
    name="ddb_single",
    version=version,
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
