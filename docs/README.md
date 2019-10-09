
## Usage
For generating the documents locally, use commands below from the root folder. 

```shell
# install dependencies
pip install Sphinx sphinxcontrib-fulltoc sphinx_bootstrap_theme

# generate rst files for ladybug modules except for euclid
sphinx-apidoc -f -e -d 4 -o ./docs ./ladybug ./ladybug/euclid.py

# build the documentation under _build/docs folder
sphinx-build -b html ./docs ./docs/_build/docs
```
