import copy
import os

from helpers.dictionary_helper import DictionaryHelper
from helpers.script_helper import ScriptHelper

from points.interval import Interval


class ModulePoint:
    def __init__(self, key, name, value):
        self.key = key
        self.name = name
        self.value = value


class ModuleVariables:
    def __init__(self):
        # These are the variables for this tick of execution (they are cleared for each tick)
        self.payload = {}

        # These are the variables for the specific module
        self.module = {}

        # These are the variables that are persisted between ticks
        self.persited = {}

    # Make a clone of current variables and set module variables
    def clone(self, module_varables):
        cloned = copy.deepcopy(self)
        cloned.module = module_variables
        return cloned


class ModuleData:
    def __init__(self, inputs, outputs, virtuals, variables):
        self.inputs = inputs
        self.outputs = outputs
        self.virtuals = virtuals
        self.variables = variables


class ModuleInstance(Interval):
    def __init__(self, key, module, priority, interval):
        super().__init__(interval)
        self.key = key
        self.module = module
        self.priority = priority
        self.variables = {}


class ScriptManager:
    def __init__(self, io_manager):
        self._modules = []
        self._variables = ModuleVariables()
        self._io_manager = io_manager

    def load_scripts(self, path, script_modules):
        # Make sure path ends with directory separator
        if not path.endswith("/"):
            path += "/"

        # Create script helper
        script_helper = ScriptHelper(path)

        # Load scripts
        for module_config in script_modules:
            # Wrap config in dictionary helper
            module_config = DictionaryHelper(module_config, "module")

            # Get required key
            key = module_config.get_str("key", False)

            # Get required name
            name = module_config.get_str("name", False)

            # Get optional priority
            priority = module_config.get_int(
                "priority", True, default=1000, min_value=1)

            # Get optional interval
            interval = module_config.get_int(
                "interval", True, default=10, min_value=1)

            # Get optional init data
            init_data = module_config.get_any(
                "init", True, default=None)

            # Load the script, it must contain a class with the 'init' and 'tick' methods
            name, module = script_helper.load_class(
                name, None, ["init", "tick"])

            # Only add if matching script module found in file
            if name != None and module != None:
                try:
                    module.init(module, key, init_data)
                except (RuntimeError, TypeError, NameError, ValueError) as error:
                    print(error)

                self._modules.append(ModuleInstance(
                    key, module, priority, interval))

        self._modules.sort(key=self._get_module_priority)

    def tick(self):
        inputs = {}
        outputs = {}
        virtuals = {}

        # If there is an IO manager conver the points
        # to virtual points for this tick
        if self._io_manager != None:
            inputs = {x.key: self._get_input(x) for x in
                      self._io_manager.inputs.values()}
            outputs = {x.key: self._get_output(x) for x in
                       self._io_manager.outputs.values()}
            virtuals = {x.key: self._get_virtual(x) for x in
                        self._io_manager.virtuals.values()}

        for module_instance in self._modules:
            # Do not execute if interval not expired for module
            if not module_instance.interval_expired():
                continue

            # Set the module variables for this call
            self._variables.module = module_instance.variables

            module_data = ModuleData(
                inputs, outputs, virtuals, self._variables)

            try:
                if not module_instance.module.tick(
                        module_instance.module, module_data):
                    # If the module returned false then
                    # don't process any more modules
                    break
            except (RuntimeError, TypeError, NameError, ValueError) as error:
                print(error)

        if self._io_manager != None:
            # Now we need to update the real outputs nad virtuals from any
            # values modified in the scripts
            for output_key in outputs:
                self._io_manager.outputs[output_key].value = outputs[output_key].value

            for virtual_key in virtuals:
                self._io_manager.virtuals[virtual_key].value = virtuals[virtual_key].value

    def _get_module_priority(self, module):
        return module.priority

    def _get_input(self, input):
        return ModulePoint(input.key, input.name, input.value)

    def _get_output(self, output):
        return ModulePoint(output.key, output.name, output.value)

    def _get_virtual(self, virtual):
        return ModulePoint(virtual.key, virtual.name, virtual.value)
