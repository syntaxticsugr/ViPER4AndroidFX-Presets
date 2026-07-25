"""Any-to-any ViPER preset converter (hub-and-spoke).

    parse[source] → canon → serialize[target]

Spokes: ``xml`` (canonical + legacy variants), ``v1`` (flat json), ``v2`` (grouped
json). The canon is the neutral hub (registry.py). Source format is auto-detected.

``v2`` is device-agnostic; when the target is ``v1``/``xml`` and the source didn't
carry a mode, pass ``mode`` ("1" = headphone / "2" = speaker) or fan out to both.

The conversion is faithful: it carries every value the source holds and adds no
opinions of its own. A caller that wants to overlay policy - a release pinning
the output stage to defaults, say - passes a ``transform`` that mutates the canon
between parse and serialize, keeping that policy out of the converter itself.

CLI:
    python -m utils.convert.convert IN.xml -t v2 -o OUT.v2.json
    python -m utils.convert.convert IN.v2.json -t xml -m 1 -o OUT.xml
"""

import json
from collections.abc import Callable

from utils.convert import serialize as _S
from utils.convert.parse import detect_format, parse

_TARGETS = ("xml", "v1", "v2")


def convert(
    text: str,
    target: str,
    mode: str | None = None,
    transform: Callable[[dict], None] | None = None,
) -> str:
    """Convert a preset (any spoke) to ``target`` ('xml'|'v1'|'v2'); return a string.

    ``transform``, when given, is applied to the parsed canon in place before
    serialization - the seam for caller-owned flavors. The converter's own
    behavior is unchanged when it is omitted.
    """
    if target not in _TARGETS:
        raise ValueError(f"unknown target {target!r}; expected one of {_TARGETS}")
    canon, src_mode = parse(text=text)
    if transform is not None:
        transform(canon)
    mode = mode or src_mode

    if target == "v2":
        return json.dumps(
            obj=_S.serialize_v2(canon=canon),
            indent=2,
            ensure_ascii=False,
        )
    if mode not in ("1", "2"):
        raise ValueError(
            f"target {target!r} needs mode '1' (headphone) or '2' (speaker); "
            "source is device-agnostic"
        )
    if target == "v1":
        return json.dumps(
            obj=_S.serialize_v1(canon=canon, mode=mode),
            indent=2,
            ensure_ascii=False,
        )
    return _S.xml_to_str(elements=_S.serialize_xml(canon=canon, mode=mode))


def _main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Any-to-any ViPER preset converter.")
    ap.add_argument("input", help="source preset (.xml / .json)")
    ap.add_argument("-t", "--target", required=True, choices=_TARGETS)
    ap.add_argument(
        "-m",
        "--mode",
        choices=("1", "2"),
        help="'1' headphone / '2' speaker (for v1/xml targets)",
    )
    ap.add_argument("-o", "--output", help="write here instead of stdout")
    a = ap.parse_args(args=argv)

    text = open(file=a.input, encoding="utf-8", errors="replace").read()
    print(f"detected source format: {detect_format(text=text)}")
    out = convert(text=text, target=a.target, mode=a.mode)
    if a.output:
        open(file=a.output, mode="w", encoding="utf-8").write(out)
        print(f"wrote {a.output}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
