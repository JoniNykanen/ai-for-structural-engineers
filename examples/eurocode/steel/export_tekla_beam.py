"""
Teräspalkin tiedot Teklasta JSON-tiedostoksi  (Tekla Open API, pythonnet)
========================================================================

Lukee Tekla Structuresista valitun palkin (tai GUIDilla annetun) pituuden,
profiilin ja materiaalin sekä profiilin geometrian ja kirjaston
poikkileikkaussuureet. Tulos menee mitoitusskriptin steel_beam_ec3.py
syötteeksi.

Vaatii: Tekla Structures käynnissä ja malli auki; Python, jossa on pythonnet
(esim. Tekla MCP -palvelimen .venv). Ei käytä MCP-palvelimen koodia.

Aja:  python export_tekla_beam.py [GUID] [--out tiedosto.json]
"""

import argparse
import json
import os
import sys

TEKLA_BIN = os.environ.get("TEKLA_BIN", r"C:\Program Files\Tekla Structures\2026.0\bin")
HERE = os.path.dirname(os.path.abspath(__file__))


def load_tekla():
    import clr
    dirs = [TEKLA_BIN, os.path.join(TEKLA_BIN, "Net48Runtime")]
    sys.path += dirs
    for name in ("Tekla.Structures", "Tekla.Structures.Model", "Tekla.Structures.Catalogs"):
        path = next((os.path.join(d, name + ".dll") for d in dirs
                     if os.path.exists(os.path.join(d, name + ".dll"))), None)
        if path is None:
            raise SystemExit(f"{name}.dll ei löydy kansiosta {TEKLA_BIN} (aseta TEKLA_BIN).")
        clr.AddReference(path)


def pick_beam(M, guid):
    model = M.Model()
    if not model.GetConnectionStatus():
        raise SystemExit("Ei yhteyttä Teklaan: avaa Tekla Structures ja malli ensin.")
    if guid:
        import System
        import Tekla.Structures as TS
        obj = model.SelectModelObject(TS.Identifier(System.Guid(guid)))
        if obj is None:
            raise SystemExit(f"GUIDia {guid} ei löydy mallista.")
        return model, obj
    sel = M.UI.ModelObjectSelector().GetSelectedObjects()
    while sel.MoveNext():
        if isinstance(sel.Current, M.Beam):
            return model, sel.Current
    raise SystemExit("Valitse palkki Teklassa tai anna sen GUID.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("guid", nargs="?")
    ap.add_argument("--out")
    a = ap.parse_args()

    load_tekla()
    import Tekla.Structures.Model as M
    import Tekla.Structures.Catalogs as C

    model, beam = pick_beam(M, a.guid)
    s, e = beam.StartPoint, beam.EndPoint
    length = ((e.X - s.X) ** 2 + (e.Y - s.Y) ** 2 + (e.Z - s.Z) ** 2) ** 0.5
    profile = beam.Profile.ProfileString

    item = C.LibraryProfileItem()
    if not item.Select(profile):
        raise SystemExit(f"Profiilia {profile} ei löydy mallin profiilikirjastosta.")
    geometry = {p.Property: p.Value for p in item.aProfileItemParameters}
    catalog = {p.Property: p.Value for p in item.aProfileItemAnalysisParameters if p.Value}

    data = {
        "source": "Tekla Structures Open API",
        "model": model.GetInfo().ModelName,
        "guid": beam.Identifier.GUID.ToString(),
        "name": beam.Name,
        "profile": profile,
        "material": beam.Material.MaterialString,
        "start_point_mm": [s.X, s.Y, s.Z],
        "end_point_mm": [e.X, e.Y, e.Z],
        "length_mm": length,
        "geometry_mm": geometry,
        "catalog_properties": catalog,
    }
    out = a.out or os.path.join(HERE, f"tekla_beam_{profile}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"{profile} {data['material']} L={length:.0f} mm -> {out}")


if __name__ == "__main__":
    main()
