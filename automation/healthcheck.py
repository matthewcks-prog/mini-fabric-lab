#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
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


def load_expected(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_ospf_full_neighbors(output: str) -> int:
    count = 0
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Neighbor ID") or line.startswith("neighborId"):
            continue
        if line.startswith("%"):
            continue
        if re.search(r"\bFull(?:/[A-Za-z0-9-]+)?\b", line):
            count += 1
    return count


def find_peers_dict(obj):
    if isinstance(obj, dict):
        if "peers" in obj and isinstance(obj["peers"], dict):
            return obj["peers"]
        for value in obj.values():
            found = find_peers_dict(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_peers_dict(item)
            if found is not None:
                return found
    return None


def parse_bgp_peers(json_text: str) -> dict:
    data = json.loads(json_text)
    peers = find_peers_dict(data)
    if peers is None:
        raise ValueError("Could not find 'peers' in BGP summary JSON output")
    return peers


def peer_state(peer_info: dict) -> str:
    for key in ("state", "bgpState", "status"):
        value = peer_info.get(key)
        if value:
            return str(value)
    if "pfxRcd" in peer_info or "peerUptimeEstablishedEpoch" in peer_info:
        return "Established"
    return "Unknown"


def route_present(output: str, prefix: str) -> bool:
    lowered = output.lower()
    if "not in table" in lowered or "network not in table" in lowered:
        return False
    return prefix in output


def ensure_results_dir() -> Path:
    path = Path("results")
    path.mkdir(parents=True, exist_ok=True)
    return path


def record(results: list[dict], name: str, passed: bool, details: str) -> None:
    results.append({
        "name": name,
        "passed": passed,
        "details": details,
    })
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} - {details}")


def write_markdown_report(results: list[dict], report_path: Path, lab_name: str) -> None:
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    lines = [
        f"# Stage 6 Healthcheck Report",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"- Lab name: `{lab_name}`",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "## Check Results",
        "",
    ]
    for r in results:
        icon = "✅" if r["passed"] else "❌"
        lines.append(f"- {icon} **{r['name']}**: {r['details']}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mini Fabric Lab healthcheck")
    parser.add_argument(
        "--expected",
        default="automation/expected_state.yml",
        help="Path to expected_state.yml"
    )
    parser.add_argument(
        "--lab-name",
        default=None,
        help="Override lab name from expected_state.yml / topology name"
    )
    args = parser.parse_args()

    expected = load_expected(Path(args.expected))
    lab_name = args.lab_name or expected["lab_name"]

    results: list[dict] = []

    routers = expected.get("routers", {})
    hosts = expected.get("hosts", {})

    # Router checks
    for node, node_expect in routers.items():
        container = container_name(lab_name, node)

        rc, out, err = run_cmd(["docker", "ps", "--format", "{{.Names}}"])
        if rc != 0 or container not in out.splitlines():
            record(results, f"{node} container exists", False, f"{container} is not running")
            continue
        record(results, f"{node} container exists", True, f"{container} is running")

        expected_ospf = node_expect.get("ospf_neighbors")
        if expected_ospf is not None:
            rc, out, err = vtysh(container, "show ip ospf neighbor")
            if rc != 0:
                record(results, f"{node} OSPF neighbor check", False, err or "command failed")
            else:
                actual = parse_ospf_full_neighbors(out)
                record(
                    results,
                    f"{node} OSPF neighbor count",
                    actual == expected_ospf,
                    f"expected {expected_ospf}, got {actual}"
                )

        expected_bgp = node_expect.get("bgp_neighbors", {})
        if expected_bgp:
            rc, out, err = vtysh(container, "show ip bgp summary json")
            if rc != 0:
                record(results, f"{node} BGP summary", False, err or "command failed")
            else:
                try:
                    peers = parse_bgp_peers(out)
                    for peer_ip, wanted_state in expected_bgp.items():
                        if peer_ip not in peers:
                            record(
                                results,
                                f"{node} BGP peer {peer_ip}",
                                False,
                                "peer missing from summary"
                            )
                            continue
                        actual_state = peer_state(peers[peer_ip])
                        record(
                            results,
                            f"{node} BGP peer {peer_ip}",
                            actual_state == wanted_state,
                            f"expected {wanted_state}, got {actual_state}"
                        )
                except Exception as exc:
                    record(results, f"{node} BGP summary parse", False, str(exc))

        for prefix in node_expect.get("must_have_routes", []):
            rc, out, err = vtysh(container, f"show ip route {prefix}")
            if rc != 0:
                record(results, f"{node} route {prefix}", False, err or "command failed")
            else:
                present = route_present(out, prefix)
                record(
                    results,
                    f"{node} route {prefix}",
                    present,
                    "present in routing table" if present else "missing from routing table"
                )

    # Host ping checks
    for host, host_expect in hosts.items():
        target = host_expect.get("ping_target")
        if not target:
            continue

        container = container_name(lab_name, host)
        rc, out, err = docker_exec(container, "ping", "-c", "2", "-W", "1", target)
        record(
            results,
            f"{host} ping {target}",
            rc == 0,
            "reachable" if rc == 0 else (err or out or "ping failed")
        )

    results_dir = ensure_results_dir()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = results_dir / f"healthcheck-{ts}.md"
    write_markdown_report(results, report_path, lab_name)

    failed = any(not r["passed"] for r in results)
    print(f"\nReport written to: {report_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())