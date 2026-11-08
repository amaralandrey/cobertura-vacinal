import re, sys, requests, html
DEF = "bd_pni/cpnibr.def"
BASE = "http://tabnet.datasus.gov.br/cgi/"
import os
FORM = os.path.join(os.path.dirname(__file__), "..", "cpnibr.html")
S = open(FORM, encoding="utf8").read()

def options(name):
    m = re.search(r'<select[^>]*name="%s"[^>]*>(.*?)</select>' % re.escape(name), S, re.I | re.S)
    return [(html.unescape(v), html.unescape(t).strip()) for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', m.group(1), re.I)]

def query(linha, coluna, incremento, anos, filtros=None):
    def pick(name, label):
        for v, t in options(name):
            if t == label or v.startswith(label + "|"):
                return v
        raise KeyError((name, label))
    data = [("Linha", pick("Linha", linha)), ("Coluna", pick("Coluna", coluna)),
            ("Incremento", pick("Incremento", incremento))]
    for a in anos: data.append(("PAno", pick("PAno", str(a))))
    for sel in re.findall(r'<select[^>]*name="(S[^"]+)"', S, re.I):
        vals = (filtros or {}).get(sel)
        if vals:
            for v in vals: data.append((sel, pick(sel, v)))
        else:
            data.append((sel, "TODAS_AS_CATEGORIAS__"))
    data += [("nomedef", DEF), ("grafico", "")]
    body = "&".join(requests.utils.quote(k, safe="", encoding="latin1") + "=" + requests.utils.quote(v, safe="", encoding="latin1") for k, v in data)
    r = requests.post(BASE + "webtabx.exe?" + DEF, data=body.encode("ascii"),
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=120)
    r.encoding = "latin1"
    return r.text

if __name__ == "__main__":
    print(query("Unidade da Federação", "Ano", "Penta", [2020, 2021, 2022])[:6000])
