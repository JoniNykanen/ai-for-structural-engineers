# 11 — Eurocode + Suomen NA: normipohjainen mitoitus (eurocode-fi)

*Ammattikäyttöön (myös opiskelijoille): tekoäly tuottaa normienmukaisia
rakennelaskuja, jotka **siteeraavat pykälän, näyttävät laskun ja ovat
tarkistettavissa** — ilman tekijänoikeudellista normitekstiä.*

## Idea

Rakennesuunnittelussa laskennan pitää olla normienmukaista ja **jäljitettävää**.
Tämä moduuli pakottaa Clauden:
1. **siteeraamaan pykälän** (esim. "EN 1995-1-1 §6.1.6"),
2. **näyttämään kaava → sijoitus → tulos yksiköineen → käyttöaste**,
3. **ei koskaan keksimään normiarvoa** — arvot tulevat sinun parametritiedostostasi,
4. **tarkistamaan tuloksen riippumattomasti** (verifiointitaso 2).

## Tekijänoikeus (tärkeä)

Repo **ei sisällä** Eurocode/SFS-NA:n tekstiä tai taulukoita — ne ovat CEN:n/SFS:n
tekijänoikeuden alaisia. Koodi sisältää vain **pykäläviittaukset** (numerot ovat
faktoja) ja **julkiset insinöörikaavat**. Kaikki normikohtaiset **arvot**
(γM, kmod, kdef, kcr, ψ, lujuudet, taipumarajat) syötät itse lisensoidusta
normistasi parametritiedostoon.

## Parametritiedosto

```bash
cp params/na_timber.example.yaml params/na_timber.yaml
```
- `params/na_timber.example.yaml` — **committoitu** pohja: tyhjät kentät +
  pykäläviittaukset mistä arvo löytyy.
- `params/na_timber.yaml` — **gitignore**, sinä täytät. Lisensoidut arvosi
  pysyvät koneellasi.

Puuttuva arvo → työkalu **pysähtyy** ja kertoo mikä kenttä ja pykälä täyttää.
Ei arvausta.

**Kuormayhdistelmät (EN 1990 6.10a/6.10b).** `glulam_beam_ec5.py` laskee kaksi
ULS-yhdistelmää ja valitsee määräävän suurimman `q_d / k_mod` -suhteen mukaan:
- **6.10a** — vain pysyvä kuorma, kerroin `actions.gamma_G_610a`, `k_mod.permanent`
- **6.10b** — pysyvä + lumi, kertoimet `actions.gamma_G_610b` ja `actions.gamma_Q`,
  `k_mod` lumen aikaluokan mukaan

**Lumen aikaluokka** on normivalinta (EN 1995-1-1 Table 2.2 + SFS-NA), joten se
on parametritiedostossa: `actions.snow_duration: long_term` tai `medium_term`.
Valittu luokka näkyy laskumuistiossa.

Jos parametritiedoston kommenteissa lukee `DUMMY` tai `TEST` (esim.
`tests/fixtures/na_timber.test.yaml`), laskumuistio sanoo sen eikä väitä arvoja
lisensoidusta normista otetuiksi.

## Verifiointi (taso 2)

Jokainen lasku (a) dokumentoi itsensä pykäläviittauksin ja (b) **lasketaan
riippumattomasti uudelleen eri menetelmällä** (esim. momentti numeerisella
integroinnilla vs. suljettu muoto), ja tulokset verrataan toleranssin sisällä.
`glulam_beam_ec5.py` tulostaa `Ristiintarkistus: OK` tai eron. Skill ohjaa Clauden
toimimaan tarkastajana, joka yrittää löytää virheen — ei kumileimasin.

## Käyttö

1. Täytä `params/na_timber.yaml`.
2. Aja esimerkki tai pyydä Claudelta lasku suomeksi:
   ```
   Mitoita liimapuupalkki EN 1995-1-1 + SFS-NA mukaan: L=6 m, GL30c, g_k=3 kN/m,
   lumi s_k=6 kN/m, poikkileikkaus 140x450. Näytä pykälät, käyttöasteet ja tee
   riippumaton ristiintarkistus.
   ```
   Claude käyttää **`eurocode-fi`-skilliä**, lukee `params/`-arvot ja tuottaa
   sekä laskumuistion että ajettavan skriptin.

## Nykytila ja laajennus
- Toteutettu: **puu (EN 1995-1-1)**. Framework on yleiskäyttöinen.
- Tulossa omina paloinaan: teräs (EN 1993), betoni (EN 1992), kuormat (EN 1990/1991).
- Epävarmasta pykälästä: käytä `autodesk-product-help` MCP:tä tai omia lisensoituja
  PDF:iäsi.

## Vastuu
Työkalu on **apuväline**. Suunnittelija vastaa tuloksista. Arvot käyttäjän
lisensoidusta normista. **Ei korvaa** EN 1995-1-1 / SFS-NA:ta.

## Liittyvät
- Skill: `.claude/skills/eurocode-fi/SKILL.md`
- Esimerkki: [`examples/eurocode/timber/`](../examples/eurocode/timber/)
- Suunnitteludokumentti: `docs/superpowers/specs/2026-09-13-eurocode-fi-design.md`
