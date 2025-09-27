import time
import requests
from confluent_kafka import Producer
import json
import re
from collections import defaultdict
import os
from dotenv import load_dotenv

conf = {
    'bootstrap.servers': '100.81.95.72:9092,100.81.95.72:9094,100.81.95.72:9096',
    'client.id': 'metrics-scraper'
}

producer = Producer(conf)

TOPIC = "provider-metrics"
METRICS_URL = "http://localhost:6996/metrics"

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# Get the provider server token from the environment
PROVIDER_ID = os.getenv("PROVIDER_SERVER_TOKEN")


def delivery_report(err, msg):
    """Callback for Kafka delivery confirmation"""
    if err is not None:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")


def parse_prometheus_metrics(text: str):
    """Parse Prometheus text exposition format into structured list"""
    metrics = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'(\w+)(\{.*\})?\s+([0-9\.\-eE]+)', line)
        if match:
            metric_name, labels_str, value = match.groups()
            labels = {}
            if labels_str:
                labels_str = labels_str.strip("{}")
                for kv in labels_str.split(","):
                    k, v = kv.split("=")
                    labels[k.strip()] = v.strip('"')
            metrics.append({
                "metric": metric_name,
                "labels": labels,
                "value": float(value),
                "timestamp": int(time.time())
            })
    return metrics


def aggregate_metrics(parsed_metrics,PROVIDER_ID):
    """Aggregate flat list into hierarchical JSON"""
    provider = {
        "provider_id": PROVIDER_ID,
        "metrics": {},
        "vms": [],
        "networks": []
    }

    vm_metrics = defaultdict(list)
    network_metrics = defaultdict(list)

    for metric in parsed_metrics:
        name = metric["metric"]
        labels = metric.get("labels", {})
        value = metric["value"]
        timestamp = metric["timestamp"]

        if "vm" in labels:
            vm_name = labels["vm"]
            vm_metrics[vm_name].append({
                "metric": name,
                "value": value,
                "timestamp": timestamp
            })
        elif "network" in labels:
            net_name = labels["network"]
            network_metrics[net_name].append({
                "metric": name,
                "value": value,
                "timestamp": timestamp
            })
        else:
            provider["metrics"][name] = {"value": value, "timestamp": timestamp}

    # Build VM list
    for vm_name, metrics in vm_metrics.items():
        provider["vms"].append({
            "vm_name": vm_name,
            "metrics": metrics
        })

    # Build network list
    for net_name, metrics in network_metrics.items():
        provider["networks"].append({
            "network_name": net_name,
            "metrics": metrics
        })

    return provider


# Main loop
while True:
    try:
        # Reload .env each iteration
        load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"), override=True)
        new_provider_id = os.getenv("PROVIDER_SERVER_TOKEN")
        if new_provider_id:
            if new_provider_id != PROVIDER_ID:
                PROVIDER_ID = new_provider_id
                print(f"PROVIDER_ID updated: {PROVIDER_ID}")
        else:
            print("PROVIDER_SERVER_TOKEN not found yet, will check again.")

        # Only proceed if token is available
        if PROVIDER_ID:
            response = requests.get(METRICS_URL)
            response.raise_for_status()
            metrics_text = response.text

            parsed = parse_prometheus_metrics(metrics_text)

            if parsed:
                structured = aggregate_metrics(parsed, PROVIDER_ID)
                producer.produce(
                    TOPIC,
                    value=json.dumps(structured).encode("utf-8"),
                    callback=delivery_report
                )
                producer.flush()
                print(f"Pushed structured metrics to Kafka")
            else:
                print("No metrics parsed")
        else:
            print("Skipping metrics push, token not yet available.")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(120)  # check every 2 minutes

