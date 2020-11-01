import importlib
import inspect
import os


class ScriptHelper:
    def __init__(self, script_path):
        if not script_path.endswith("/"):
            script_path += "/"

        self.script_path = script_path

    def load_class(self, file_name_with_path, class_name, required_methods=None):
        # Get file name and module name from full path
        file_name = os.path.basename(file_name_with_path)
        module_name = os.path.splitext(file_name)[0]

        # Build import spec
        spec = importlib.util.spec_from_file_location(
            module_name, self.script_path + file_name)

        # Load the module
        module = importlib.util.module_from_spec(spec)

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
