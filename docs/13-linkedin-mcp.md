# 13 — LinkedIn MCP (lue omat postauksesi Claudeen)

*Valinnainen, henkilökohtainen liitäntä. Antaa Claudelle pääsyn **omiin
LinkedIn-postauksiisi** LinkedInin **virallisella OAuth-API:lla** (ei scrapea).
Käyttötarkoitus tässä: Claude oppii kirjoitustyylisi ja voi luonnostella sinun
äänelläsi. Read-only — ei automaattista julkaisua.*

> ⚠️ **Kolmannen osapuolen open-source-serveri**
> ([jahnavi-yarramsetty/linkedin-mcp-server](https://github.com/jahnavi-yarramsetty/linkedin-mcp-server)),
> ei Anthropicin virallinen. Se on avoin ja ajetaan paikallisesti; token
> tallentuu vain koneellesi (`~/.linkedin_mcp_token.json`, 60 vrk). Kloonaus,
> creds ja rekisteröinti ovat **konekohtaisia — niitä ei committoida tähän repoon.**

## ⚠️ Iso este ennen kuin aloitat
Omien postausten luku vaatii scope-oikeuden **`r_member_social`**, joka kuuluu
LinkedInin **Community Management API**:in. LinkedIn **portittaa** sen: sovelluksesi
pitää **hakea ja saada hyväksyntä** tuotteelle. Ilman sitä `get_my_posts` voi
palauttaa 403. Tämä voi kestää tai jäädä epäämättä pienelle sovellukselle. Jos
haluat vain nopeasti tyylinäytteen, **postausten liittäminen chattiin on yhä
nopein reitti** — tämä liitäntä kannattaa vain jos aiot käyttää LinkedIniä
Claudessa toistuvasti.

## 1. Luo LinkedIn-sovellus
1. <https://www.linkedin.com/developers/apps> → **Create app**.
2. **Auth** → lisää *Authorized redirect URL*: `http://localhost:8000/callback`
   (täsmälleen sama kuin alla).
3. **Products** → ota käyttöön:
   - *Sign In with LinkedIn using OpenID Connect* (`openid`, `profile`, `email`)
   - *Community Management API* (`r_member_social` — postausten luku; **vaatii hyväksynnän**)
4. Kopioi **Client ID** ja **Client Secret**.

## 2. Palvelin (jo asennettu tälle koneelle)
Kloonattu: `~/linkedin-mcp-server`, oma venv + riippuvuudet (`fastmcp`, `httpx`,
`python-dotenv`). Jos teet toisella koneella:
```bash
git clone https://github.com/jahnavi-yarramsetty/linkedin-mcp-server.git ~/linkedin-mcp-server
cd ~/linkedin-mcp-server
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt    # Win; mac/linux: .venv/bin/python
```

## 3. Rekisteröi Claude Codeen (creds `-e`:llä)
Anna creds suoraan rekisteröinnissä — palvelin lukee ne ympäristöstä (luotettavampi
kuin `.env`, koska palvelin lukee muuttujat heti käynnistyessä):

```bash
claude mcp add linkedin -s local \
  -e LINKEDIN_CLIENT_ID=<oma_client_id> \
  -e LINKEDIN_CLIENT_SECRET=<oma_client_secret> \
  -e LINKEDIN_REDIRECT_URI=http://localhost:8000/callback \
  -- "C:\Users\jonin\linkedin-mcp-server\.venv\Scripts\python.exe" \
     "C:\Users\jonin\linkedin-mcp-server\server.py"
```
(mac/Linux: käytä `.venv/bin/python`.) Tarkista: `claude mcp list`.

## 4. Valtuuta ja käytä
1. **Käynnistä Claude Code uudelleen** repossa.
2. Sano sessiossa: **"Call authenticate"** → selain avaa LinkedIn-OAuth:n → hyväksy.
   Token tallentuu `~/.linkedin_mcp_token.json`.
3. Pyydä esim.: *"Hae 5 viimeisintä postaustani ja analysoi kirjoitustyylini."*

## Työkalut (read-only)
`authenticate`, `check_auth_status`, `get_profile`, `get_my_posts(count)`,
`get_my_articles(count)`, `get_post_detail(post_id)`, `revoke_auth`.

## Huomiot
- **Token vanhenee 60 vrk**, ei refreshiä → aja `revoke_auth` + `authenticate` uudelleen.
- **Redirect-URL:n oltava täsmälleen sama** sovelluksessa ja rekisteröinnissä.
- Poisto: `claude mcp remove linkedin -s local`.
- Ei julkaisua — postaat itse; tämä vain lukee.

## Kun tämä toimii
Claude voi lukea postauksesi → **kirjoitan sinulle LinkedIn-vedokset omalla
tyylilläsi** (rytmi, aloitukset, emoji/hashtag-tavat). Siihen asti: liitä pari
postausta chattiin.
