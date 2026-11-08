"""Coleta cobertura vacinal 2014-2022 do TabNet (bd_pni/cpnibr.def).
Cada consulta (nível x vacina) é salva na pasta de brutos; rodar de novo retoma o que faltou.
Uso: python3 coleta_tabnet.py <pasta_brutos> <saida.csv>"""
import re, sys, time, csv, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
import tabnet

BRUTOS, OUT = sys.argv[1], sys.argv[2]
VACINAS = ["Penta", "Poliomielite", "Pneumocócica", "Tríplice Viral  D1", "Tríplice Viral  D2",
           "BCG", "Hepatite B idade <= 30 dias", "Febre Amarela"]
ANOS = list(range(2014, 2023))
NIVEIS = [("Região", "Região", None),
          ("UF", "Unidade da Federação", None),
          ("Município", "Município", {"SUnidade da Federação": ["Pará"]})]


def parse(page):
    cols = [c.strip() for c in re.findall(r"addColumn\('[^']*',\s*'([^']*)'", page)]
    rows = []
    for m in re.finditer(r'\["([^"]+)"\s*((?:,\s*\{v:[^}]*\}\s*)+)\]', page):
        vals = re.findall(r"\{v:\s*([^,]*?)\s*,f:\s*'([^']*)'\}", m.group(2))
        rows.append((m.group(1).strip(), [v for v, f in vals]))
    return cols, rows


def arquivo(nivel, vac):
    return os.path.join(BRUTOS, re.sub(r"\W+", "_", f"{nivel}_{vac}").strip("_") + ".html")


def baixa(tarefa):
    nivel, linha, filtro, vac = tarefa
    f = arquivo(nivel, vac)
    if os.path.exists(f) and parse(open(f, encoding="utf-8").read())[1]:
        return f"{nivel} {vac}: já existia"
    for tent in range(6):
        try:
            page = tabnet.query(linha, "Ano", vac, ANOS, filtro)
            if parse(page)[1]:
                open(f, "w", encoding="utf-8").write(page)
                return f"{nivel} {vac}: ok"
        except Exception as e:
            print("retry", nivel, vac, type(e).__name__, flush=True)
        time.sleep(20)
    return f"{nivel} {vac}: FALHOU"


os.makedirs(BRUTOS, exist_ok=True)
tarefas = [(n, l, f, v) for n, l, f in NIVEIS for v in VACINAS]
with ThreadPoolExecutor(3) as ex:
    for r in ex.map(baixa, tarefas):
        print(r, flush=True)

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["nivel", "territorio", "vacina_tabnet", "ano", "cobertura"])
    for nivel, linha, filtro, vac in tarefas:
        f = arquivo(nivel, vac)
        if not os.path.exists(f):
            continue
        cols, rows = parse(open(f, encoding="utf-8").read())
        for terr, vals in rows:
            if terr == "Total" and nivel != "Região":
                continue
            for a, v in zip(cols[1:], vals):
                if a == "Total":
                    continue
                w.writerow(["Brasil" if terr == "Total" else nivel, terr, vac, a, v])
