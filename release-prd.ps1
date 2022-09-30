pandoc -f markdown -t rst -o readme.rst readme.md
python -m readme_renderer readme.rst -o readme.html

sphinx-apidoc -f -o ./docs_src ./ddb_single
sphinx-build ./docs_src ./docs

python setup.py sdist bdist_wheel
twine upload dist/*

twine upload --repository testpypi dist/*
twine upload --repository pypi dist/*
