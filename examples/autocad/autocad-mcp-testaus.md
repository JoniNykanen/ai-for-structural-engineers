# AutoCAD MCP: käyttöönotto ja testaus

Tällä ohjeella Claude saadaan ohjaamaan AutoCADia. Lopussa on testisarja,
jolla tarkistetaan, toimiiko yhteys rakennesuunnittelun piirustuksissa.
Asennus kestää noin 15 minuuttia ja testit noin 30 minuuttia.

Tarkempi englanninkielinen ohje: [docs/20](../../docs/20-autocad-mcp.md).

**Claudelle:** kun käyttäjä pyytää testaamaan AutoCAD-yhteyttä, käy testit
T1–T7 läpi järjestyksessä. Kirjaa jokaisen testin tulos taulukkoon tämän
tiedoston lopussa: OK, VIRHE tai OSITTAIN, ja yhden rivin kuvaus. Lainaa
virheilmoitukset sanatarkasti. Älä korjaa palvelimen koodia. Kirjaa vain mitä tapahtui.

---

## Mitä tarvitset

- Windows 10 tai 11
- **AutoCAD:n täysversio**, mieluiten 2026 tai uudempi. **AutoCAD LT ei
  käy**, koska siinä ei ole COM-rajapintaa, jonka kautta Claude ohjaa AutoCADia.
- Claude Code ja tämä repo kloonattuna

## Asennus

1. **Asenna uv** PowerShellissä:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   Avaa uusi PowerShell-ikkuna ja tarkista, että `uvx --version` tulostaa
   versionumeron.
2. **Lataa palvelin valmiiksi** (ensimmäinen lataus kestää minuutin tai pari):
   ```powershell
   uvx --from "autocad-mcp-pro[com,pdf]==1.8.0" python -c "import ezdxf, win32com; print('ok')"
   ```
   Komennon pitää tulostaa `ok`.
3. **Tee testipiirustus.** Kopioi jokin oma rakennepiirustus (`.dwg`), jossa
   on profiilitekstejä (esim. HEA200, IPE300, RHS 100x100x5), nimellä
   `C:\temp\testi_kopio.dwg`. **Älä käytä alkuperäistä**, koska testit
   kirjoittavat piirustukseen.
4. **Avaa AutoCAD ja `testi_kopio.dwg` ensin.** Käynnistä Claude Code vasta
   sen jälkeen tässä repokansiossa. Hyväksy `autocad`-palvelin, kun Claude kysyy.
   - Jos AutoCAD aukesi vasta Clauden jälkeen: kirjoita `/mcp`, valitse
     *autocad* ja sitten *Reconnect*.

## Testit

Kirjoita Claudelle kunkin testin kehote. Testi on läpäisty, kun ehto
"Toimii, jos" täyttyy.

**T1 – Yhteys**
> Kutsu autocad-palvelimen system_status-työkalua.

Toimii, jos vastauksessa on `"backend":"com"`, `"connected":true` ja
oikea piirustuksen nimi.

**T2 – Tasojen lukeminen**
> Listaa avoimen piirustuksen tasot ja kuinka monta objektia kullakin on.

Toimii, jos lista vastaa AutoCADin Layer Properties -ikkunaa.

**T3 – Profiilitekstien lukeminen**
> Etsi piirustuksesta kaikki tekstit, joissa on teräsprofiili (HEA, HEB, IPE,
> RHS, SHS, CHS) tai liimapuu (GL), ja listaa ne sijainteineen.

Toimii, jos kaikki piirustuksen profiilitekstit löytyvät eikä mukana ole
vääriä osumia. Tarkista muutama sijainti AutoCADissa komennolla `ID`.

**T4 – Palkin piirtäminen**
> Piirrä mallitilaan tyhjään kohtaan vapaasti tuettu palkki: 7200 mm vaakaviiva
> tasolle GEOMETRY, tukisymbolit (kolmio) molempiin päihin, teksti
> "IPE300 S355" palkin yläpuolelle ja jännevälin mittaviiva.

Toimii, jos AutoCADin `DIST`-komento antaa palkin pituudeksi 7200 ja
mittaviivassa lukee 7200.

**T5 – Profiilin poikkileikkaus**
> Piirrä IPE300-profiilin poikkileikkaus mittoineen: h = 300, b = 150,
> tw = 7,1, tf = 10,7, r = 15 mm. Mitoita h, b, tw ja tf.

Toimii, jos muoto näyttää I-profiililta ja mitat täsmäävät, kun ne
tarkistetaan AutoCADissa `DIST`- tai `LIST`-komennolla.

**T6 – Sauvaluettelo taulukkona**
> Tee piirustukseen taulukko, jossa sarakkeet Tunnus, Profiili, Materiaali,
> Pituus (mm) ja Käyttöaste. Rivit: P1, IPE330, S355, 7200, 0.68 ja
> P2, HEA200, S355, 4800, 0.55.

Toimii, jos AutoCADiin syntyy oikea TABLE-objekti (ei irrallisia tekstejä)
ja arvot ovat oikein.

**T7 – Tallennus ja uudelleenavaus**
> Tallenna piirustus nimellä C:\temp\testi_tulos.dwg.

Sulje piirustus AutoCADissa ja avaa `testi_tulos.dwg` uudelleen. Toimii, jos
T4–T6:n piirrokset ovat tallessa.

## Tulokset

Claude täyttää tämän taulukon. Lähetä lopuksi tämä tiedosto Jonille.

| Testi | Tulos | Huomiot |
|---|---|---|
| T1 Yhteys | OK | `system_status`: `"backend":"com"`, `"connected":true`, `"active_document":"testi_kopio.dwg"`, AutoCAD `25.1s`, 257 työkalua. Ajettu kahdesti (2026-11-19 ja 2026-11-22), molemmilla kerroilla OK. Epäonnistuneet yritykset ennen: 19.11. `CONNECTION_CLOSED: "Connection closed"` (`uvx` puuttui, korjattu asentamalla `uv` ja käynnistämällä Claude uudelleen); 22.11. `CONNECT_TIMEOUT: "MCP server autocad connection timed out after 30000ms"` (AutoCAD ei ollut auki, `CAD_LAUNCH=never`; korjattu avaamalla AutoCAD ja testikopio ja yhdistämällä `/mcp` → Reconnect). |
| T2 Tasot | OK | `analysis_layer_stats`: 0 = 0, PALKIT = 2, PILARIT = 2, TEKSTI = 8, MITAT = 0 (5 tasoa), vastaa testipiirustusta. Ei verrattu AutoCADin Layer Properties -ikkunaan. |
| T3 Profiilitekstit | OK | `entity_list` (TEXT) palautti tekstit sijainteineen. Kokonaisen sanan haulla löytyi 6/6: IPE330, HEA200, HEB240, RHS 100x100x5, SHS 80x80x4, GL30C 140x360. Ei vääriä osumia: `PIPE 5 M` (sisältää kirjaimet IPE) ja `KATTOPALKKI` jäivät pois. Sijainnit täsmäävät testipiirustuksen luontiarvoihin, mutta niitä ei tarkistettu AutoCADin `ID`-komennolla. Ei erillistä tekstihakutyökalua käytetty, vaan lista suodatettiin Clauden päässä. |
| T4 Palkki | OK | Taso GEOMETRY, viiva 7200 (`length` 7200, COM `Length` 7200,0), kaksi kolmiotukea (3 viivaa/pää), teksti `IPE300 S355`, mittaviiva (COM `Measurement` 7200,0). Mittaus luettiin COM:lla, ei AutoCADin `DIST`-komennolla. |
| T5 Poikkileikkaus | OK | IPE300 viivoina ja kaarina (16 osaa, r = 15), mitat h 300, b 150, tw 7,1, tf 10,7 (COM `Measurement`). Ääriviiva sulkeutuu (ei vapaita päätepisteitä), pinta-ala kaavalla 5381,2 mm² (taulukkoarvo 5381). Ei tarkistettu silmämääräisesti, ettei muoto näytä I-profiililta. |
| T6 Taulukko | OK | Natiivi `TABLE`-objekti (3 riviä x 5 saraketta). Solut luettu takaisin: otsikot Tunnus, Profiili, Materiaali, Pituus (mm), Käyttöaste; P1 IPE330 S355 7200 0.68; P2 HEA200 S355 4800 0.55. |
| T7 Tallennus | OK | `drawing_save_as` -> `C:\temp\testi_tulos.dwg` (115 994 t). Piirustus suljettiin ja avattiin uudelleen (`drawing_open`). GEOMETRY-tasolla 29 objektia (19 LINE, 4 ARC, 5 ROTATEDDIMENSION, 1 TEXT), TEKSTI-tasolla 8 TEXT + 1 TABLE. Kaikki T4-T6:n piirrokset tallessa. |

### 3. ajo 2026-11-23 (kaikki T1–T7)

Ajettu `master`-haaralta (`5509e1c`) `autocad-mcp`-skillin ohjeilla.

| Testi | Tulos | Huomiot |
|---|---|---|
| T1 Yhteys | OK | `system_status`: `"backend":"com"`, `"connected":true`, `"active_document":"testi_kopio.dwg"`, AutoCAD `25.1s`, 257 työkalua. Yhdistyi ensimmäisellä kerralla. |
| T2 Tasot | OK | `analysis_layer_stats`: 0 = 0, PALKIT = 2, PILARIT = 2, TEKSTI = 8, MITAT = 0. Sama kuin aiemmin. |
| T3 Profiilitekstit | OK | `entity_list` (TEXT, `fields` + `compact`), suodatus kokonaisella sanalla Pythonissa: 6/6 löytyi, `PIPE 5 M` ja `KATTOPALKKI` hylättiin. Yksi oma virhe: kenttä `properties.insertion_point` hylättiin tyypitetyllä virheellä, joka kertoi oikean nimen (`insertion`). |
| T4 Palkki | OK | Viiva 1000,6000 → 8200,6000, `length` 7200. Mittaviivan `measurement` 7200 luettiin MCP:n `entity_get`-työkalulla (ei COM:ia). Kolmiotuet ja teksti `IPE300 S355` tasolla GEOMETRY. |
| T5 Poikkileikkaus | OK | 12 viivaa + 4 kaarta (r = 15). `entity_get`: h 300, b 150, tw 7,1, tf 10,7. Sulkeutuvuus: 16 päätepistettä, jokainen kahden osan yhteinen, ei vapaita päitä. Pinta-ala kaavalla 5381,2 mm² (taulukkoarvo 5381, ero 0,004 %). |
| T6 Taulukko | OK | `entity_create_table` (taso TEKSTI) → `AcDbTable` 3 × 5. Solut luettu COM:lla (vain luku, MCP:ssä ei solujen lukutyökalua): kaikki arvot oikein. |
| T7 Tallennus | OK | `drawing_save_as` → `C:\temp\testi_tulos.dwg` (115 999 t, korvasi 22.11. tiedoston), `document_close`, `drawing_open`. Uudelleenavauksen jälkeen GEOMETRY 29 (19 LINE, 4 ARC, 5 ROTATEDDIMENSION, 1 TEXT), TEKSTI 8 TEXT + 1 TABLE. Kaikki tallessa. |

Huomiot 3. ajosta:
- T4–T6 meni yhtenä `cad_batch`-kutsuna (31 askelta, kaikki OK).
- Mittaviivojen arvot saa nyt MCP:stä (`entity_get` → `dimension.measurement`), joten COM:ia tarvittiin vain taulukon solujen lukemiseen.
- Repon `.venv`:ssä ei ole `pywin32`:ta. COM-tarkistus ajettiin palvelimen omalla ympäristöllä: `uvx --from "autocad-mcp-pro[com,pdf]==1.8.0" python`.
- Mittatyyli ISO-25 (tekstikorkeus 2,5) on 7200 mm:n palkin rinnalla mittakaavassa 1:1 hyvin pieni. Mittaa ei tarkistettu silmämääräisesti eikä `DIST`-komennolla.

**Ympäristö:**
- AutoCAD-versio: AutoCAD 2026 (acad.exe 25.1.164.0.0, Education/non-commercial); myös 2023 asennettuna
- Windows-versio: Windows 11 Pro 10.0.26200
- `uvx --version`: uvx 0.13.9 (asennettu 2026-11-19, `autocad-mcp-pro==1.8.0`)
- Testipäivä: 2026-11-19 (1. ajo) ja 2026-11-22 (uusinta, kaikki T1–T7 OK samoin tuloksin); 2026-11-23 (3. ajo, kaikki T1–T7 OK, ks. oma taulukko yllä)
- Testipiirustus: synteettinen `C:\temp\testi_kopio.dwg` (4 tasoa, 6 profiilitekstiä + 2 harhatekstiä), ei oikea rakennepiirustus
- Muuta huomattavaa (hitaus, jumiutumiset, virheilmoitukset):
  - Uusinnassa 22.11. T4–T6 ajettiin yhtenä `cad_batch`-kutsuna (9 askelta, kaikki onnistuivat), tulokset samat kuin ensimmäisellä ajolla. T7:n `drawing_open` toimi, vaikka kaikki piirustukset oli suljettu (AutoCAD ilman avointa piirustusta).
  - Ei hitautta eikä jumiutumisia. Kaikki kutsut onnistuivat ensimmäisellä yrityksellä.
  - `analysis_list_properties` ei näytä mittaviivan mitattua arvoa eikä taulukon sisältöä. Ne luettiin AutoCADista COM:lla (vain luku) tarkistuksena.
  - `entity_create_table` käyttää oletuksena tasoa `TEXT`, jota ei ollut. Taso `TEKSTI` annettiin erikseen.
  - `cad_batch`-rollback on vain "best effort" (palvelimen oma huomautus).
  - 19.11. ennen `uv`:n asennusta AutoCAD lakkasi kerran vastaamasta COM:iin avoimen dialogin takia. Ei liity MCP-palvelimeen.
  - Kaksi avointa piirustusta (testi + `Drawing1.dwg`), `active_document_changed` pysyi `false`.
