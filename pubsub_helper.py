import pika
import json
import ssl
import time

DEFAULT_BROKER_URL = 'amqps://xpfdnlyf:gILPRBWs2XY2SymBgsXjDYfVeJdk2682@puffin.rmq2.cloudamqp.com/xpfdnlyf'


class PubSub:
    def __init__(self, topic: str, brokerUrl: str = DEFAULT_BROKER_URL):
        self.topic = topic
        self.brokerUrl = brokerUrl
        self.connection = None
        self.channel = None
        self.exchange = "Test_PubSub"
        self.queue_name = None
        self.connected = False

    def connect(self):
        """Connect to RabbitMQ with SSL."""
        try:
            parameters = pika.URLParameters(self.brokerUrl)

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchange, exchange_type='topic')

            self.connected = True
        except Exception as e:
            print(f'Exception - connect: {e}')
            self.connected = False

    def publish(self, msg_dict: dict) -> bool:
        """Publish a message to the topic."""
        try:
            if not self.connected:
                self.connect()

            if msg_dict is None:
                msg_dict = {}

            json_body = json.dumps(msg_dict)
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.topic,  # Use topic as routing key
                body=json_body
            )
            print(f"Message published to topic [{self.topic}]: {msg_dict}")
            return True
        except Exception as e:
            print(f'Exception - publish: {e}')
            self.connected = False
            return False

    def subscribe(self, callback_function):
        """Subscribe to a topic using a temporary queue."""
        try:
            if not self.connected:
                self.connect()

            # Declare a temporary queue (auto-deleted when disconnected)
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue

            # Bind the temporary queue to the exchange with the topic as the routing key
            self.channel.queue_bind(exchange=self.exchange, queue=self.queue_name, routing_key=self.topic)

            print("Waiting for messages...")

            def internal_callback(ch, method, properties, body):
                message = json.loads(body.decode())
                callback_function(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            self.channel.basic_consume(queue=self.queue_name, on_message_callback=internal_callback)
            self.channel.start_consuming()
        except Exception as e:
            print(f'Exception - subscribe: {e}')
            self.connected = False
