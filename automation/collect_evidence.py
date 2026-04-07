#!/usr/bin/env python3
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

import yaml


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def docker_exec(container: str, *cmd: str) -> tuple[int, str, str]:
    return run_cmd(["docker", "exec", container, *cmd])


def vtysh(container: str, command: str) -> tuple[int, str, str]:
    return docker_exec(container, "vtysh", "-c", command)


def container_name(lab_name: str, node: str) -> str:
    return f"clab-{lab_name}-{node}"


def save_text(path: Path, title: str, stdout: str, stderr: str, rc: int) -> None:
    content = [
        f"# {title}",
        "",
        f"- Return code: {rc}",
        "",
        "## STDOUT",
        "",
        "```",
        stdout,
        "```",
        "",
        "## STDERR",
        "",
        "```",
        stderr,
        "```",
        "",
    ]
    path.write_text("\n".join(content), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Mini Fabric Lab evidence")
    parser.add_argument("--expected", default="automation/expected_state.yml")
    parser.add_argument("--lab-name", default=None)
    args = parser.parse_args()

    with open(args.expected, "r", encoding="utf-8") as f:
        expected = yaml.safe_load(f)

    lab_name = args.lab_name or expected["lab_name"]
    routers = list(expected.get("routers", {}).keys())
    hosts = list(expected.get("hosts", {}).keys())

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = Path("results") / f"evidence-{ts}"
    base.mkdir(parents=True, exist_ok=True)

    router_cmds = {
        "show_ip_ospf_neighbor.txt": "show ip ospf neighbor",
        "show_ip_route_ospf.txt": "show ip route ospf",
        "show_ip_bgp_summary.txt": "show ip bgp summary",
        "show_ip_bgp.txt": "show ip bgp",
        "show_ip_route.txt": "show ip route",
    }

    for node in routers:
        node_dir = base / node
        node_dir.mkdir(parents=True, exist_ok=True)
        container = container_name(lab_name, node)

        for filename, command in router_cmds.items():
            rc, out, err = vtysh(container, command)
            save_text(node_dir / filename, f"{node}: {command}", out, err, rc)

    for host in hosts:
        node_dir = base / host
        node_dir.mkdir(parents=True, exist_ok=True)
        container = container_name(lab_name, host)

        for filename, cmd in {
            "ip_addr.txt": ["ip", "addr"],
            "ip_route.txt": ["ip", "route"],
        }.items():
            rc, out, err = docker_exec(container, *cmd)
            save_text(node_dir / filename, f"{host}: {' '.join(cmd)}", out, err, rc)

    # Optional end-to-end checks from h1 and h2
    h1_target = expected.get("hosts", {}).get("h1", {}).get("ping_target")
    h2_target = expected.get("hosts", {}).get("h2", {}).get("ping_target")

    if h1_target:
        rc, out, err = docker_exec(container_name(lab_name, "h1"), "ping", "-c", "3", h1_target)
        save_text(base / "h1_to_target_ping.txt", f"h1 ping {h1_target}", out, err, rc)

        rc, out, err = docker_exec(container_name(lab_name, "h1"), "traceroute", "-n", h1_target)
        save_text(base / "h1_to_target_traceroute.txt", f"h1 traceroute {h1_target}", out, err, rc)

    if h2_target:
        rc, out, err = docker_exec(container_name(lab_name, "h2"), "ping", "-c", "3", h2_target)
        save_text(base / "h2_to_target_ping.txt", f"h2 ping {h2_target}", out, err, rc)

        rc, out, err = docker_exec(container_name(lab_name, "h2"), "traceroute", "-n", h2_target)
        save_text(base / "h2_to_target_traceroute.txt", f"h2 traceroute {h2_target}", out, err, rc)

    print(f"Evidence written to: {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())