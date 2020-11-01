class IoPoint:
    def __init__(self, key, name, description, value, topic, interval):
        self.key = key
        self.name = name
        self.description = description
        self.topic = topic
        self.interval = interval
        self.value = value

        # Init count down to interval
        self._count_down = self.interval

    def interval_expired(self):
        # If there is not interval then it has expired
        if self.interval == None:
            return True

        # Decrement count down
        self._count_down -= 1

        # Count down not reached zero (interval incomplete)?
        if self._count_down > 0:
            return False

        # Reset countdown from interval
        self._count_down = self.interval

        return True

    def build_topic(self, topic_host_name=None, action=None):
        # Get topic (if any)
        topic_template = self.topic

        # If not topic then return none
        if topic_template == None:
            return

        # Add standard parameters
        topic = topic_template.format(
            key=self.key,
            name=self.name,
            action=action,
            topicHostName=topic_host_name)

        # Return the topic with any parameters set
        return topic
