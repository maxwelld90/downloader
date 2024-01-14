import subprocess

ARCHIVER_EXECUTABLE = '7zz'  # sudo dnf install p7zip p7zip-plugins

def pad_string(input_string, max_length=22):
    if len(input_string) >= max_length:
        return input_string[:max_length - 3] + "..."
    else:
        return input_string + " " * (max_length - len(input_string))

def does_archiver_exist():
    """
    
    """
    if run_archiver(['--help']) == 0:
        return True
    
    return False

def run_archiver(args: list):
    try:
        result = subprocess.run([ARCHIVER_EXECUTABLE] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return -1