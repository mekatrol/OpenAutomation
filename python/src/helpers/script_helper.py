from importlib import util
import inspect
import os


class ScriptHelper:
    def __init__(self, script_path):
        if not script_path.endswith("/"):
            script_path += "/"

        self.script_path = script_path

    def load_class(self, file_name, class_name, required_methods=None):
        # Get module name from file name
        module_name = os.path.splitext(file_name)[0]

        # Get full path name 
        full_path = self.script_path + file_name

        # Can't load module if file does not exist
        if not os.path.isfile(full_path):
            return None, None

        # Build import spec
        spec = util.spec_from_file_location(
            module_name, self.script_path + file_name)

        # Load the module
        module = util.module_from_spec(spec)

        # Execute module loading
        spec.loader.exec_module(module)

        # Iterate members
        for name, obj in inspect.getmembers(module):
            # Looking for a class (with matching calss name if specified)
            if inspect.isclass(obj) and (class_name == None or name == class_name):

                if required_methods != None:

                    # Get methods of the class
                    methods = dict((name, func) for name, func
                                   in inspect.getmembers(obj))

                    # Get all method names set
                    all_methods_set = set(methods.keys())

                    # Get required method names set
                    required_methods_set = set(required_methods)

                    # Make sure that the required names are in all names
                    if not required_methods_set.issubset(all_methods_set):
                        continue

                    return name, obj

        # Nothing found
        return None, None
