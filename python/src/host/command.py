import re
import shutil
from subprocess import check_output, CalledProcessError

class Command:
    def __init__(self):
        return

    @staticmethod
    def execute(cmd, params):
        # Concat params to cmd if defined
        if params != None and len(params) > 0:
            cmd = cmd + params

        # Execute command (with optional params)
        # Convert output to UTF8
        out = check_output(cmd).decode('utf-8')

        # Return the output
        return out

    @staticmethod
    def disk_usage(path):
        total, used, free = shutil.disk_usage(path)
        return total, used, free
        