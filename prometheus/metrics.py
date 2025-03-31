import subprocess
from flask import Blueprint, Response
from prometheus_client import Gauge, generate_latest, CollectorRegistry
from virt_controllers import telemetry

metrics_bp = Blueprint("metrics", __name__)

def get_virsh_metrics():
    """Fetch VM details dynamically when Prometheus scrapes /metrics"""
    registry = CollectorRegistry()

    provider_heartbeat = Gauge("provider_heartbeat", "Heartbeat signal for provider", registry=registry)
    provider_heartbeat.set(1)

    try:
        # Get list of active VMs
        active_vms_data = telemetry.list_running_vms()[0].get_json()
        active_vms = active_vms_data.get("vms", [])

        active_vms_gauge = Gauge("active_vms", "Number of active VMs", registry=registry)
        active_vms_gauge.set(len(active_vms))

        # Get list of inactive VMs
        inactive_vms_data = telemetry.list_inactive_vms()[0].get_json()
        inactive_vms = inactive_vms_data.get("vms", [])

        inactive_vms_gauge = Gauge("inactive_vms", "Number of inactive VMs", registry=registry)
        inactive_vms_gauge.set(len(inactive_vms))

        # VM state metric with labels instead of dynamic names
        vm_state = Gauge("vm_state", "State of the VM (0: Inactive, 1: Running)", ["vm"], registry=registry)
        vm_cpu_allocated = Gauge("vm_cpu_allocated", "CPU allocated of the VM", ["vm"], registry=registry)
        vm_ram_allocated = Gauge("vm_ram_allocated", "RAM allocated of the VM", ["vm"], registry=registry)
        vm_cpu_used = Gauge("vm_cpu_used", "CPU used of the VM", ["vm"], registry=registry)
        vm_ram_used = Gauge("vm_ram_used", "RAM used of the VM", ["vm"], registry=registry)

        
        for vm in active_vms:
            print(f"Getting info for VM: {vm}")
            vm_info = telemetry.get_vm_info(vm)[0].get_json()
            print(f"VM info: {vm_info}")
            vm_state.labels(vm=vm).set(vm_info["Running"])
            vm_cpu_allocated.labels(vm=vm).set(vm_info["VCPU-Allocated"])
            vm_ram_allocated.labels(vm=vm).set(vm_info["RAM-Allocated"])
            vm_cpu_used.labels(vm=vm).set(vm_info["VCPU-Used"])
            vm_ram_used.labels(vm=vm).set(vm_info["RAM-Used"])

        for vm in inactive_vms:
            vm_state.labels(vm=vm).set(0)

        # Get list of networks
        networks_data = telemetry.list_networks()[0].get_json()
        active_networks = networks_data.get("active_networks", [])
        inactive_networks = networks_data.get("inactive_networks", [])

        network_active = Gauge("network_active", "State of active networks", ["network"], registry=registry)
        network_inactive = Gauge("network_inactive", "State of inactive networks", ["network"], registry=registry)

        for network in active_networks:
            network_active.labels(network=network).set(1)

        for network in inactive_networks:
            network_inactive.labels(network=network).set(0)

    except Exception as e:
        print(f"Error fetching virsh data: {e}")

    return generate_latest(registry)

@metrics_bp.route("/metrics")
def metrics():
    return Response(get_virsh_metrics(), mimetype="text/plain; charset=utf-8")
