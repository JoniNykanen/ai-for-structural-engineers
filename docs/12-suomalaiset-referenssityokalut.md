# 12 — Suomalaiset ilmaiset referenssi- ja validointityökalut

*Käytä näitä eurocode-fi-laskujen **riippumattomaan ristiintarkistukseen** ja
referenssinä. Linkit ja kuvaukset vain — sisältöä (kaavoja, RIL/normidataa) ei
kopioida tähän repoon tekijänoikeussyistä. Käytä työkaluja "mustana laatikkona".*

## Puuinfo — ilmaiset puurakenteiden mitoitustyökalut (EC5 / RIL 205)

Kokoelmasivu: <https://puuinfo.fi/suunnittelu/mitoitustyokalu/>

Nämä ovat auktoritatiivisia suomalaisia referenssitoteutuksia. Erityisen
hyödyllisiä ristiintarkistukseen, koska ne kattavat samat tapaukset kuin repon
puu-esimerkit:

| Työkalu | Mitä laskee | Muoto | Linkki |
|---|---|---|---|
| **Suoran liimapuupalkin mitoitus** | Suora liimapuupalkki (RIL 205-1-2017) — vastaa `glulam_beam_ec5.py`:tä | Excel | <https://puuinfo.fi/suunnittelu/mitoitustyokalu/suoran-liimapuupalkin-mitoitus/> |
| **Liimapuumahapalkin mitoitus** | Kaareva mahapalkki — vastaa repon `mahapalkki`-esimerkkiä | Excel | <https://puuinfo.fi/suunnittelu/mitoitustyokalu/liimapuumahapalkin-mitoitus/> |
| **Liimapuupilarin mitoitus** | Liimapuupilari | Excel | <https://puuinfo.fi/suunnittelu/mitoitustyokalu/liimapuupilarin-mitoitus/> |
| **Liimapuuharjapalkin mitoitus** | Harjapalkki | Excel | <https://puuinfo.fi/suunnittelu/mitoitustyokalu/liimapuuharjapalkin-mitoitus/> |
| **Finnwood 2.4.3** | Puutuotteiden (LVL ym.) mitoitus EC5 | Ohjelma | <https://puuinfo.fi/suunnittelu/mitoitustyokalu/finnwood-mitoitusohjelma/> |
| **Palkkivälipohjan värähtely** | Välipohjan värähtely (RIL 205-1) | Excel | <https://puuinfo.fi/suunnittelu/mitoitustyokalu/palkkivalipohjan-varahtelymitoitusohjelma/> |
| **Palomitoitus** (kantava seinä / osastoivuus / palkisto) | Puurakenteiden palomitoitus (RIL 205-2-2019) | Excel | ks. kokoelmasivu |
| **Jäykistys** (hirsiseinä / levy / NR-yläpohja) | Rakenteiden jäykistys | Excel | ks. kokoelmasivu |

Kaikki ilmaisia (Puuinfo Oy). Perustuvat RIL 205 -ohjeisiin → älä kopioi niiden
sisältöä; **vertaa tuloksia**.

## DOF — D.O.F. tech Oy (varauksella)

<https://www.dof.fi/>

- **DOF-Teräs** — teräspalkki/-pilari, mutta **RakMK B7:n mukaan** (vanha,
  Eurocodea edeltävä Suomen normi). Nykyiseen EN 1993 -suunnitteluun osin
  **vanhentunut**. Työpöytäohjelma, **ei rajapintaa** → vain viite, ei
  integroitavissa.
- **DOF-Puu** — puumitoitus (legacy-normit). Vastaava varaus.

**Suositus:** DOF vain historiallisena/viitteenä. Nykysuunnitteluun luota
EN-normeihin ja eurocode-fi-moduuliin; teräkselle tulossa oma EN 1993 -vertikaali.

## Miten käytät näitä ristiintarkistukseen

1. Laske eurocode-fi:llä (repo) → saat käyttöasteet + laskumuistion.
2. Aja sama tapaus Puuinfon vastaavalla ilmaistyökalulla.
3. Vertaa avaintulokset (käyttöasteet, taipumat). Ero → tarkista syöte ja
   oletukset. Tämä on konkreettinen **taso 2 -verifiointi** (ks.
   [docs/11](11-eurocode-fi.md)).

> Työkalut ovat apuvälineitä; suunnittelija vastaa tuloksista. Linkit voivat
> muuttua — tarkista Puuinfon kokoelmasivulta.
