import os
import json
import time
from typing import Callable, Optional, Dict, Any

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


class SharedMQTTClient:
    """Wrapper class for managing MQTT connections and topic subscriptions."""
    
    def __init__(self, broker: str = "mqtt-broker", port: int = 1883, client_id: Optional[str] = None):
        """Initialize the MQTT client with target broker address and client identifier.
        
        Args:
            broker: Hostname or IP address of the MQTT broker.
            port: Port number for the MQTT broker (default 1883).
            client_id: Unique identifier for this client connection.
        """
        self.broker = broker
        self.port = port
        self.client_id = client_id or "homelab-shared-client"
        self.subscriptions: Dict[str, Callable] = {}
        self._client = None

    def _get_client(self):
        if self._client is None:
            if mqtt is None:
                raise ImportError("paho-mqtt package is required. Install via 'pip install paho-mqtt'")
            try:
                self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=self.client_id)
            except Exception:
                self._client = mqtt.Client(client_id=self.client_id)
        return self._client

    def _on_connect(self, client, userdata, flags, rc):
        print(f"[{self.client_id}] Connected to MQTT broker with result code {rc}")
        for topic in self.subscriptions:
            client.subscribe(topic)
            print(f"[{self.client_id}] Subscribed to topic: {topic}")

    def _on_message(self, client, userdata, msg):
        for topic_pattern, callback in self.subscriptions.items():
            if self._topic_matches(topic_pattern, msg.topic):
                try:
                    payload = json.loads(msg.payload.decode('utf-8'))
                except Exception:
                    payload = msg.payload.decode('utf-8', errors='replace')
                try:
                    callback(msg.topic, payload)
                except Exception as e:
                    print(f"[{self.client_id}] Error in callback for topic '{msg.topic}': {e}")

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        if pattern == topic or pattern == "#":
            return True
        if pattern.endswith("/#"):
            prefix = pattern[:-2]
            return topic.startswith(prefix)
        return pattern == topic

    def connect(self) -> None:
        """Establish connection to the configured MQTT broker with auto-reconnect logic."""
        client = self._get_client()
        client.on_connect = self._on_connect
        client.on_message = self._on_message

        print(f"[{self.client_id}] Connecting to MQTT Broker at {self.broker}:{self.port}...")
        while True:
            try:
                client.connect(self.broker, self.port, 60)
                break
            except Exception as e:
                print(f"[{self.client_id}] Waiting for MQTT broker ({e})... retrying in 5 seconds.")
                time.sleep(5)
        client.loop_start()

    def subscribe(self, topic: str, on_message_callback: Callable) -> None:
        """Subscribe to a given MQTT topic pattern and attach a message handler callback."""
        self.subscriptions[topic] = on_message_callback
        if self._client and self._client.is_connected():
            self._client.subscribe(topic)

    def publish(self, topic: str, payload: dict, qos: int = 0) -> None:
        """Publish a JSON payload dictionary to a specified MQTT topic."""
        client = self._get_client()
        payload_str = json.dumps(payload, default=str)
        client.publish(topic, payload_str, qos=qos)

