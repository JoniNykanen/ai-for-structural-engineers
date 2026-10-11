# Revit MCP – käyttöönotto

Tällä ohjeella Claude pystyy lukemaan avoinna olevaa Revit-mallia: se hakee
mallista esimerkiksi kantavat palkit, niiden jännevälit ja poikkileikkausarvot
ja laskee ne repon Python-työkaluilla.

Laajempi englanninkielinen ohje: [docs/17 – Revit MCP](../../docs/17-revit-mcp.md).

## Mitä tarvitset

- Windows ja Revit 2027 (kirjoitustyökaluihin vähintään päivitys 2027.2)
- Autodeskin Revit MCP Server -lisäosa (Technical Preview)
- Claude Code ja tämä repo asennettuna (`./setup.ps1`)

## Käyttöönotto

**1. Asenna lisäosa.** Autodesk Account → *Products and Services* →
*Product Updates* → suodata *Revit 2027* → *Add-ons*. Asenna yksi versio:
*Read-Tools* (vain luku) tai *Write-Tools* (luku ja muokkaus). Repon
`.mcp.json` osoittaa Write-Tools-versioon. Jos asennat Read-Toolsin, vaihda
polussa `Write-Tools` → `Read-Tools`.

**2. Käynnistä Revit uudelleen.** Lisäosa latautuu vain Revitin käynnistyessä.
Jos Revit oli auki asennuksen aikana, palvelin ei löydä sitä. Jos Revit kysyy
lisäosasta, valitse *Always Load*.

**3. Avaa malli** ja sulje kaikki dialogit. Jätä Revit *Modify*-tilaan, koska
palvelin ei vastaa, kun jokin komento on kesken.

**4. Käynnistä Claude Code uudelleen** repon kansiossa ja hyväksy
`revit`-palvelin.

## Kokeile

> *"Hae revit MCP:llä avoimesta mallista kantavat palkit, valitse yksi
> teräspalkki, lue sen jänneväli ja tyypin poikkileikkausarvot, tallenna ne
> JSONiksi ja aja `examples/revit/check_revit_beam.py` kuormalla 10 kN/m."*

## Muista

- **Yksiköt:** käytä `value`-kenttää, joka on Revitin sisäisissä yksiköissä
  eli jaloissa (1 ft = 0,3048 m). `displayValue` on pelkkää muotoiltua tekstiä.
- **Poikkileikkausarvot ovat tyypissä**, eivät palkkiyksilössä. Hae tiedot
  tyypin id:llä.
- **Tarkista BIM-data.** Autodeskin omassa esimerkkimallissa tyypin *W18x55*
  jäykkyysarvot ovat W12X26:n, joten taipuma tulisi 4,3-kertaiseksi.
  `check_revit_beam.py` huomaa tämän.
- **Mallissa ei ole kuormia.** Kuorma ja tuennat ovat omia oletuksiasi, ja ne
  on kerrottava tuloksen yhteydessä.
- **Kirjoitustyökalut muuttavat mallia.** Käytä kopiota ja tarkista jokainen
  muutos `review_changes`-työkalulla.
- **Opetuslisenssi:** tuloksia ei saa käyttää kaupallisesti.
