from points.interval import Interval


class IoPoint(Interval):
    def __init__(self, key, name, description, value, invert, topic, interval, mqtt_publish_interval):
        super().__init__(interval)

        self.key = key
        self.name = name
        self.description = description
        self.topic = topic
        self.value = value
        self.invert = invert
        self.mqtt_publish_interval = mqtt_publish_interval
        self._mqtt_publish_tick_count = 0

    def mqtt_publish_tick(self, topic_host_name):
        self._mqtt_publish_tick_count = self._mqtt_publish_tick_count + 1

        if self.mqtt_publish_interval == None or self._mqtt_publish_tick_count < self.mqtt_publish_interval:
            # False signals topic should not be published
            return False

        self._mqtt_publish_tick_count = 0

        # True signals topic should be published
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
