"""Cluster status page — read-only dashboard for the k3d portfolio platform."""

from fastapi import FastAPI
from starlette.responses import HTMLResponse
import k8s_client

app = FastAPI(title="Cluster Status", version="0.1.0")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cluster Status</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; background: #0d1117; color: #c9d1d9; }
    h1 { margin-bottom: 0.5rem; }
    .meta { color: #8b949e; margin-bottom: 1.5rem; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 2rem; }
    th, td { border: 1px solid #30363d; padding: 0.5rem 1rem; text-align: left; }
    th { background: #161b22; }
    .ok { color: #3fb950; }
    .bad { color: #f85149; }
    .card { display: inline-block; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem 1.5rem; margin: 0.5rem; text-align: center; }
    .card h2 { margin: 0; font-size: 2rem; }
    .card p { margin: 0.25rem 0 0; color: #8b949e; font-size: 0.85rem; }
  </style>
</head>
<body>
  <h1>Cluster Status</h1>
  <p class="meta">k3d-dev · 3 nodes · auto-refresh 30s</p>
  <div id="cards"></div>
  <h2>Nodes</h2>
  <table id="nodes"><tr><th>Name</th><th>Status</th><th>Role</th><th>CPU</th><th>Memory</th></tr></table>
  <h2>Deployments</h2>
  <table id="deployments"><tr><th>Name</th><th>Namespace</th><th>Ready</th><th>Healthy</th></tr></table>
  <h2>Argo CD Applications</h2>
  <table id="apps"><tr><th>Name</th><th>Sync</th><th>Health</th></tr></table>
  <script>
    async function load() {
      const r = await fetch('/api/cluster');
      const d = await r.json();
      // cards
      const nodes = d.nodes, pods = d.pods, deps = d.deployments;
      const ready = nodes.filter(n => n.ready).length;
      const running = pods.filter(p => p.phase === 'Running').length;
      const healthy = deps.filter(x => x.healthy).length;
      document.getElementById('cards').innerHTML =
        card('Nodes', `${ready}/${nodes.length} ready`) +
        card('Pods', `${running}/${pods.length} running`) +
        card('Deployments', `${healthy}/${deps.length} healthy`) +
        card('Argo Apps', `${d.argocd.filter(a=>a.sync==='Synced').length}/${d.argocd.length} synced`);
      // nodes
      const nt = document.getElementById('nodes');
      nt.innerHTML = '<tr><th>Name</th><th>Status</th><th>Role</th><th>CPU</th><th>Memory</th></tr>';
      for (const n of nodes) nt.innerHTML += `<tr><td>${n.name}</td><td class="${n.ready?'ok':'bad'}">${n.ready?'Ready':'NotReady'}</td><td>${n.roles}</td><td>${n.cpu}</td><td>${n.memory}</td></tr>`;
      // deployments
      const dt = document.getElementById('deployments');
      dt.innerHTML = '<tr><th>Name</th><th>Namespace</th><th>Ready</th><th>Healthy</th></tr>';
      for (const dep of deps) dt.innerHTML += `<tr><td>${dep.name}</td><td>${dep.namespace}</td><td>${dep.ready}</td><td class="${dep.healthy?'ok':'bad'}">${dep.healthy?'Yes':'No'}</td></tr>`;
      // argocd
      const at = document.getElementById('apps');
      at.innerHTML = '<tr><th>Name</th><th>Sync</th><th>Health</th></tr>';
      for (const a of d.argocd) at.innerHTML += `<tr><td>${a.name}</td><td class="${a.sync==='Synced'?'ok':'bad'}">${a.sync}</td><td class="${a.health==='Healthy'?'ok':'bad'}">${a.health}</td></tr>`;
    }
    function card(t, v) { return `<div class="card"><h2>${v}</h2><p>${t}</p></div>`; }
    load();
    setInterval(load, 30000);
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML

@app.get("/api/cluster")
def cluster():
    return {
        "nodes": k8s_client.get_nodes(),
        "pods": k8s_client.get_pods(),
        "deployments": k8s_client.get_deployments(),
        "argocd": k8s_client.get_argocd_apps(),
    }

@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": "0.1.0"}