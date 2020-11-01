from points.interval import Interval


class IoPoint(Interval):
    def __init__(self, key, name, description, value, topic, interval):
        super().__init__(interval)

        self.key = key
        self.name = name
        self.description = description
        self.topic = topic
        self.value = value

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
