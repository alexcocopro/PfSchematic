from __future__ import annotations

import argparse
import html
import ipaddress
import json
from collections import Counter
from pathlib import Path
from typing import Any, BinaryIO

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException


APP_NAME = "PfSchematic"
OWNER_TEXT = "Propiedad de Alex Cabello Leiva, consultor de innovacion y ciberseguridad."
ROOT_DIR = Path(__file__).resolve().parent
SAMPLE_XML = ROOT_DIR / "muestra" / "demo-pfschematic.xml"

ACTION_STYLES = {
    "pass": {"label": "Permitir", "color": "#18a058"},
    "block": {"label": "Bloquear", "color": "#d64545"},
    "reject": {"label": "Rechazar", "color": "#f08c00"},
    "unknown": {"label": "Sin tipo", "color": "#64748b"},
}

NODE_GROUPS = {
    "any": {"label": "Cualquiera", "color": "#8b5cf6"},
    "alias": {"label": "Alias", "color": "#0ea5a4"},
    "interface": {"label": "Interfaz", "color": "#2563eb"},
    "interface_ip": {"label": "IP interfaz", "color": "#0891b2"},
    "private": {"label": "Red privada", "color": "#16a34a"},
    "public": {"label": "Red publica", "color": "#dc2626"},
    "host": {"label": "Host/objeto", "color": "#7c3aed"},
}


class DiagramadorError(Exception):
    """Error controlado para XML invalido o archivos no soportados."""


def _clean(value: Any, default: str = "") -> str:
    if value is None:
        return default
    cleaned = html.unescape(str(value)).strip()
    return cleaned if cleaned else default


def _text(node: ET.Element | None, tag: str, default: str = "") -> str:
    if node is None:
        return default
    return _clean(node.findtext(tag), default)


def _parse_root(xml_source: str | Path | BinaryIO) -> ET.Element:
    try:
        return ET.parse(xml_source).getroot()
    except FileNotFoundError as exc:
        raise DiagramadorError("El archivo XML no existe.") from exc
    except ET.ParseError as exc:
        raise DiagramadorError("El archivo no es un XML valido o esta corrupto.") from exc
    except DefusedXmlException as exc:
        raise DiagramadorError("El XML fue rechazado por seguridad.") from exc
    except OSError as exc:
        raise DiagramadorError(f"No se pudo leer el archivo: {exc}") from exc


def _interface_label(name: str, interfaces: dict[str, dict[str, str]]) -> str:
    interface = interfaces.get(name)
    if not interface:
        return name
    descr = interface.get("descr") or name
    return f"{descr} ({name})"


def _split_address_list(value: str) -> list[str]:
    return [item for item in value.replace(",", " ").split() if item]


def _split_detail_list(value: str) -> list[str]:
    return [_clean(item) for item in value.split("||") if _clean(item)]


def _classify_alias_item(value: str, alias_type: str) -> str:
    if alias_type == "port":
        return "Puerto"

    try:
        network = ipaddress.ip_network(value, strict=False)
        if "/" in value:
            return "Red privada" if network.is_private else "Red publica"
        return "IP privada" if network.is_private else "IP publica"
    except ValueError:
        pass

    if "." in value and " " not in value:
        return "Dominio"
    return "Objeto"


def extract_aliases(root: ET.Element) -> dict[str, dict[str, Any]]:
    aliases: dict[str, dict[str, Any]] = {}
    for alias in root.findall(".//aliases/alias"):
        name = _text(alias, "name")
        if not name:
            continue
        alias_type = _text(alias, "type", "alias")
        addresses = _split_address_list(_text(alias, "address"))
        details = _split_detail_list(_text(alias, "detail"))
        entries = [
            {
                "value": address,
                "description": details[index] if index < len(details) else "",
                "kind": _classify_alias_item(address, alias_type),
            }
            for index, address in enumerate(addresses)
        ]
        aliases[name] = {
            "name": name,
            "type": alias_type,
            "descr": _text(alias, "descr"),
            "url": _text(alias, "url"),
            "updatefreq": _text(alias, "updatefreq"),
            "addresses": addresses,
            "details": details,
            "entries": entries,
            "count": len(addresses),
        }
    return aliases


def extract_interfaces(root: ET.Element) -> dict[str, dict[str, str]]:
    interfaces: dict[str, dict[str, str]] = {}
    interfaces_node = root.find("interfaces")
    if interfaces_node is None:
        return interfaces

    for node in list(interfaces_node):
        name = node.tag
        ipaddr = _text(node, "ipaddr")
        subnet = _text(node, "subnet")
        descr = _text(node, "descr", name)
        cidr = f"{ipaddr}/{subnet}" if ipaddr and subnet else ""
        interfaces[name] = {
            "name": name,
            "descr": descr,
            "device": _text(node, "if"),
            "ipaddr": ipaddr,
            "subnet": subnet,
            "cidr": cidr,
            "label": f"{descr} ({name})",
        }
    return interfaces


def _firewall_rule_elements(root: ET.Element) -> list[ET.Element]:
    if root.tag == "filter":
        return root.findall("rule")

    filter_node = root.find("filter")
    if filter_node is None:
        return []
    return filter_node.findall("rule")


def _classify_endpoint(value: str, aliases: dict[str, dict[str, Any]], interfaces: dict[str, dict[str, str]]) -> str:
    if value == "any":
        return "any"
    if value in aliases:
        return "alias"
    if value in interfaces:
        return "interface"
    if value.endswith("ip") and value[:-2] in interfaces:
        return "interface_ip"

    try:
        network = ipaddress.ip_network(value, strict=False)
        return "private" if network.is_private else "public"
    except ValueError:
        return "host"


def _endpoint_title(value: str, group: str, aliases: dict[str, dict[str, Any]], interfaces: dict[str, dict[str, str]]) -> str:
    if value in aliases:
        alias = aliases[value]
        preview = ", ".join(alias["addresses"][:6])
        if alias["count"] > 6:
            preview = f"{preview}, ..."
        parts = [f"Alias: {value}", f"Tipo: {alias['type']}"]
        if alias["descr"]:
            parts.append(f"Descripcion: {alias['descr']}")
        if preview:
            parts.append(f"Objetos: {preview}")
        return "\n".join(parts)

    if value in interfaces:
        interface = interfaces[value]
        parts = [f"Interfaz: {interface['label']}"]
        if interface["device"]:
            parts.append(f"Dispositivo: {interface['device']}")
        if interface["cidr"]:
            parts.append(f"Red/IP: {interface['cidr']}")
        return "\n".join(parts)

    if value.endswith("ip") and value[:-2] in interfaces:
        return f"IP de interfaz: {_interface_label(value[:-2], interfaces)}"

    return f"{NODE_GROUPS.get(group, NODE_GROUPS['host'])['label']}: {value}"


def _endpoint_label(value: str, aliases: dict[str, dict[str, Any]], interfaces: dict[str, dict[str, str]]) -> str:
    if value == "any":
        return "any"
    if value in interfaces:
        return interfaces[value]["descr"]
    if value.endswith("ip") and value[:-2] in interfaces:
        return f"{interfaces[value[:-2]]['descr']} IP"
    return value


def _parse_endpoint(node: ET.Element | None, aliases: dict[str, dict[str, Any]], interfaces: dict[str, dict[str, str]]) -> dict[str, Any]:
    value = "any"
    field = "any"
    if node is not None:
        if node.find("network") is not None:
            value = _text(node, "network", "any")
            field = "network"
        elif node.find("address") is not None:
            value = _text(node, "address", "any")
            field = "address"
        elif node.find("any") is not None:
            value = "any"
            field = "any"

    group = _classify_endpoint(value, aliases, interfaces)
    return {
        "value": value,
        "label": _endpoint_label(value, aliases, interfaces),
        "group": group,
        "field": field,
        "port": _text(node, "port", "any") if node is not None else "any",
        "negated": node is not None and node.find("not") is not None,
        "title": _endpoint_title(value, group, aliases, interfaces),
    }


def _rule_user(rule: ET.Element, node_name: str) -> str:
    node = rule.find(node_name)
    if node is None:
        return ""
    return _text(node, "username")


def load_pfsense_config(xml_source: str | Path | BinaryIO, display_name: str | None = None) -> dict[str, Any]:
    root = _parse_root(xml_source)
    aliases = extract_aliases(root)
    interfaces = extract_interfaces(root)
    rule_nodes = _firewall_rule_elements(root)

    if not rule_nodes:
        raise DiagramadorError("No se encontraron reglas de firewall en el XML.")

    rules: list[dict[str, Any]] = []
    for index, rule in enumerate(rule_nodes, start=1):
        action = _text(rule, "type", "unknown").lower()
        if action not in ACTION_STYLES:
            action = "unknown"
        interface = _text(rule, "interface", "unknown")
        protocol = _text(rule, "protocol", "any").lower()
        source = _parse_endpoint(rule.find("source"), aliases, interfaces)
        destination = _parse_endpoint(rule.find("destination"), aliases, interfaces)
        disabled = rule.find("disabled") is not None

        rules.append(
            {
                "id": f"rule-{index}",
                "number": index,
                "tracker": _text(rule, "tracker"),
                "action": action,
                "action_label": ACTION_STYLES[action]["label"],
                "interface": interface,
                "interface_label": _interface_label(interface, interfaces),
                "ipprotocol": _text(rule, "ipprotocol", "inet"),
                "protocol": protocol or "any",
                "source": source["value"],
                "source_label": source["label"],
                "source_group": source["group"],
                "source_port": source["port"],
                "source_negated": source["negated"],
                "destination": destination["value"],
                "destination_label": destination["label"],
                "destination_group": destination["group"],
                "destination_port": destination["port"],
                "destination_negated": destination["negated"],
                "description": _text(rule, "descr", "Sin descripcion"),
                "disabled": disabled,
                "logged": rule.find("log") is not None,
                "gateway": _text(rule, "gateway"),
                "state_type": _text(rule, "statetype"),
                "created_by": _rule_user(rule, "created"),
                "updated_by": _rule_user(rule, "updated"),
            }
        )

    name = display_name
    if not name and isinstance(xml_source, (str, Path)):
        name = Path(xml_source).name
    if not name:
        name = "archivo-subido.xml"

    config = {
        "name": name,
        "root_tag": root.tag,
        "rules": rules,
        "aliases": aliases,
        "interfaces": interfaces,
    }
    config["stats"] = build_stats(config)
    return config


def build_stats(config: dict[str, Any]) -> dict[str, Any]:
    rules = config["rules"]
    action_counts = Counter(rule["action"] for rule in rules)
    protocol_counts = Counter(rule["protocol"] for rule in rules)
    interface_counts = Counter(rule["interface"] for rule in rules)
    disabled = sum(1 for rule in rules if rule["disabled"])

    return {
        "total_rules": len(rules),
        "enabled_rules": len(rules) - disabled,
        "disabled_rules": disabled,
        "actions": dict(action_counts),
        "protocols": dict(protocol_counts),
        "interfaces": dict(interface_counts),
        "alias_count": len(config["aliases"]),
        "interface_count": len(config["interfaces"]),
    }


def build_diagram_payload(config: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def add_node(value: str, label: str, group: str, title: str, rule_number: int) -> None:
        if value not in nodes:
            node = {
                "id": value,
                "label": label,
                "group": group,
                "title": title,
                "value": 18 if group == "any" else 12,
                "ruleNumbers": [],
            }
            if group == "alias" and value in aliases:
                node["aliasType"] = aliases[value]["type"]
                node["aliasCount"] = aliases[value]["count"]
            nodes[value] = node

        if rule_number not in nodes[value]["ruleNumbers"]:
            nodes[value]["ruleNumbers"].append(rule_number)

    aliases = config["aliases"]
    interfaces = config["interfaces"]
    for rule in config["rules"]:
        source_group = rule["source_group"]
        destination_group = rule["destination_group"]
        add_node(
            rule["source"],
            rule["source_label"],
            source_group,
            _endpoint_title(rule["source"], source_group, aliases, interfaces),
            rule["number"],
        )
        add_node(
            rule["destination"],
            rule["destination_label"],
            destination_group,
            _endpoint_title(rule["destination"], destination_group, aliases, interfaces),
            rule["number"],
        )

        action_color = ACTION_STYLES[rule["action"]]["color"]
        port = rule["destination_port"]
        label_parts = [rule["protocol"].upper()]
        if port != "any":
            label_parts.append(port)
        label = ":".join(label_parts)

        title = "\n".join(
            [
                f"Regla #{rule['number']} - {rule['action_label']}",
                f"Interfaz: {rule['interface_label']}",
                f"Origen: {rule['source_label']}:{rule['source_port']}",
                f"Destino: {rule['destination_label']}:{rule['destination_port']}",
                f"Protocolo: {rule['protocol'].upper()}",
                f"Descripcion: {rule['description']}",
                f"Estado: {'Deshabilitada' if rule['disabled'] else 'Activa'}",
            ]
        )
        edges.append(
            {
                "id": rule["id"],
                "from": rule["source"],
                "to": rule["destination"],
                "label": label,
                "title": title,
                "color": {"color": "#94a3b8" if rule["disabled"] else action_color},
                "width": 1.2 if rule["disabled"] else 2.4,
                "dashes": bool(rule["disabled"]),
                "arrows": {"to": {"enabled": True, "scaleFactor": 0.75}},
                "ruleId": rule["id"],
                "ruleNumber": rule["number"],
                "action": rule["action"],
                "interface": rule["interface"],
                "protocol": rule["protocol"],
                "disabled": rule["disabled"],
                "smooth": {"type": "curvedCW", "roundness": 0.18 + (rule["number"] % 5) * 0.035},
            }
        )

    for node in nodes.values():
        rule_numbers = sorted(node["ruleNumbers"])
        node["ruleNumbers"] = rule_numbers
        node["ruleCount"] = len(rule_numbers)
        node["firstRule"] = rule_numbers[0] if rule_numbers else None
        node["lastRule"] = rule_numbers[-1] if rule_numbers else None
        if rule_numbers:
            preview = ", ".join(f"#{number}" for number in rule_numbers[:12])
            if len(rule_numbers) > 12:
                preview = f"{preview}, ..."
            node["title"] = "\n".join(
                [
                    node["title"],
                    f"Reglas asociadas: {preview}",
                    f"Primera regla: #{node['firstRule']} | Ultima regla: #{node['lastRule']}",
                ]
            )

    return {
        "name": config["name"],
        "stats": config["stats"],
        "rules": config["rules"],
        "aliases": aliases,
        "nodes": list(nodes.values()),
        "edges": edges,
        "groups": NODE_GROUPS,
        "actions": ACTION_STYLES,
    }


def parse_pfsense_rules(xml_file: str | Path) -> list[dict[str, Any]]:
    return load_pfsense_config(xml_file)["rules"]


def generate_network_diagram(rules: list[dict[str, Any]], output_file: str | Path = "pfsense_diagram.html") -> None:
    from pyvis.network import Network

    config = {
        "name": Path(output_file).name,
        "rules": rules,
        "aliases": {},
        "interfaces": {},
        "stats": {},
    }
    payload = build_diagram_payload(config)
    network = Network(height="780px", width="100%", bgcolor="#f8fafc", font_color="#172033", directed=True)
    network.repulsion(node_distance=210, spring_length=190)

    color_by_group = {name: meta["color"] for name, meta in NODE_GROUPS.items()}
    for node in payload["nodes"]:
        network.add_node(
            node["id"],
            label=node["label"],
            title=node["title"],
            color=color_by_group.get(node["group"], "#64748b"),
            shape="dot" if node["group"] in {"public", "private"} else "box",
        )
    for edge in payload["edges"]:
        network.add_edge(
            edge["from"],
            edge["to"],
            label=edge["label"],
            title=edge["title"],
            color=edge["color"]["color"],
            width=edge["width"],
            dashes=edge["dashes"],
            arrows="to",
        )

    network.save_graph(str(output_file))


def _print_summary(config: dict[str, Any], output_file: Path | None = None) -> None:
    stats = config["stats"]
    print(f"{APP_NAME} - {config['name']}")
    print(f"Reglas: {stats['total_rules']} activas: {stats['enabled_rules']} deshabilitadas: {stats['disabled_rules']}")
    print(f"Acciones: {json.dumps(stats['actions'], ensure_ascii=True)}")
    print(f"Interfaces con reglas: {len(stats['interfaces'])}")
    print(f"Alias detectados: {stats['alias_count']}")
    if output_file:
        print(f"HTML generado: {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera diagramas de reglas firewall de pfSense.")
    parser.add_argument("xml", nargs="?", default=str(SAMPLE_XML), help="Ruta del backup XML de pfSense.")
    parser.add_argument("-o", "--output", default="pfsense_diagram.html", help="Archivo HTML de salida.")
    parser.add_argument("--summary", action="store_true", help="Muestra solo el resumen, sin generar HTML.")
    args = parser.parse_args()

    config = load_pfsense_config(args.xml)
    output_file = None
    if not args.summary:
        output_file = Path(args.output)
        generate_network_diagram(config["rules"], output_file)
    _print_summary(config, output_file)


if __name__ == "__main__":
    main()
