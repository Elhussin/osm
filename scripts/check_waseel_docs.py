"""Read-only source audit; persist structure and hashes, never request/sample values.

Python standard library only. No network or provider calls. --refresh explicitly
updates the sanitized manifest; the default checks that it is still current.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Waseel_PI_Document"
TARGET = ROOT / "docs/rebuild/waseel/contract-inventory.json"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
KNOWN_STATES = {"approved", "partial", "pended", "queued", "processing complete", "error", "rejected"}
SHEETS = {"PreAuthorization Request", "Preauthorization Response", "Eligibility Request", "Eligibility Response", "Cancel Request", "Cancel Response", "Communication"}


def structure(value, prefix=""):
    """Describe every array member, including empty/null containers; omit values."""
    result = set()
    def visit(node, path):
        kind = "null" if node is None else type(node).__name__
        result.add((path or "$", kind))
        if isinstance(node, dict):
            for key, child in node.items():
                visit(child, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for child in node:
                visit(child, path + "[]")
    visit(value, prefix)
    return [{"path": path, "type": kind} for path, kind in sorted(result)]


def requests(items, parent=""):
    for item in items:
        name = f"{parent}/{item['name']}"
        if "item" in item:
            yield from requests(item["item"], name)
        else:
            yield name, item["request"]


def summarize_request(name, request):
    url = request.get("url", {})
    raw = url if isinstance(url, str) else url.get("raw", "")
    parsed = urlsplit(raw)
    if parsed.hostname not in {"api.eclaims.waseel.com", "api.stg-eclaims.waseel.com"}:
        raise ValueError("Unreviewed API host in supplied documentation")
    # Provider identifiers belong to configuration, not to this manifest.
    path = re.sub(r"/providers/[^/]+/", "/providers/{provider_id}/", parsed.path)
    body = request.get("body", {})
    raw_body = body.get("raw")
    body_structure, body_status = [], "none"
    if raw_body:
        try:
            body_structure = structure(json.loads(raw_body))
            body_status = "strict_json"
        except json.JSONDecodeError:
            body_status = "non_strict_json_requires_review"
    auth = request.get("auth", {})
    return {
        "name": name, "method": request["method"], "host": parsed.hostname,
        "path_template": path,
        "query_keys": sorted(q["key"] for q in url.get("query", [])) if isinstance(url, dict) else [],
        "auth_type": auth.get("type"),
        "contains_nonempty_auth_value": any(bool(entry.get("value")) for entry in auth.get("bearer", [])),
        "body_status": body_status, "body_structure": body_structure,
    }


def workbook_inventory(path):
    """Bound XLSX extraction to A:G; one source sheet has a huge styled extent."""
    with ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in item.iterfind(".//m:t", NS)))
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        sheets = []
        fields = []
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).findall("m:sheets/m:sheet", NS):
            name = sheet.attrib["name"]
            sheets.append(name)
            if name not in SHEETS:
                continue
            rel = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = rels[rel].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            top = None
            for row in ET.fromstring(archive.read(target)).findall("m:sheetData/m:row", NS):
                cells = {}
                for cell in row.findall("m:c", NS):
                    column = re.match(r"[A-Z]+", cell.attrib["r"])[0]
                    if column not in {"A", "B", "C", "D", "E", "F", "G"}:
                        continue
                    v = cell.find("m:v", NS)
                    value = v.text if v is not None else None
                    if cell.attrib.get("t") == "s" and value is not None:
                        value = shared[int(value)]
                    elif cell.attrib.get("t") == "inlineStr":
                        value = "".join(t.text or "" for t in cell.iterfind(".//m:t", NS))
                    cells[column] = value
                if int(row.attrib["r"]) == 1:
                    continue
                a, b = cells.get("A"), cells.get("B")
                paired = name in {"PreAuthorization Request", "Preauthorization Response", "Eligibility Request"}
                if paired:
                    if a:
                        top = a
                    field = f"{top}.{b}" if b and top else a
                else:
                    field = a
                if field and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]*", field):
                    record = {"sheet": name, "row": int(row.attrib["r"]), "field": field}
                    if name in {"PreAuthorization Request", "Eligibility Request"}:
                        record["requirement_as_documented"] = cells.get("C")
                    fields.append(record)
        return {"sheets": sheets, "field_locations": fields}


def collect(source=SOURCE):
    files = sorted(p for p in source.rglob("*") if p.is_file())
    if not files:
        raise ValueError("Waseel source directory is missing or empty")
    collections = list(source.rglob("*.postman_collection"))
    if len(collections) != 1:
        raise ValueError("Expected one supplied Postman collection")
    collection = json.loads(collections[0].read_text(encoding="utf-8-sig"))
    operations = [summarize_request(name, request) for name, request in requests(collection["item"])]
    samples = []
    for path in sorted(source.glob("*.json")):
        sample = json.loads(path.read_text(encoding="utf-8-sig"))
        states = {}
        for key in ("outcome", "status"):
            value = sample.get(key)
            if value is None:
                states[key] = None
            elif isinstance(value, str) and value.lower() in KNOWN_STATES:
                states[key] = value
            else:
                states[key] = "unrecognized_value_omitted"
        samples.append({"source": path.name, "states": states, "structure": structure(sample)})
    return {
        "scope": "local_documentation_only_no_network_no_business_test",
        "source_files": [{"path": p.relative_to(source).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
        "workbook": workbook_inventory(source / "Waseel API v2.0 - Document.xlsx"),
        "operations": operations, "sample_structures": samples,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    report = collect()
    if args.refresh:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not TARGET.exists() or json.loads(TARGET.read_text(encoding="utf-8")) != report:
        raise SystemExit("FAIL: supplied Waseel sources changed; review and refresh the sanitized inventory")
    print(f"PASS: {len(report['source_files'])} source files, {len(report['operations'])} Postman requests, {len(report['workbook']['sheets'])} sheets, {len(report['sample_structures'])} JSON samples; hashes and sanitized structure match.")
    print("LIMIT: no API calls, credential validation, or ERP business tests performed.")


if __name__ == "__main__":
    main()
