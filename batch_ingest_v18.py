"""
Bulk/Batch File Ingestion w/ Error Reporting
- can work with 'smart_chunk.py' program to make the chunks from a source file
- requires .env file
- require .tools_env file

Steps:
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


Tip: 
run this in parallel terminals
on sets of the overall files
then re-try the error files

This is set in the .env file:
#------------ bulk_file_ingestion -----------------#
URL_FOR_BULK_FILE_INGESTION = f"http://localhost:{endpoint_name}"

1. put the target_file_folder and this file in the cwd
- "bulk_files_folder_{n}"

2. open as many terminal (in env) that you want:

2. in each terminal run pointing to a batch folder:
```bash
python batch_ingest.py 1
```
or
```bash
python batch_ingest.py NUMBER_HERE
```
Where NUMBER_HERE is the batch-directory you want to load.

3. program will Upload ALL files in folder: "bulk_files_folder_{n}"
- batch upload
- pauses between operations
- log report of errors

4. run all terminal at once, in parallel (don't wait for the last to stop)

5. check for error logs:
- e.g. "failed_ingestion_doc_log_20040814_124602.txt"

6. re-run on the missed files
- put the files that were missed (see report for name) in a new folder and try again
- in the past this always worked on the 2nd try



select url and files directory below
to send as a post-request to a file-uploader endpoint


tip: make unique file name for easier checking in mongoDB
Note: do not put a directory in the file folder, only doc files

Note: This is designed for a file-upload endpoint.
a very similar variation can work with a text-string input endpoint.

Note: The details of how each endpoint recieves what will need to be 
adjusted to.

TODO:
A future version could use async to parallelize...but that might make logging an issue?

"""

SLEEP_TIME = 2

################################
# User data comes from toolsenv
################################
import time
import os
import glob
import sys
from datetime import datetime
from dotenv import load_dotenv
import requests
import jwt

load_dotenv()

# Get the current working directory.
cwd = os.getcwd()

URL_FOR_BULK_FILE_INGESTION = os.getenv("URL_FOR_BULK_FILE_INGESTION")

# preset/reset
status_code = None
failed_files_to_rety_list = []
batch_number = None

###############
# select batch
###############
# sys.argv is a list in Python, which contains the command-line arguments passed to the script.
# sys.argv[0] is the name of the script itself.
# sys.argv[1] is the first argument, and so on.


if len(sys.argv) > 1:
    batch_number = int(sys.argv[1])
    print(f"Processing batch: {batch_number}")
else:
    batch_number = None
    print(f"No batch number provided: {batch_number}")
    batch_number = input("")

try:
    if isinstance(batch_number, str):
        batch_number = int(batch_number)
    elif isinstance(batch_number, int):
        print(f"batch number ok: {batch_number}")
    else:
        print(f"batch number type problem: please fix. type -> {type(batch_number)}")
        sys.exit()

except Exception as e:
    raise e
    # sys.exit()


THIS_BATCH = batch_number


target_file_folder_name = f"bulk_files_folder_{THIS_BATCH}"


# Define the path to the 'docs' directory.
docs_directory = os.path.join(cwd, target_file_folder_name)

# Use glob to get all the files from the 'docs' directory.
list_of_file_paths = glob.glob(os.path.join(docs_directory, "*"))

# Print the list of files.
for this_file_path in list_of_file_paths:
    print(this_file_path, "\n")


##########
# dev_env
##########
def is_in_gitignore(ignore_this):
    """
    Checks if something is included in the local .gitignore file or any parent .gitignore files.

    Returns:
        bool: True if the specified file or directory is ignored, False otherwise.

    requires:
        import os
    """
    current_dir = os.getcwd()
    while True:
        # # inspection
        # print(f"current_dir -> {current_dir}")
        gitignore_file = os.path.join(current_dir, ".gitignore")
        if os.path.exists(gitignore_file):
            with open(gitignore_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line == ignore_this:
                        # # inspection
                        # print("item found in env, OK!")
                        return True

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir

    return False


def get_from__tools_env(field_name, env_name=".tools_env"):
    """
    Reads a value from a '.tools_env' file in the current working directory.

    Args:
        field_name (str): The name of the field to retrieve.

    Returns:
        str: The value of the specified field, or None if the field is not found.

    Record your quasi-environment-variables in .tools_env
    these are not OS-level environement variables,
    but project secrets not saved to git.
    e.g. .tools_env is in git-ignore
    no spaces, no quotes
    field_name=value_string
    """

    if is_in_gitignore(env_name):
        pass
    else:
        input(
            f"Warning, Halted, {env_name} not in local .gitignore; press return to proceed, or ctrl c to exit"
        )
        return None

    try:
        env_file = os.path.join(os.getcwd(), env_name)

        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith(f"{field_name}="):
                        return line.split("=")[1].strip()

    except Exception as e:
        print(f"It's The Error -> {str(e)}")
        return None

    return None


def get_user_data_from_toolsenv():
    """
    return either
    - both id and email for user
    or
    - None
    """

    user_id_string = get_from__tools_env("user_id_string")
    email_string = get_from__tools_env("email_string")

    the_return_tuple = (user_id_string, email_string)

    if len(the_return_tuple) == 2:
        return the_return_tuple

    else:
        return None


# get user id data from .tools_env
user_secrets_tuple = get_user_data_from_toolsenv()

# if tools_env was use-able, overwrite with data from toolsenv
if user_secrets_tuple:
    try:
        user_id_string = user_secrets_tuple[0]
        email_string = user_secrets_tuple[1]
        print(f"OK! Data obtained from tools_env")

    except Exception as e:
        print(f"error geting tools_env data -> {str(e)}")
        sys.exit()


##############
# Setup Token
##############

token = jwt.encode(
    payload={
        "id": user_id_string,
        "email": email_string,
        "language": "en",
        "iat": int(time.time()),
    },
    key=os.getenv("JWT_SECRET_KEY"),
    algorithm="HS256",
)

print(f"token ->")
print(token)

start_time_outer = time.monotonic()

# preset/reset variables
main_counter = 1
success_counter = 0
fail_counter = 0
total_counter = 0
failed_doc_log = []

print(f"\n{len(list_of_file_paths)} files to upload.")  # iterate and upload


# select endpoint,
endpoint_name = "user-document-ingestion"


#########################################
# whole_url = base(from .env) + endpoint
#########################################
whole_url = URL_FOR_BULK_FILE_INGESTION + endpoint_name

# inspection
print(f"\nendpoint_name -> {endpoint_name}")
print(f"whole_url -> {whole_url}")
print(f"user_id_string -> {user_id_string}")
print(f"email_string -> {email_string}")
print(f"target_file_folder_name -> {target_file_folder_name}\n")


# # use to pause, inspect
input("Breakpoint: Ready the start? Press for the Return (or ctrl c to exit)")


#############
# First Pass
#############

# iterate through files
for this_file_path in list_of_file_paths:

    print(f"\n\nNext doc...{main_counter}/{len(list_of_file_paths)}")

    # pause between uploads
    time.sleep(SLEEP_TIME)

    # path to the file you want to upload,
    # e.g. file_path = 'path/to/your/file.txt'

    # get file name
    filename = os.path.basename(this_file_path)

    # inspection
    print(f"endpoint_name -> {endpoint_name}")
    print(f"user_id_string -> {user_id_string}")
    print(f"filename -> {filename}")
    print(f"email_string -> {email_string}")

    # start debug timer
    start_time_inner = time.monotonic()

    # Prepare the file in the correct format for uploading
    # file_bytes = {'file': open(file_path, 'rb')}
    with open(this_file_path, "rb") as file:

        # # use to pause, inspect
        # input("breakpoint")

        file_bytes = {"file": file}

        # Convert JSON data to a string and include it in the form data
        form_data = {"file": file_bytes["file"]}

        headers = {"Authorization": "Bearer " + token}

        # Send the POST request to the server's file upload endpoint
        try:
            response_object = requests.post(
                whole_url,
                files=form_data,
                headers=headers,
                timeout=10000,
            )
            # Print the server's response
            status_code = response_object.status_code
            reply_text = response_object.text
            print(reply_text, status_code)


            #############
            # log errors
            #############
            # check for any 2nn status code
            if status_code // 100 == 2:
                success_counter += 1
                total_counter += 1

            else:
                fail_counter += 1
                total_counter += 1

                logg = f"Failed on this_file_path->'{os.path.basename(this_file_path)}', status_code->{status_code}"
                failed_doc_log.append(logg)

                # Add the failed file to the list of failed files
                failed_files_to_rety_list.append(this_file_path)            

            
                blurb = f"\nFailed: not a 200 or 2nn status code. status code -> {status_code}"
                print(blurb)
            
            if status_code is None:
                blurb = "\nFail & Exit: Probably Unable to connect to server (or local server not running). (in try)"
                print(blurb)
                logg = blurb
                failed_doc_log.append(logg)
                sys.exit()

                # Add the failed file to the list of failed files
                failed_files_to_rety_list.append(this_file_path)
        
        except requests.exceptions.RequestException as e:
            if status_code is None:
                blurb = "\nFail & Exit: Probably Unable to connect to server (or local server not running). (in try)"
                print(blurb)
                logg = blurb
                failed_doc_log.append(logg)
                sys.exit()

            blurb = f"except Error in python frontend request ->  {e}"
            logg = f"Failed on this_file_path->'{os.path.basename(this_file_path)}', status_code->{status_code}, {blurb}"
            failed_doc_log.append(logg)
            fail_counter += 1
            total_counter += 1

            # Add the failed file to the list of failed files
            failed_files_to_rety_list.append(this_file_path)

        finally:
            main_counter += 1

    end_time_inner = time.monotonic()
    elapsed_time = end_time_inner - start_time_inner
    print(f"Tester-FrontEnd Inner Elapsed time: {elapsed_time} seconds")

end_time_outer = time.monotonic()
elapsed_time = end_time_outer - start_time_outer
print(f"Tester-FrontEnd Outer Elapsed time (all docs time): {elapsed_time} seconds")

# prints the logs (be an advocate! spread the word!)
print(f"failed_doc_log -> {failed_doc_log}")

# add url to log
blurb = f"{len(failed_doc_log)} error(s) logged."
print(blurb)

# text for report
counter_blurb = f"""
success_counter = {success_counter}
fail_counter    = {fail_counter}

total_counter   = {total_counter}
"""
print(counter_blurb)
print(whole_url)

# save log IF the there is an error message
if failed_doc_log:

    failed_doc_log.append(whole_url)
    failed_doc_log.append(blurb)
    failed_doc_log.append(counter_blurb)

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # save the loggs (entangered species!)
    with open(f"failed_ingestion_doc_log_{timestamp}.txt", "w") as file:
        for item in failed_doc_log:
            file.write(item + "\n\n")

    print("\n\nError log printed; pick up your copy today.")

else:
    print("\n\nNo errors to log. OK OK!\n\n")


#############
#############
# Retry Pass
#############
#############

# preset/reset
main_counter = 1

print(f"failed_files_to_rety_list -> {failed_files_to_rety_list}")
print(f"len failed_files_to_rety_list -> {len(failed_files_to_rety_list)}")
if failed_files_to_rety_list:
    for this_error_item in failed_files_to_rety_list:
        print(this_error_item)
print("\n\n Starting 2nd retry pass")

retry_counter = 0

# After the main loop, retry the failed files
while failed_files_to_rety_list:
    retry_counter += 1
    print(
        f"\nRetrying {len(failed_files_to_rety_list)} failed files... retry_counter={retry_counter}"
    )

    # iterate through files
    for this_file_path in failed_files_to_rety_list:

        print(f"\n\nNext (retry) doc...{main_counter}/{len(list_of_file_paths)}")

        # pause between uploads
        time.sleep(SLEEP_TIME)

        # path to the file you want to upload,
        # e.g. file_path = 'path/to/your/file.txt'

        # get file name
        filename = os.path.basename(this_file_path)

        # inspection
        print(f"endpoint_name -> {endpoint_name}")
        print(f"user_id_string -> {user_id_string}")
        print(f"filename -> {filename}")
        print(f"email_string -> {email_string}")

        # start debug timer
        start_time_inner = time.monotonic()

        # Prepare the file in the correct format for uploading
        # file_bytes = {'file': open(file_path, 'rb')}
        with open(this_file_path, "rb") as file:

            # # use to pause, inspect
            # input("breakpoint")

            file_bytes = {"file": file}

            # Convert JSON data to a string and include it in the form data
            form_data = {"file": file_bytes["file"]}

            headers = {"Authorization": "Bearer " + token}

            # Send the POST request to the server's file upload endpoint
            try:
                response_object = requests.post(
                    whole_url,
                    files=form_data,
                    headers=headers,
                    timeout=10000,
                )
                # Print the server's response
                status_code = response_object.status_code
                reply_text = response_object.text
                print(reply_text, status_code)
                
                ###
                # log errors
                ###
                # check for any 2nn status code
                if status_code // 100 == 2:
                    success_counter += 1
                    total_counter += 1

                    # remove item from fail-list (pop uses index, remove uses value)
                    failed_files_to_rety_list.remove(this_file_path)

                else:
                    fail_counter += 1
                    total_counter += 1

                    logg = f"Failed on this_file_path->'{os.path.basename(this_file_path)}', status_code->{status_code}"
                    failed_doc_log.append(logg)

                if status_code is None:
                    blurb = "\nFail & Exit: Probably Unable to connect to server (or local server not running). (in try)"
                    print(blurb)
                    logg = blurb
                    failed_doc_log.append(logg)
                    sys.exit()

            except requests.exceptions.RequestException as e:
                if status_code is None:
                    blurb = "\nFail & Exit: Probably Unable to connect to server (or local server not running). (in try)"
                    print(blurb)
                    logg = blurb
                    failed_doc_log.append(logg)
                    sys.exit()

                blurb = f"except Error in python frontend request ->  {e}"
                logg = f"Failed on this_file_path->'{os.path.basename(this_file_path)}', status_code->{status_code}, {blurb}"
                failed_doc_log.append(logg)
                fail_counter += 1
                total_counter += 1

                # Add the failed file to the list of failed files
                failed_files_to_rety_list.append(this_file_path)

            finally:
                main_counter += 1

        end_time_inner = time.monotonic()
        elapsed_time = end_time_inner - start_time_inner
        print(f"Tester-FrontEnd Inner Elapsed time: {elapsed_time} seconds")

    end_time_outer = time.monotonic()
    elapsed_time = end_time_outer - start_time_outer
    print(f"Tester-FrontEnd Outer Elapsed time (all docs time): {elapsed_time} seconds")

    # prints the logs (be an advocate! spread the word!)
    print(f"failed_doc_log -> {failed_doc_log}")

    # add url to log
    blurb = f"{len(failed_doc_log)} error(s) logged."
    print(blurb)

    # text for report
    counter_blurb = f"""
    success_counter = {success_counter}
    fail_counter    = {fail_counter}

    total_counter   = {total_counter}
    """
    print(counter_blurb)
    print(whole_url)

    # save log IF the there is an error message
    if failed_doc_log:

        failed_doc_log.append(whole_url)
        failed_doc_log.append(blurb)
        failed_doc_log.append(counter_blurb)

        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # save the loggs (entangered species!)
        with open(f"failed_ingestion_doc_log_{timestamp}.txt", "w") as file:
            for item in failed_doc_log:
                file.write(item + "\n\n")

        print("\n\nError log printed; pick up your copy today.")

    else:
        print("\n\nNo errors to log. OK OK!\n\n")

########
# Final
########


end_time_outer = time.monotonic()
elapsed_time = end_time_outer - start_time_outer
print(f"Tester-FrontEnd Outer Elapsed time (all docs time): {elapsed_time} seconds")

# prints the logs (be an advocate! spread the word!)
print(f"failed_doc_log -> {failed_doc_log}")

# add url to log
blurb = f"{len(failed_doc_log)} error(s) logged."
print(blurb)

# text for report
counter_blurb = f"""
success_counter = {success_counter}
fail_counter    = {fail_counter}

total_counter   = {total_counter}
"""
print(counter_blurb)
print(whole_url)

# save log IF the there is an error message
if failed_doc_log:

    failed_doc_log.append(whole_url)
    failed_doc_log.append(blurb)
    failed_doc_log.append(counter_blurb)

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # save the loggs (entangered species!)
    with open(f"failed_ingestion_doc_log_{timestamp}.txt", "w") as file:
        for item in failed_doc_log:
            file.write(item + "\n\n")

    print("\n\nError log printed; pick up your copy today.")

else:
    print("\n\nNo errors to log. OK OK!\n\n")


print(f"Final: retry_counter -> {retry_counter}")
print(f"Final: failed_files_to_rety_list -> {failed_files_to_rety_list}")
