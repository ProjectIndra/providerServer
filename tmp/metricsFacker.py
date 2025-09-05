import random
import time
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CollectorRegistry

app = Flask(__name__)

# --- Simulated Environment State ---
VM_POOL = {}
NETWORK_POOL = {}
last_update_time = time.time()

def init_state():
    """Initialize fake VM and network pool."""
    global VM_POOL, NETWORK_POOL
    VM_POOL = {
        f"vm{i}": {
            "running": True,
            "cpu_allocated": random.randint(1, 8),
            "ram_allocated": random.randint(512, 16384),
            "cpu_used": random.uniform(0.1, 8.0),
            "ram_used": random.uniform(100, 16000),
        }
        for i in range(3)  # start with 3 active VMs
    }
    NETWORK_POOL = {f"net{i}": True for i in range(2)}  # 2 active networks

def update_state():
    """Occasionally change VM and network states."""
    global last_update_time
    now = time.time()

    # Update only every ~5 seconds to avoid frantic changes
    if now - last_update_time < 5:
        return
    last_update_time = now

    # Random chance to add or remove a VM
    if random.random() < 0.3:  # 30% chance
        vm_name = f"vm{len(VM_POOL)}"
        VM_POOL[vm_name] = {
            "running": True,
            "cpu_allocated": random.randint(1, 8),
            "ram_allocated": random.randint(512, 16384),
            "cpu_used": random.uniform(0.1, 8.0),
            "ram_used": random.uniform(100, 16000),
        }
        print(f"[INFO] VM started: {vm_name}")

    if random.random() < 0.2 and VM_POOL:  # 20% chance to stop a VM
        vm = random.choice(list(VM_POOL.keys()))
        VM_POOL[vm]["running"] = not VM_POOL[vm]["running"]
        print(f"[INFO] VM {'started' if VM_POOL[vm]['running'] else 'stopped'}: {vm}")

    # Gradually change CPU/RAM usage
    for vm in VM_POOL.values():
        vm["cpu_used"] = max(0.1, min(vm["cpu_allocated"], vm["cpu_used"] + random.uniform(-0.5, 0.5)))
        vm["ram_used"] = max(50, min(vm["ram_allocated"], vm["ram_used"] + random.uniform(-100, 100)))

    # Networks: flip state occasionally
    if random.random() < 0.1:  # 10% chance
        net = f"net{len(NETWORK_POOL)}"
        NETWORK_POOL[net] = True
        print(f"[INFO] Network started: {net}")

    if random.random() < 0.1 and NETWORK_POOL:
        net = random.choice(list(NETWORK_POOL.keys()))
        NETWORK_POOL[net] = not NETWORK_POOL[net]
        print(f"[INFO] Network {'up' if NETWORK_POOL[net] else 'down'}: {net}")

def get_fake_metrics():
    """Generate Prometheus metrics based on state."""
    registry = CollectorRegistry()

    provider_heartbeat = Gauge("provider_heartbeat", "Heartbeat signal for provider", registry=registry)
    provider_heartbeat.set(1)

    # Separate active/inactive VMs
    active_vms = [name for name, info in VM_POOL.items() if info["running"]]
    inactive_vms = [name for name, info in VM_POOL.items() if not info["running"]]

    active_vms_gauge = Gauge("active_vms", "Number of active VMs", registry=registry)
    inactive_vms_gauge = Gauge("inactive_vms", "Number of inactive VMs", registry=registry)
    active_vms_gauge.set(len(active_vms))
    inactive_vms_gauge.set(len(inactive_vms))

    # VM state & resource metrics
    vm_state = Gauge("vm_state", "State of the VM (0: Inactive, 1: Running)", ["vm"], registry=registry)
    vm_cpu_allocated = Gauge("vm_cpu_allocated", "CPU allocated of the VM", ["vm"], registry=registry)
    vm_ram_allocated = Gauge("vm_ram_allocated", "RAM allocated of the VM", ["vm"], registry=registry)
    vm_cpu_used = Gauge("vm_cpu_used", "CPU used of the VM", ["vm"], registry=registry)
    vm_ram_used = Gauge("vm_ram_used", "RAM used of the VM", ["vm"], registry=registry)

    for vm, info in VM_POOL.items():
        vm_state.labels(vm=vm).set(1 if info["running"] else 0)
        vm_cpu_allocated.labels(vm=vm).set(info["cpu_allocated"])
        vm_ram_allocated.labels(vm=vm).set(info["ram_allocated"])
        vm_cpu_used.labels(vm=vm).set(round(info["cpu_used"], 2))
        vm_ram_used.labels(vm=vm).set(round(info["ram_used"], 2))

    # Network metrics
    network_active = Gauge("network_active", "State of active networks", ["network"], registry=registry)
    network_inactive = Gauge("network_inactive", "State of inactive networks", ["network"], registry=registry)

    for net, is_active in NETWORK_POOL.items():
        if is_active:
            network_active.labels(network=net).set(1)
        else:
            network_inactive.labels(network=net).set(0)

    return generate_latest(registry)

@app.route("/metrics")
def metrics():
    update_state()
    return Response(get_fake_metrics(), mimetype="text/plain; charset=utf-8")

if __name__ == "__main__":
    init_state()
    app.run(host="0.0.0.0", port=3000)
