import json
import re
from helpers.command_helper import CommandHelper
from devices.one_wire import OneWire


class Monitor:
    def __init__(self, config):
        self.name = None
        if "name" in config:
            self.name = config["name"]

        self.cmd = None
        if "cmd" in config:
            self.cmd = config["cmd"]

        self.params = None
        if "params" in config:
            self.params = config["params"]

        self.topic = None
        if "topic" in config:
            self.topic = config["topic"]

        self.interval = None
        if "interval" in config:
            self.interval = config["interval"]

        self.regex = None
        self.regex_group = 1
        if "regex" in config:
            self.regex = config["regex"]
            if "regexGroup" in config:
                self.regex_group = config["regexGroup"]

        self._count_down = self.interval

    def tick(self, topic_host_name, mqtt):
        # Use interval if defined
        if self.interval != None:
            # Decrement count down
            self._count_down -= 1

            # Count down not reached zero (interval incomplete)?
            if self._count_down > 0:
                return

            # Reset countdown from interval
            self._count_down = self.interval

        if self.cmd == None:
            # No command then nothing to do
            return

        # Construct params from tempalate
        params = self.params
        if params != None:
            params = params.format(name=self.name)
        else:
            params = ""

        # Construct topic from template
        topic = self.topic
        if topic == None:
            # No topic then no publish end point
            return

        # Format the topic using any defined parameters
        topic = topic.format(name=self.name, topicHostName=topic_host_name)

        # Is this an internal command?
        if "[internal]" == self.cmd:
            return self.__internal_command(params, topic, mqtt)

        # Execute command
        out = CommandHelper.execute([self.cmd], params.split())

        # Is there a regular expression to process the output
        if self.regex != None:
            # Search for the match
            m = re.search(self.regex, out)

            # Assume the first group is the required value
            if m != None and len(m.groups()) > 0:
                out = m.group(self.regex_group)

        # Pusblish the value
        mqtt.publish(topic, out)

    def __internal_command(self, params, topic, mqtt):
        if params == None or len(params) == 0 or mqtt == None:
            raise Exception("Missing params or mqtt")

        # Split params in to parts
        param_parts = params.split()

        if param_parts[0] == "diskusage":
            # For disk usage params should be something like 'diskusage /'
            path = "/"
            if len(param_parts) > 1:
                path = param_parts[1]

            total, used, free = CommandHelper.disk_usage(path)

            payload = {
                "path": path,
                "total": total,
                "used": used,
                "free": free
            }

            # Pusblish the value
            mqtt.publish(topic, json.dumps(payload))

        if param_parts[0] == "onewire":
            device_name = param_parts[1]
            temp = OneWire.read_temp(device_name)

            # Pusblish the value
            mqtt.publish(topic, temp)


class HostController:
    def __init__(self, config, mqtt, topic_host_name):
        if not "io" in config or not "monitors" in config["io"] or mqtt == None:
            # Nothing to monitor and publish
            return

        # Keep reference to mqtt client
        self._mqtt = mqtt

        # Keep topic host name
        self._topic_host_name = topic_host_name

        # Create the monitor items from the monitor config
        self._monitors = [Monitor(c)
                          for c in config["io"]["monitors"]]

    def tick(self):
        for item in self._monitors:
            item.tick(self._topic_host_name, self._mqtt)
