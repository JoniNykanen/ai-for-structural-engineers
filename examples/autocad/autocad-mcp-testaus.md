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
| T1 Yhteys | | |
| T2 Tasot | | |
| T3 Profiilitekstit | | |
| T4 Palkki | | |
| T5 Poikkileikkaus | | |
| T6 Taulukko | | |
| T7 Tallennus | | |

**Ympäristö:**
- AutoCAD-versio:
- Windows-versio:
- `uvx --version`:
- Testipäivä:
- Muuta huomattavaa (hitaus, jumiutumiset, virheilmoitukset):
