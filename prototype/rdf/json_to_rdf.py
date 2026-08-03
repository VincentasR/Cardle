from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.namespace import XSD


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "rdf" / "bmw_6_series.json"
SHAPES_PATH = ROOT / "rdf" / "shapes.ttl"
ACCEPTED_OUTPUT_PATH = ROOT / "rdf" / "bmw_6_series_accepted.ttl"
REJECTED_DIRECTORY = ROOT / "rdf"

# The full game might contain more namespaces
CARDLE = Namespace("https://cardle.example/ontology/")
CAR = Namespace("https://cardle.example/resource/car/")
ENGINE = Namespace("https://cardle.example/resource/engine/")
BODY_STYLE = Namespace("https://cardle.example/resource/body-style/")
ARRANGEMENT = Namespace("https://cardle.example/resource/cylinder-arrangement/")
SOURCE = Namespace("https://cardle.example/resource/source/")


def bind_namespaces(graph: Graph) -> None:
    """Register readable prefixes for Turtle serialization."""
    graph.bind("cardle", CARDLE)
    graph.bind("car", CAR)
    graph.bind("engine", ENGINE)
    graph.bind("style", BODY_STYLE)
    graph.bind("arrangement", ARRANGEMENT)
    graph.bind("source", SOURCE)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("xsd", XSD)


def add_label(
    graph: Graph,
    resource: Any,
    label: str,
) -> None:
    graph.add(
        (
            resource,
            RDFS.label,
            Literal(label, lang="en"),
        )
    )


def record_to_rdf(record: dict[str, Any]) -> Graph:
    """Convert one canonical JSON record into an RDF graph."""
    graph = Graph()
    bind_namespaces(graph)

    manufacturer = CAR[record["manufacturer"]["id"]]
    model = CAR[record["model"]["id"]]
    variant = CAR[record["variant"]["id"]]
    version = CAR[record["version"]["id"]]

    body_style = BODY_STYLE[record["body_style"]["id"]]
    engine = ENGINE[record["engine"]["id"]]
    source = SOURCE[record["source"]["id"]]

    # Manufacturer
    graph.add((manufacturer, RDF.type, CARDLE.Manufacturer))
    add_label(
        graph,
        manufacturer,
        record["manufacturer"]["name"],
    )
    graph.add((manufacturer, CARDLE.hasModel, model))
    graph.add((manufacturer, CARDLE.assertedFrom, source))

    # Model
    graph.add((model, RDF.type, CARDLE.Model))
    add_label(graph, model, record["model"]["name"])
    graph.add((model, CARDLE.hasVariant, variant))
    graph.add((model, CARDLE.assertedFrom, source))

    # Variant
    graph.add((variant, RDF.type, CARDLE.Variant))
    add_label(graph, variant, record["variant"]["name"])
    graph.add((variant, CARDLE.hasVersion, version))
    graph.add((variant, CARDLE.assertedFrom, source))

    # Version
    graph.add((version, RDF.type, CARDLE.Version))
    add_label(graph, version, record["version"]["name"])
    graph.add((version, CARDLE.hasBodyStyle, body_style))
    graph.add((version, CARDLE.hasEngine, engine))
    graph.add((version, CARDLE.assertedFrom, source))

    # Body style
    graph.add((body_style, RDF.type, CARDLE.BodyStyle))
    add_label(
        graph,
        body_style,
        record["body_style"]["name"],
    )

    # Engine
    graph.add((engine, RDF.type, CARDLE.Engine))
    add_label(graph, engine, record["engine"]["name"])

    graph.add(
        (
            engine,
            CARDLE.cylinderCount,
            Literal(
                record["engine"]["cylinder_count"],
                datatype=XSD.integer,
            ),
        )
    )

    graph.add((engine, CARDLE.assertedFrom, source))

    # Cylinder arrangement is deliberately optional in the mapper.
    #
    # This allows malformed input to become malformed RDF, which SHACL
    # can then detect. The mapper should not silently invent a value.
    arrangement_data = record["engine"].get(
        "cylinder_arrangement"
    )

    if arrangement_data is not None:
        arrangement = ARRANGEMENT[arrangement_data["id"]]

        graph.add(
            (
                arrangement,
                RDF.type,
                CARDLE.CylinderArrangement,
            )
        )
        add_label(
            graph,
            arrangement,
            arrangement_data["name"],
        )
        graph.add(
            (
                engine,
                CARDLE.hasCylinderArrangement,
                arrangement,
            )
        )

    # Source
    graph.add((source, RDF.type, CARDLE.Source))
    graph.add(
        (
            source,
            CARDLE.sourceUrl,
            Literal(
                record["source"]["url"],
                datatype=XSD.anyURI,
            ),
        )
    )

    return graph


def validate_record(
    data_graph: Graph,
    shapes_graph: Graph,
) -> tuple[bool, str]:
    """Validate one generated RDF record against SHACL."""
    conforms, _, report_text = validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
        advanced=False,
        debug=False,
    )

    return bool(conforms), str(report_text)


def safe_filename(record: dict[str, Any]) -> str:
    return f'{record["variant"]["id"]}.ttl'


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input JSON not found: {INPUT_PATH}"
        )

    if not SHAPES_PATH.exists():
        raise FileNotFoundError(
            f"SHACL file not found: {SHAPES_PATH}"
        )

    ACCEPTED_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    REJECTED_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = json.loads(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    if not isinstance(records, list):
        raise TypeError(
            "The input JSON must contain a list of records."
        )

    shapes_graph = Graph()
    shapes_graph.parse(SHAPES_PATH, format="turtle")

    accepted_graph = Graph()
    bind_namespaces(accepted_graph)

    accepted_count = 0
    rejected_count = 0

    for record in records:
        variant_name = record["variant"]["name"]
        version_name = record["version"]["name"]

        record_graph = record_to_rdf(record)

        conforms, report = validate_record(
            record_graph,
            shapes_graph,
        )

        if conforms:
            accepted_graph += record_graph
            accepted_count += 1

            print(
                f"PASS: {variant_name} {version_name}"
            )
        else:
            rejected_count += 1

            rejected_path = (
                REJECTED_DIRECTORY
                / safe_filename(record)
            )

            record_graph.serialize(
                destination=rejected_path,
                format="turtle",
            )

            report_path = rejected_path.with_suffix(
                ".report.txt"
            )
            report_path.write_text(
                report,
                encoding="utf-8",
            )

            print(
                f"FAIL: {variant_name} {version_name}"
            )
            print(report)

    accepted_graph.serialize(
        destination=ACCEPTED_OUTPUT_PATH,
        format="turtle",
    )

    print()
    print(f"Accepted records: {accepted_count}")
    print(f"Rejected records: {rejected_count}")
    print(
        f"Accepted RDF written to: "
        f"{ACCEPTED_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()