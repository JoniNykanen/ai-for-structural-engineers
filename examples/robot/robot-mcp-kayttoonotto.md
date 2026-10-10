# Robot MCP – käyttöönotto

Tällä ohjeella saat Clauden ohjaamaan Autodesk Robot Structural Analysisia
samalla tavalla kuin MATLABia: Claude rakentaa mallin, laskee sen ja lukee
tulokset suoraan Robotista.

Laajempi englanninkielinen ohje: [docs/14 – Robot MCP](../../docs/14-robot-mcp.md).

## Mitä tarvitset

- Windows 10 tai 11
- Autodesk Robot Structural Analysis Professional asennettuna ja lisensoituna
  (opiskelijat saavat ilmaisen Autodeskin opetuslisenssin)
- Python 3.10 tai uudempi
- Git ja Claude Code

## Käyttöönotto

**1. Käynnistä Robot kerran.** Avaa Robot Käynnistä-valikosta ja anna sen
suorittaa ensikäynnistys loppuun. Sulje se sen jälkeen.

**2. Aja asennusskripti** repon juurikansiossa PowerShellissä:

```powershell
./setup.ps1
```

Skripti tunnistaa Robotin ja asentaa MCP-palvelimen kansioon `tools/rsap-mcp/`.
Jos Robot asennettiin vasta myöhemmin tai skripti ei löydä sitä, pakota asennus:

```powershell
./setup.ps1 -WithRobot
```

Onnistuessaan skripti tulostaa rivin `[selfcheck] 35 tools registered`.

**3. Käynnistä Claude Code uudelleen** repon kansiossa. Claude kysyy, saako
projektin `robot`-palvelimen ottaa käyttöön. Hyväksy se. Hyväksynnän voi tehdä
myös komennolla `/mcp`.

**4. Tarkista yhteys:**

```bash
claude mcp list
```

Listassa pitää näkyä `robot: ... - ✔ Connected`.

## Ensimmäinen kokeilu

Kirjoita Claudelle esimerkiksi:

> Käytä robot-MCP:tä: tee uusi 2D-kehä, 6 m vapaasti tuettu IPE 240 -palkki,
> teräs S355, tasainen kuorma 10 kN/m ja oma paino. Laske ja kerro suurin
> momentti, tukireaktiot ja taipuma keskellä. Tarkista lopuksi suurin momentti
> käsin kaavalla wL²/8.

Claude käyttää `rsap_*`-työkaluja: luo solmut ja sauvat, asettaa profiilin,
materiaalin, tuet ja kuormat, laskee mallin ja lukee tulokset.

## Muista nämä

- **Yksiköt.** Palvelin käyttää aina perusyksiköitä: m, N ja N·m. Robotin näytöllä
  voi silti näkyä kN. Jos luet N·m-arvon kN·m:nä, tulos on tuhat kertaa väärin,
  eikä virhettä huomaa päältä. Tarkista yksiköt joka kerta.
- **Tarkista tulokset.** MCP estää Claudea keksimästä olemattomia Robot-komentoja,
  mutta mallinnusvirheiltä se ei suojaa. Vertaa tulosta käsilaskuun, Pythoniin tai
  eurocode-fi-tarkistukseen ([docs/11](../../docs/11-eurocode-fi.md)).
- **Palvelin voi muuttaa malleja.** Se pystyy luomaan, muokkaamaan ja
  tallentamaan malleja. Kokeile oikeiden projektien kopioilla.
- **Kyseessä on ulkopuolisen tekijän palvelin**
  ([nhantruong96/rsap-mcp](https://github.com/nhantruong96/rsap-mcp), MIT-lisenssi),
  ei Autodeskin. Se on lukittu tarkistettuun versioon `08ab805`.
- **Kokeiltu Robot 2027:llä.** Mallin rakentaminen, kuormat, yhdistelmät,
  lineaarinen ja epälineaarinen laskenta sekä tulosten luku toimivat.
  Nurjahdusanalyysia, sauvojen vapautuksia ja kuormien poistoa ei voi tehdä
  työkaluilla. Kiertotiet ja sudenkuopat:
  [docs/14, Field-tested notes](../../docs/14-robot-mcp.md#field-tested-notes).
- **Älä poista ja luo sauvoja uudelleen annetussa mallissa.** Sauvojen
  vapautukset katoavat ilman virheilmoitusta, eikä niitä saa työkaluilla takaisin.

## Vianetsintä

| Ongelma | Ratkaisu |
|---|---|
| `robot` puuttuu listasta | Käynnistä Claude Code uudelleen repon juurikansiossa |
| `✘ Failed to connect` | Palvelinta ei ole asennettu: aja `./setup.ps1 -WithRobot` |
| Työkalu ilmoittaa, ettei yhteyttä Robotiin saada | Käynnistä Robot kerran Käynnistä-valikosta ja yritä uudelleen |
| Tulokset tuhatkertaisia | Yksikkösekaannus N ↔ kN, katso kohta *Yksiköt* yllä |
