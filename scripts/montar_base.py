"""Monta a base final para o Tableau a partir de:
  - dados/tabnet_bruto_2014_2022.csv               (TabNet/DATASUS, 2014-2022)
  - painel_2023_2025/ufs_painel_mensal_2023_2025.csv (Painel MS, 2023-2025, Brasil e UFs)
  - painel_2023_2025/municipios_PA_painel_mensal_2023_2025.csv (Painel MS, 2023-2025, municípios PA)
  - dados/idhm_para_2010.csv                        (Ipeadata/Atlas DH + IBGE localidades)
Gera em base_tableau/: cobertura_longa.csv, municipios_pa.csv, indicadores_municipais_vacina.csv,
indicadores_municipais_ano.csv, proporcao_municipios_meta.csv
Uso: python3 montar_base.py <pasta_do_trabalho>"""
import os, sys
import numpy as np
import pandas as pd

RAIZ = sys.argv[1]
SAIDA = os.path.join(RAIZ, "base_tableau")
META = 95.0
ANOS_MAPA = [2014, 2019, 2022, 2024]  # anos dos mapas comparáveis pedidos no trabalho
SOMENTE_OBRIGATORIAS = True  # False inclui BCG, Hepatite B, Febre amarela e Tríplice viral D2 (só 2014-2022)

UF = {11: ("RO", "Rondônia"), 12: ("AC", "Acre"), 13: ("AM", "Amazonas"), 14: ("RR", "Roraima"), 15: ("PA", "Pará"),
      16: ("AP", "Amapá"), 17: ("TO", "Tocantins"), 21: ("MA", "Maranhão"), 22: ("PI", "Piauí"), 23: ("CE", "Ceará"),
      24: ("RN", "Rio Grande do Norte"), 25: ("PB", "Paraíba"), 26: ("PE", "Pernambuco"), 27: ("AL", "Alagoas"),
      28: ("SE", "Sergipe"), 29: ("BA", "Bahia"), 31: ("MG", "Minas Gerais"), 32: ("ES", "Espírito Santo"),
      33: ("RJ", "Rio de Janeiro"), 35: ("SP", "São Paulo"), 41: ("PR", "Paraná"), 42: ("SC", "Santa Catarina"),
      43: ("RS", "Rio Grande do Sul"), 50: ("MS", "Mato Grosso do Sul"), 51: ("MT", "Mato Grosso"),
      52: ("GO", "Goiás"), 53: ("DF", "Distrito Federal")}
REGIAO = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste"}

# nome padronizado, dose, público-alvo, obrigatória no trabalho
VACINAS = {
    "Penta":                       ("Pentavalente", "3ª dose", "Menores de 1 ano", True),
    "Poliomielite":                ("Poliomielite", "3ª dose", "Menores de 1 ano", True),
    "Pneumocócica":                ("Pneumocócica 10V", "2ª dose", "Menores de 1 ano", True),
    "Tríplice Viral  D1":          ("Tríplice viral D1", "1ª dose", "1 ano", True),
    "Tríplice Viral  D2":          ("Tríplice viral D2", "2ª dose", "1 ano", False),
    "BCG":                         ("BCG", "Dose única", "Menores de 1 ano", False),
    "Hepatite B idade <= 30 dias": ("Hepatite B ao nascer", "Dose ao nascer (até 30 dias)", "Menores de 1 mês", False),
    "Febre Amarela":               ("Febre amarela", "1ª dose", "Menores de 1 ano", False),
    "Penta (DTP/HepB/Hib)":        ("Pentavalente", "3ª dose", "Menores de 1 ano", True),
    "Pneumocócica Conjugada":      ("Pneumocócica 10V", "2ª dose", "Menores de 1 ano", True),
    "Tríplice Viral - 1° Dose":    ("Tríplice viral D1", "1ª dose", "1 ano", True),
}


def periodo(ano):
    if ano <= 2019:
        return "1. Pré-pandemia (2014-2019)"
    if ano <= 2022:
        return "2. Pandemia (2020-2022)"
    return "3. Pós-pandemia (2023-2025)"


# ---------------- TabNet 2014-2022 ----------------
t = pd.read_csv(os.path.join(RAIZ, "dados", "tabnet_bruto_2014_2022.csv"), dtype=str)
t = t[t.ano.str.fullmatch(r"\d{4}")]
t["cobertura"] = pd.to_numeric(t.cobertura, errors="coerce")
t["codigo"] = t.territorio.str.extract(r"^(\d+)")[0]
t = t[(t.nivel == "Brasil") | t.codigo.notna()]  # descarta "ignorado/exterior" sem código
t = t[~((t.nivel == "Região") & (t.codigo == "0"))]
t["doses"] = np.nan
t["populacao"] = np.nan
t["fonte"] = "TabNet/DATASUS (SI-PNI)"
tab = t.rename(columns={"vacina_tabnet": "vacina_fonte"})[["nivel", "codigo", "vacina_fonte", "ano", "cobertura", "doses", "populacao", "fonte"]]

# ---------------- Painel 2023-2025 ----------------
u = pd.read_csv(os.path.join(RAIZ, "painel_2023_2025", "ufs_painel_mensal_2023_2025.csv"), dtype={"cod_uf": str})
u = u.rename(columns={"Doses Aplicadas": "doses", "População": "populacao"})
u["ano"] = u.mes_ano.str[:4]
ufa = u[u.cod_uf != "BR"].groupby(["vacina_painel", "ano", "cod_uf"])[["doses", "populacao"]].sum().reset_index()
ufa["regiao_cod"] = ufa.cod_uf.str[0]
partes = [ufa.assign(nivel="UF", codigo=ufa.cod_uf)]
reg = ufa.groupby(["vacina_painel", "ano", "regiao_cod"])[["doses", "populacao"]].sum().reset_index()
partes.append(reg.assign(nivel="Região", codigo=reg.regiao_cod))
br = u[u.cod_uf == "BR"].groupby(["vacina_painel", "ano"])[["doses", "populacao"]].sum().reset_index()
partes.append(br.assign(nivel="Brasil", codigo=None))
mu = pd.read_csv(os.path.join(RAIZ, "painel_2023_2025", "municipios_PA_painel_mensal_2023_2025.csv"), dtype={"cod_ibge6": str})
mu["ano"] = mu.mes_ano.str[:4]
mu = mu[mu.cod_ibge6 != "PA_TOTAL"].groupby(["vacina_painel", "ano", "cod_ibge6"])[["doses", "populacao"]].sum().reset_index()
partes.append(mu.assign(nivel="Município", codigo=mu.cod_ibge6))
p = pd.concat(partes, ignore_index=True)
p["cobertura"] = p.doses / p.populacao * 100
p["fonte"] = "Painel de Cobertura Vacinal MS (SI-PNI/RNDS)"
pan = p.rename(columns={"vacina_painel": "vacina_fonte"})[["nivel", "codigo", "vacina_fonte", "ano", "cobertura", "doses", "populacao", "fonte"]]

# ---------------- dimensão municípios ----------------
mun = pd.read_csv(os.path.join(RAIZ, "dados", "idhm_para_2010.csv"), dtype={"cod_ibge7": str, "cod_ibge6": str})
nv = pd.read_csv(os.path.join(RAIZ, "dados", "sinasc_nascidos_vivos_para_2023_2025.csv"), dtype={"co_municipio": str})
mun = mun.merge(nv[["co_municipio", "nv2023", "nv2024", "nv2025"]].rename(columns={
    "co_municipio": "cod_ibge6", "nv2023": "nascidos_vivos_2023", "nv2024": "nascidos_vivos_2024", "nv2025": "nascidos_vivos_2025_prelim"}),
    on="cod_ibge6", how="left")
mun["porte_nascidos_vivos"] = pd.cut(mun.nascidos_vivos_2024, [0, 200, 500, 1500, np.inf],
                                     labels=["Até 200", "201-500", "501-1.500", "Mais de 1.500"])
nome_mun = dict(zip(mun.cod_ibge6, mun.municipio))

# ---------------- tabela longa ----------------
f = pd.concat([tab, pan], ignore_index=True)
f["ano"] = f.ano.astype(int)
f["vacina"] = f.vacina_fonte.map(lambda v: VACINAS[v][0])
f["dose"] = f.vacina_fonte.map(lambda v: VACINAS[v][1])
f["publico_alvo"] = f.vacina_fonte.map(lambda v: VACINAS[v][2])
f["vacina_obrigatoria"] = f.vacina_fonte.map(lambda v: "Sim" if VACINAS[v][3] else "Não (complementar)")
if SOMENTE_OBRIGATORIAS:
    f = f[f.vacina_obrigatoria == "Sim"]


def cod_uf(r):
    if r.nivel == "UF":
        return int(r.codigo)
    if r.nivel == "Município":
        return int(r.codigo[:2])
    return np.nan


f["cod_uf"] = f.apply(cod_uf, axis=1)
f["sigla_uf"] = f.cod_uf.map(lambda c: UF[int(c)][0] if c == c else None)
f["regiao"] = np.where(f.nivel == "Região", f.codigo.map(lambda c: REGIAO.get(int(c)) if isinstance(c, str) else None),
                       f.cod_uf.map(lambda c: REGIAO[int(c) // 10] if c == c else None))
f["territorio"] = np.select(
    [f.nivel == "Brasil", f.nivel == "Região", f.nivel == "UF"],
    ["Brasil", f.regiao, f.cod_uf.map(lambda c: UF[int(c)][1] if c == c else None)],
    default=f.codigo.map(nome_mun))
f["cod_territorio"] = np.where(f.nivel == "Brasil", "BR", f.codigo)
f["cod_ibge7"] = np.where(f.nivel == "Município", f.codigo.map(dict(zip(mun.cod_ibge6, mun.cod_ibge7))), None)
f["ordem_nivel"] = f.nivel.map({"Brasil": 1, "Região": 2, "UF": 3, "Município": 4})
f["periodo"] = f.ano.map(periodo)
f["ano_mapa"] = np.where(f.ano.isin(ANOS_MAPA), "Sim", "Não")
f["cobertura"] = f.cobertura.round(2)
f["cobertura_valida"] = np.where(f.cobertura.notna() & (f.cobertura > 0), "Sim", "Não")
f["meta_atingida"] = np.where(f.cobertura_valida == "Não", None, np.where(f.cobertura >= META, "Sim", "Não"))
f["distancia_meta_pp"] = (f.cobertura - META).round(2)
f["quebra_serie"] = np.where(f.ano >= 2023, "Após mudança para RNDS (2023+)", "Antes (até 2022)")
f["dado_provisorio"] = np.where(f.ano == 2025, "Sim", "Não")
f = f.sort_values(["ordem_nivel", "cod_territorio", "vacina", "ano"])
# cobertura do ano anterior e variação anual
f["cobertura_ano_anterior"] = f.groupby(["nivel", "cod_territorio", "vacina"]).cobertura.shift()
f.loc[f.groupby(["nivel", "cod_territorio", "vacina"]).ano.diff() != 1, "cobertura_ano_anterior"] = np.nan
f["variacao_anual_pp"] = (f.cobertura - f.cobertura_ano_anterior).round(2)

cols = ["nivel", "ordem_nivel", "cod_territorio", "cod_ibge7", "territorio", "sigla_uf", "cod_uf", "regiao",
        "ano", "periodo", "ano_mapa", "vacina", "dose", "publico_alvo", "vacina_obrigatoria", "vacina_fonte",
        "cobertura", "doses", "populacao", "cobertura_valida", "meta_atingida", "distancia_meta_pp",
        "cobertura_ano_anterior", "variacao_anual_pp", "fonte", "quebra_serie", "dado_provisorio"]
f = f[cols]
f["cod_uf"] = f.cod_uf.astype("Int64")
f["cod_ibge7"] = f.cod_ibge7.astype("string")

# ---------------- indicadores municipais ----------------
m = f[(f.nivel == "Município") & (f.cobertura_valida == "Sim")].copy()
m["na_meta"] = (m.cobertura >= META).astype(int)

# por município x vacina
def var(g, a, b):
    s = g.set_index("ano").cobertura
    return round(s[b] - s[a], 2) if a in s.index and b in s.index else np.nan

linhas = []
for (cod, vac), g in m.groupby(["cod_territorio", "vacina"]):
    linhas.append({
        "cod_ibge6": cod, "vacina": vac, "vacina_obrigatoria": g.vacina_obrigatoria.iloc[0],
        "anos_com_dado": len(g), "primeiro_ano": g.ano.min(), "ultimo_ano": g.ano.max(),
        "anos_na_meta": int(g.na_meta.sum()), "anos_abaixo_meta": int((1 - g.na_meta).sum()),
        "pct_anos_abaixo_meta": round((1 - g.na_meta).mean() * 100, 1),
        "cobertura_media": round(g.cobertura.mean(), 2),
        "cobertura_minima": g.cobertura.min(), "cobertura_maxima": g.cobertura.max(),
        "var_2014_2019_pp": var(g, 2014, 2019), "var_2019_2022_pp": var(g, 2019, 2022),
        "var_2022_2024_pp": var(g, 2022, 2024), "var_2014_2024_pp": var(g, 2014, 2024),
        "var_2023_2025_pp": var(g, 2023, 2025),
    })
iv = pd.DataFrame(linhas)
iv["classificacao_persistencia"] = pd.cut(iv.pct_anos_abaixo_meta, [-0.1, 0, 50, 99.9, 100],
                                          labels=["Sempre na meta", "Abaixo ocasionalmente", "Abaixo na maioria dos anos", "Sempre abaixo"])
iv["municipio"] = iv.cod_ibge6.map(nome_mun)

# por município x ano (número de vacinas obrigatórias na meta)
ob = m[m.vacina_obrigatoria == "Sim"]
ia = ob.groupby(["cod_territorio", "ano"]).agg(vacinas_obrigatorias_com_dado=("vacina", "nunique"),
                                               n_vacinas_na_meta=("na_meta", "sum")).reset_index()
ia = ia.rename(columns={"cod_territorio": "cod_ibge6"})
ia["classe_vacinas_na_meta"] = ia.n_vacinas_na_meta.astype(int).astype(str) + " de " + ia.vacinas_obrigatorias_com_dado.astype(str)
ia["todas_4_na_meta"] = np.where(ia.n_vacinas_na_meta == 4, "Sim", "Não")
ia["periodo"] = ia.ano.map(periodo)
ia["municipio"] = ia.cod_ibge6.map(nome_mun)

# proporção de municípios do Pará na meta (ano x vacina)
pr = m.groupby(["ano", "vacina", "vacina_obrigatoria"]).agg(municipios_com_dado=("cod_territorio", "nunique"),
                                                            municipios_na_meta=("na_meta", "sum")).reset_index()
pr["pct_municipios_na_meta"] = (pr.municipios_na_meta / pr.municipios_com_dado * 100).round(1)
pr["periodo"] = pr.ano.map(periodo)

os.makedirs(SAIDA, exist_ok=True)
f.to_csv(os.path.join(SAIDA, "cobertura_longa.csv"), index=False)
mun.to_csv(os.path.join(SAIDA, "municipios_pa.csv"), index=False)
iv.to_csv(os.path.join(SAIDA, "indicadores_municipais_vacina.csv"), index=False)
ia.to_csv(os.path.join(SAIDA, "indicadores_municipais_ano.csv"), index=False)
pr.to_csv(os.path.join(SAIDA, "proporcao_municipios_meta.csv"), index=False)

print("cobertura_longa:", f.shape)
print(f.groupby(["nivel", "fonte"]).agg(territorios=("cod_territorio", "nunique"), anos=("ano", "nunique"),
                                        vacinas=("vacina", "nunique"), linhas=("ano", "size")).to_string())
print("municipios_pa:", mun.shape, "| ind. vacina:", iv.shape, "| ind. ano:", ia.shape, "| proporção:", pr.shape)
