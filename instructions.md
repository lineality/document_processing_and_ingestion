
# To Use Linters and Formatters
- To activate the flake8 and pylint config files, rename with a . before the name
```
$ python -m black FILENAME.py
$ python -m mypy FILENAME.py
$ python -m pylint FILENAME.py
$ python -m pydocstyle FILENAME.py
$ python -m flake8 FILENAME.py

$ python -m flake8 FILENAME.py --verbose
```

# check python version: (eventually will be upgraded, updated)
```bash
python --version
python3 --version
python3.11 --version
```

# check github branch
```bash
git branch
git status
```

# to build server env:
```bash
python3.11 -m venv env; source env/bin/activate
python3.11 -m pip install --upgrade pip; python3.11 -m pip install -r requirements.txt
python3.11 -m pip install git+https://github.com/psf/black pylint pydocstyle flake8
```
or
```bash
python -m venv env; source env/bin/activate
python -m pip install --upgrade pip; python -m pip install -r requirements.txt
python -m pip install git+https://github.com/psf/black pylint pydocstyle flake8
```

# to run flask server:
```bash
python3.11 src/main.py
```

# to build env for tests: in /local_endpoint_tests/ls
```bash
python -m venv env; source env/bin/activate
python -m pip install --upgrade pip; python3.11 -m pip install -r requirements.txt
```

# to run test-module: (run in a new terminal, also to be run in env) 
- add /local_endpoint_tests/ to your file system 
- (not needed to be inside project repo, safer outside to not need to remove it)
- select file name specifically in req_test.py file, e.g. if you make a new file
```python
source env/bin/activate
python3.11 py_tests/update_test.py
```
or
```python
source env/bin/activate
python3.11 py_tests/post_req_test.py
```

# to evaluate success
1. Look in the uploads_should_be_here folder/directory, see if the uploaded file is there.
2. Look at terminal output. (e.g. 200 OK or error)

# URLs
add '/dt/' before the endpoint name

## For cases where server instance hangs, steps to end a specific port-listening process here.
- https://github.com/lineality/end_sigkill_process_bash_cheatsheet/tree/main


# For inspection: see if your functions work in mongoDB
The:
```
"Embedding save result: {'test chunk upload response': [ObjectId('XXXXXXXXXXXXXXXXXXXXXXXXX')]"
```
in the returned json response can be looked up in collections:embeddings:
```
{text_id: ObjectId('XXXXXXXXXXXXXXXXXXXXXXXX')}
```
The file name can be looked up in collections:recordings uploaded documents as, e.g.:
```
{filename: "FILENAME.txt")}
```
