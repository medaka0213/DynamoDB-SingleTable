pandoc -f markdown -t rst -o readme.rst readme.md
python -m readme_renderer readme.rst -o readme.html

Copy-Item -Path readme.md -Destination docs_src/readme.md  -Force
sphinx-apidoc -f -o ./docs_src ./ddb_single
sphinx-build ./docs_src ./docs

python setup.py sdist bdist_wheel

twine upload --repository testpypi dist/*
twine upload --repository pypi dist/*
