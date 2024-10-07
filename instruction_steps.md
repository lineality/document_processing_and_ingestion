# On Document Processing and Ingestions Steps

In most cases the document processing-and-ingestion pipeline has two steps (or stages) using, respectively, two program files:

### The Smart Chunking (document processing) phase uses:
1. smart_chunk.py

### The Batch Ingestion phase uses:
2. batch_ingest.py


### First you will need a 'setup' including:
1. a python environment.
2. environment variable files, to safely handle user and login information, etc.
3. the requirement.txt file (for the python environment)

You can either try to run each phase in a separate environment, or try to run them together.


#### To build your python environment:
Assuming you have python etc. installed, run these three lines in your terminal:
```bash
python -m venv env; source env/bin/activate
python -m pip install --upgrade pip; python -m pip install -r requirements.txt
python -m pip install git+https://github.com/psf/black pylint pydocstyle flake8
```

# Part I

#### Document Processing
When you have your python environment running,
put your source-documents in a directory called "target_files"

Run the document processor with something like this line.
Note: if the file has a version number in the name, either call that name 'smart_chunk_v89.py' or remove the number to call a standard name 'smart_chunk.py'

Run ~this in a terminal: (see above comment about exact file names)
```bash
python smart_chunk.py
```

This will produce a txt_pool directory and document-specific directories. the txt_pool directory ~should have all the files copied into it already.

Note: 
pdf files, a printer-format, not a text-format, are notoriously unreliable for accurately containing text characters (though PDF is excellent for showing an accurate picture of the text), and for being non-standard in how the file should be read at all. There are three possible PDF readers built into the smart chunker, but if one crashes or freezes you will need to turn that one off and try again. And sometimes a PDF simply contains no text to extract, you will need a new document.

# Part II

You can ingest files in one batch or in parallel batches. The ingestion software will log any errors that occur so you can retry those files. The software will attempt to retry by itself which so far has always worked.

As above, make sure you are in a python environment, 

create directories with names like:
- bulk_files_folder_1
- bulk_files_folder_2

put your chunks into those directories. e.g. copy perhaps 100-300 files into each folder from the original txt_pool folder. I recommend making an archive of the original txt_pool for various reasons.

For this step you will need a .env and .tools_env set up depending on your system.

open a separate terminal for each parallel batch (e.g. for each bulk_files directory)

Run batch_ingest with something like this line.
Note: if the file has a version number in the name, either call that name 'batch_ingest_v98.py' or remove the number to call a standard name batch_ingest.py'

Note: you should enter the number of the bulk_files_folder_THIS-NUMBER when you run the software:
```bash
python batch_ingest_v11.py NUMBER_HERE
```

recommended steps (also in the .py file) 
#### Steps:
0. do a demo test in a test database first
1. make your bulk_files_folder_{NUMBER_HERE} directories in cwd
2. make your .tools_env and .env (set correct URL and USER info)
3. make your venv env
4. (per NUMBER_HERE bulk directory) open terminal in cwd
5. use venv env: $ source env/bin/activate
6. start run: $ python batch_ingest_v11.py NUMBER_HERE
7. double check the configuration print and hit enter to run
8. check for status:200 in first few results
9. check results and look for missed-file reports (note: retry will be attempted)
10. test your system to make sure ingestion worked
