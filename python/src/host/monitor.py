import re
import socket
from host.command import Command


class MonitorItem:
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

        # Execute command
        out = Command.execute([ self.cmd ], params.split())

        # Is there a regular expression to process the output
        if self.regex != None:
            # Search for the match
            m = re.search(self.regex, out)

            # Assume the first group is the required value
            if m != None and len(m.groups()) > 0:
                out = m.group(self.regex_group)

        # Pusblish the value
        mqtt.publish(topic, out)


class Monitor:
    def __init__(self, config, mqtt):
        if not "mqtt" in config or not "monitors" in config["mqtt"] or mqtt == None:
            # Nothing to monitor and publish
            return

        # Keep reference to mqtt client
        self._mqtt = mqtt

        # Default topic host name to None
        self._topic_host_name = None

        # Read the host name if defined (can be used for string formatting)
        if "topicHostName" in config["mqtt"]:
            self._topic_host_name = config["mqtt"]["topicHostName"]

        # If set to null (or None in python terms) then get the hostname for current device code is running on
        if self._topic_host_name == None:
            self._topic_host_name = socket.gethostname()

        # Create the monitor items from the monitor config
        self._monitors = [MonitorItem(c)
                          for c in config["mqtt"]["monitors"]]

    def tick(self):
        for item in self._monitors:
            item.tick(self._topic_host_name, self._mqtt)
