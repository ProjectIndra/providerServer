import time
import requests
from confluent_kafka import Producer
import json
import re
from collections import defaultdict

conf = {
    'bootstrap.servers': '192.168.1.9:9092,192.168.1.9:9094,192.168.1.9:9096',
    'client.id': 'metrics-scraper'
}

producer = Producer(conf)

TOPIC = "provider-metrics"
METRICS_URL = "http://localhost:3000/metrics"  # replace with your app metrics endpoint

PROVIDER_ID = "provider1"
PROVIDER_URL = "http://localhost:3000"


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


def aggregate_metrics(parsed_metrics):
    """Aggregate flat list into hierarchical JSON"""
    provider = {
        "provider_id": PROVIDER_ID,
        "provider_url": PROVIDER_URL,
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


while True:
    try:
        response = requests.get(METRICS_URL)
        response.raise_for_status()
        metrics_text = response.text

        parsed = parse_prometheus_metrics(metrics_text)

        if parsed:
            structured = aggregate_metrics(parsed)
            producer.produce(
                TOPIC,
                value=json.dumps(structured).encode("utf-8"),
                callback=delivery_report
            )
            producer.flush()
            print(f"Pushed structured metrics to Kafka")
        else:
            print("No metrics parsed")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(120)
