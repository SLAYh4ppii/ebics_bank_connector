# Copyright (c) 2026, EBICS Bank Connector
"""Generic ISO 20022 XML helpers shared by CAMT parsers."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

try:
    from lxml import etree
except ImportError:  # pragma: no cover
    from xml.etree import ElementTree as etree  # type: ignore

# ISO 20022 namespaces used by CAMT.053 / CAMT.054
NS = {
    "ns": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02",
    "ns2": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.04",
    "ns3": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.02",
}

# Some banks use the pain/camt namespaces without a prefix; we register the
# most common variants and resolve dynamically in :func:`parse_xml`.
_DYNAMIC_NS = [
    "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02",
    "urn:iso:std:iso:20022:tech:xsd:camt.053.001.03",
    "urn:iso:std:iso:20022:tech:xsd:camt.053.001.04",
    "urn:iso:std:iso:20022:tech:xsd:camt.053.001.05",
    "urn:iso:std:iso:20022:tech:xsd:camt.054.001.02",
    "urn:iso:std:iso:20022:tech:xsd:camt.054.001.04",
]


def parse_xml(xml: bytes):
    """Parse CAMT XML, returning the root element with a resolved namespace map."""
    if isinstance(xml, str):
        xml = xml.encode("utf-8")
    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(xml, parser=parser)
    return root


def local(tag: str) -> str:
    """Strip the XML namespace prefix from a tag."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find(elem, *path, ns=None):
    """Find an element by local-name path, namespace-agnostic."""
    cur = elem
    for name in path:
        cur = _find_first_child(cur, name)
        if cur is None:
            return None
    return cur


def findall(elem, name):
    return [c for c in elem.iter() if local(c.tag) == name]


def _find_first_child(elem, name):
    for c in elem:
        if local(c.tag) == name:
            return c
    # descend one level for convenience
    return None


def text(elem) -> Optional[str]:
    return (elem.text or "").strip() if elem is not None else None


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_amount(value: Optional[str]) -> Decimal:
    if not value:
        return Decimal("0")
    return Decimal(value)
