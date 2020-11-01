import importlib
import inspect
import os


class ScriptHelper:
    def __init__(self, script_path):
        if not script_path.endswith("/"):
            script_path += "/"

        self.script_path = script_path

    def load_class(self, file_name_with_path, class_name):
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

                # Get methods of the class
                methods = dict((name, func) for name, func
                               in inspect.getmembers(obj))

                # The init and tick methods are mandatory
                if not "tick" in methods or not "init" in methods:
                    continue

                args, varargs, keywords, defaults = inspect.getargspec(
                    methods['tick'])

                # init method needs to have two args, self and data
                if (not args or "self" not in args or "data" not in args):
                    continue

                return name, obj

        # Nothing found
        return None, None
