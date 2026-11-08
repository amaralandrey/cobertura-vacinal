# Cobertura vacinal infantil: Brasil, regiões, UFs e municípios do Pará (2014–2025)

Base de dados do trabalho de painéis no Tableau.

## Use no Tableau: pasta `base_tableau/`

| Arquivo | Grão (uma linha por) | Uso |
|---|---|---|
| `cobertura_longa.csv` | território × ano × vacina | Tabela principal: evolução, comparações e mapas |
| `municipios_pa.csv` | município do Pará | Dimensão: IDHM 2010, regiões IBGE, nascidos vivos |
| `indicadores_municipais_vacina.csv` | município × vacina | Persistência abaixo da meta e variações em p.p. |
| `indicadores_municipais_ano.csv` | município × ano | Número de vacinas obrigatórias na meta (0 a 4) |
| `proporcao_municipios_meta.csv` | ano × vacina | % de municípios do Pará na meta |
| `dicionario_variaveis.csv` | variável | Dicionário de variáveis |

Relacionamentos sugeridos no Tableau (aba Fonte de dados, "Relacionamentos", não junções):

- `cobertura_longa.cod_territorio` = `municipios_pa.cod_ibge6`
- `municipios_pa.cod_ibge6` = `indicadores_municipais_vacina.cod_ibge6`
- `municipios_pa.cod_ibge6` = `indicadores_municipais_ano.cod_ibge6`

Cuidados:

1. Filtre sempre por `nivel` (Brasil, Região, UF ou Município). A tabela principal tem todos os níveis juntos.
2. Use `cobertura` com agregação MÉDIA ou ATRIBUTO, nunca SOMA.
3. Mapas: a pasta `mapas/` traz GeoJSON do IBGE. Ligue `ufs_BR.geojson` pelo campo `codarea` = `cod_uf` e `municipios_PA.geojson` pelo campo `codarea` = `cod_ibge7`.

## Fontes

| Período | Fonte | Observação |
|---|---|---|
| 2014–2022 | TabNet/DATASUS, Imunizações – Cobertura (`bd_pni/cpnibr.def`), SI-PNI | Só a porcentagem de cobertura; última atualização em maio/2023 |
| 2023–2025 | Painel de Cobertura Vacinal do Ministério da Saúde (infoms.saude.gov.br), exportado manualmente | Doses e população mensais; cobertura anual = soma das doses ÷ soma da população |
| IDHM | Atlas do Desenvolvimento Humano (PNUD/IPEA/FJP), via API do Ipeadata | Censo 2010, o último disponível |
| Nascidos vivos | SINASC, via TabNet | 2025 preliminar |
| Territórios e mapas | IBGE, API de localidades e de malhas | — |

Conferências feitas:

- No painel, a cobertura anual calculada bate exatamente com o valor acumulado de dezembro publicado para o Brasil.
- A soma das regiões é igual ao Brasil.
- A soma dos 144 municípios é igual ao Pará.

## Limitações (citar no trabalho)

- **Quebra de série em 2023:** os registros passaram para a RNDS, vinculados ao CPF, e a fonte mudou (TabNet → Painel). Parte da variação entre 2022 e 2023 pode refletir a mudança de sistema, não só a vacinação. Campo `quebra_serie`.
- **2025 provisório:** dados sujeitos a atualização; a população-alvo de 2025 é igual à de 2024 (SINASC 2025 preliminar). Campo `dado_provisorio`.
- **Coberturas acima de 100%:** ocorrem em municípios pequenos (denominador pequeno), por vacinação de crianças de outros municípios ou por subestimativa de nascidos vivos.
- **IDHM de 2010:** é anterior ao período analisado. Mojuí dos Campos, instalado em 2013, não tem IDHM.
- **Escopo:** a base usa apenas as 4 vacinas obrigatórias (Pentavalente, Poliomielite, Pneumocócica 10V e Tríplice viral D1). As complementares (BCG, Hepatite B ao nascer, Febre amarela e Tríplice viral D2) foram coletadas só para 2014–2022 e estão em `dados/tabnet_bruto_2014_2022.csv`. Para incluí-las, use `SOMENTE_OBRIGATORIAS = False` em `scripts/montar_base.py`.

## Reproduzir

```
python3 scripts/coleta_tabnet.py brutos_tabnet dados/tabnet_bruto_2014_2022.csv
python3 scripts/montar_base.py .
python3 scripts/dicionario.py .
```

As planilhas originais do painel ficam em `painel_2023_2025/` (brasil, estados, municipios_PA).
