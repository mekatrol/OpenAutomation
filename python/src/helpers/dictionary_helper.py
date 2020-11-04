class DictionaryHelper:
    def __init__(self, instance, name):
        self._dict = instance
        self._name = name

    def has_config_section(self, name):
        return name in self._dict

    def get_config_section(self, name):
        if not self.has_config_section(name):
            return None

        return DictionaryHelper(self._dict[name], name)

    def get_any(self, property_name, optional=True, default=None):
        if not property_name in self._dict:

            # If optional then just return default
            if optional:
                return default

            raise Exception(
                f"'{property_name}' property must be defined for all '{self._name}' value")

        return self._dict[property_name]

    def get_int(self, property_name, optional=True, default=None, min_value=None, max_value=None):
        if not property_name in self._dict:

            # If optional then just return default
            if optional:
                return default

            raise Exception(
                f"'{property_name}' property must be defined for all '{self._name}' value")

        property_value = self._dict[property_name]

        # Must have a value if not optional
        if property_value == None and not optional:
            raise Exception(
                f"'{property_name}' property value must be set for all '{self._name}' value")

        # Value must be a valid integer value
        if property_value != None and not isinstance(property_value, int):
            raise Exception(
                f"{property_name} property must be a valid integer value for {self._name}")

        # Must be >= min_value if defined
        if min_value != None and (not property_value or property_value < min_value):
            raise Exception(
                f"{property_name} property value must be >= {min_value} for {self._name}")

        # Must be <= max_value if defined
        if max_value != None and (not property_value or property_value > max_value):
            raise Exception(
                f"{property_name} property value must be <= {max_value} for {self._name}")

        # Return validated value
        return property_value

    def get_bool(self, property_name, optional=True, default=None):
        if not property_name in self._dict:

            # If optional then just return default
            if optional:
                return default

            raise Exception(
                f"'{property_name}' property must be defined for all '{self._name}' value")

        property_value = self._dict[property_name]

        # Must have a value if not optional
        if property_value == None and not optional:
            raise Exception(
                f"'{property_name}' property value must be set for all '{self._name}' value")

        # Value must be a valid bool value
        if property_value != None and not isinstance(property_value, bool):
            raise Exception(
                f"{property_name} property must be a valid bool value for {self._name}")

        # Return validated value
        return property_value

    def get_float(self, property_name, optional=True, default=None, min_value=None, max_value=None):
        if not property_name in self._dict:

            # If optional then just return default
            if optional:
                return default

            raise Exception(
                f"'{property_name}' property must be defined for all '{self._name}' value")

        property_value = self._dict[property_name]

        # Must have a value if not optional
        if property_value == None and not optional:
            raise Exception(
                f"'{property_name}' property value must be set for all '{self._name}' value")

        # Value must be a valid float value
        if property_value != None and not isinstance(property_value, float):
            raise Exception(
                f"{property_name} property must be a valid integer value for {self._name}")

        # Must be >= min_value if defined
        if min_value != None and (not property_value or property_value < min_value):
            raise Exception(
                f"{property_name} property value must be >= {min_value} for {self._name}")

        # Must be <= max_value if defined
        if max_value != None and (not property_value or property_value > max_value):
            raise Exception(
                f"{property_name} property value must be <= {max_value} for {self._name}")

        # Return validated value
        return property_value

    def get_str(self, property_name, optional=True, default=None):
        if not property_name in self._dict:

            # If optional then just return default
            if optional:
                return default

            raise Exception(
                f"'{property_name}' property must be defined for '{self._name}'")

        # Get the value
        property_value = self._dict[property_name]

        # If the property is not optional then it must have a value
        if not optional and (property_value == None or not property_value):
            raise Exception(
                f"'{property_name}' property value must be defined for '{self._name}' (cannot be null or empty)")

        # If there is a property value then it must be a string type
        if property_value and type(property_value) != str:
            raise Exception(
                "Shift register 'key' property must be a valid string value")

        # Return validated value
        return property_value
