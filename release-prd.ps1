pandoc -f markdown -t rst -o readme.rst readme.md
pandoc -f markdown -t html -o readme.html readme.md

Copy-Item -Path readme.md -Destination docs_src/readme.md  -Force
sphinx-apidoc -f -o ./docs_src ./ddb_single
sphinx-build ./docs_src ./docs

python setup.py sdist bdist_wheel
twine upload --repository testpypi dist/*
twine upload --repository pypi dist/*
