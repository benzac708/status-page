"""Read-only Kubernetes API client for the status page."""

from kubernetes import client, config
from kubernetes.client.rest import ApiException


def load_kube_config():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def get_nodes() -> list[dict]:
    load_kube_config()
    v1 = client.CoreV1Api()
    nodes = v1.list_node()
    result = []
    for n in nodes.items:
        conditions = {c.type: c.status for c in n.status.conditions}
        ready = conditions.get("Ready", "Unknown") == "True"
        alloc = n.status.allocatable or {}
        result.append({
            "name": n.metadata.name,
            "ready": ready,
            "roles": "control-plane" if "control-plane" in (n.metadata.labels or {}) else "worker",
            "cpu": alloc.get("cpu", "?"),
            "memory": alloc.get("memory", "?"),
        })
    return result


def get_pods() -> list[dict]:
    load_kube_config()
    v1 = client.CoreV1Api()
    pods = v1.list_pod_for_all_namespaces()
    result = []
    for p in pods.items:
        phase = p.status.phase or "Unknown"
        ready = 0
        total = 0
        if p.status.container_statuses:
            for cs in p.status.container_statuses:
                total += 1
                if cs.ready:
                    ready += 1
        result.append({
            "name": p.metadata.name,
            "namespace": p.metadata.namespace,
            "phase": phase,
            "ready": f"{ready}/{total}",
            "node": p.spec.node_name or "-",
        })
    return result


def get_deployments() -> list[dict]:
    load_kube_config()
    apps = client.AppsV1Api()
    deps = apps.list_deployment_for_all_namespaces()
    result = []
    for d in deps.items:
        ready = d.status.ready_replicas or 0
        desired = d.spec.replicas or 0
        result.append({
            "name": d.metadata.name,
            "namespace": d.metadata.namespace,
            "ready": f"{ready}/{desired}",
            "healthy": ready == desired,
        })
    return result


def get_argocd_apps() -> list[dict]:
    load_kube_config()
    try:
        custom = client.CustomObjectsApi()
        apps = custom.list_cluster_custom_object(
            "argoproj.io", "v1alpha1", "applications"
        )
        result = []
        for a in apps.get("items", []):
            sync = a.get("status", {}).get("sync", {}).get("status", "Unknown")
            health = a.get("status", {}).get("health", {}).get("status", "Unknown")
            result.append({
                "name": a["metadata"]["name"],
                "namespace": a["metadata"]["namespace"],
                "sync": sync,
                "health": health,
            })
        return result
    except ApiException:
        return []