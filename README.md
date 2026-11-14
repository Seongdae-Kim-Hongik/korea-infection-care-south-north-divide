# A south-north divide in care for infectious and parasitic diseases across Korean districts, 2011-2024

Analysis code for the manuscript

> Kim S. *A south-north divide in care for infectious and parasitic diseases held across Korean districts for fourteen years.* Submitted to *Applied Spatial Analysis and Policy*.

Archived version: Zenodo, https://doi.org/10.5281/zenodo.24212935 (v1.0.0).

## Contents

This repository contains code only. The processed district-year data (master table, analytic panel, expected counts, result tables, adjacency graph and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/INFECT/sets_INFECT_std3.json`, `sets_INFECT_s577.json`, `sets_INFECT_s2.json`, `sets_INFECT_s8.json`, `sets_INFECT_sage.json`, `config_INFECT_std3.json`, `run_std3_chain.sh` | Covariates with expected directions, forced controls, negative controls, comparison outcomes and model settings (principal model `std3` with sex- and age-standardized expected counts; sensitivity versions with the queen contiguity graph, without the share aged 80 or older, with coarser age-only expected counts, and with age-only expected counts) |
| `04_분석/INFECT/MS/` | Scripts that read the result tables and write every number, table and figure in the manuscript and supplementary material, including `content_infect.py`, which generates the Methods and Results text (the draft source of the Introduction and Discussion is not included) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment describing its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- People treated for infectious and parasitic diseases (A00-B99 as the principal diagnosis) by district of residence, and comparison outcomes (arthritis, stomach cancer): National Health Insurance Service, Regional Medical Care Utilization Statistics (Korean Statistical Information Service, KOSIS), 2011-2024.
- National numbers treated by age group (ten groups, to 75 years or older): the same statistics, national disease-classification tables.
- National counts by three-character code, sex and 5-year age group (A00-B99, 2015-2024): National Health Insurance Service big data platform (public statistics pages; `99I_fetch_infect_sexage.py`), used for the composition table and to split national counts by sex.
- Population by sex and 5-year age group: Ministry of the Interior and Safety, resident registration statistics. The 2023 age block of Changwon duplicated the 2022 block and was corrected.
- District covariates: Community Health Survey (current smoking, walking, moderate-or-vigorous activity), national general health screening statistics (screening uptake, suspected diabetes, obesity management), Health Insurance Review and Assessment Service register of care institutions (long-term care hospitals), basic livelihood security recipients, single-person households, local business licensing (public bathhouses), public sports facility registers (swimming pools, all facilities), weather station temperature interpolated to districts, and KOSIS local indicators (forced controls and negative controls). KOSIS tables were fetched with a personal API key, which is not included.

## Pipeline

Run from the repository root (set `ST_DATA_ROOT` and `ST_FBDZIP_CORRECTED` to the local copies of the public source files).

| Step | Script | Output |
|---|---|---|
| 0 | `99I_fetch_infect_sexage.py` | National counts by three-character code, sex and age |
| 1 | `99I_screen_infect_std3_prep.py`, `98_fit_forced_v.R`, `99I_screen_infect_std3.py` | Sex- and age-standardized expected counts and spatial screening with forced controls only |
| 2 | `99b_extra_canonical_pool.py`, `99c_extra_canonical_pool_infect.py` | Corrected basic livelihood rate, public bathhouses and temperature joined by district code |
| 3 | `80_build_disease_panel_v.py INFECT` (`ST_VER=std3`) | Analytic panel |
| 4 | `81_fit_inla.R INFECT` (`ST_VER=std3`, `ST_GRAPH=04_분석/INFECT/graph_593.graph`, `ST_THREADS=1`; see `04_분석/INFECT/run_std3_chain.sh`, which wraps R jobs in `rslot.sh`) | Principal model, set comparison, 200-subset multiverse, window models |
| 5 | `82_core_report.py`, `83_check_report.py`, `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `86b_ehsa_modified_mk.py`, `87_window_grid.py` | Core report, maps, yearly smoothed ratios and emerging hot spot analysis |
| 6 | `88g_sens_prep.py INFECT std3 ARTH,GCA`, `88g_sens_suite.R` (`GROUP=1..6`), `88h_ppc_varpart.R`, `88k_struct_kh.R` (nb, struct, kh, review) with `kh_constraints.R`, `89g_sens_combine.py` | Sensitivity analyses, comparison outcomes, Knorr-Held models, review outputs |
| 7 | `04_분석/INFECT/MS/build/` (`figs_infect.py`, `build_id_infect.py` (shared tables and text helpers), `build_asap_infect.py`, `esm_infect.py`, `check_asap_infect.py`; `run_all_asap.sh`) | Manuscript, supplementary material, figures and checks |

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path.

## Software

R 4.6.0 with R-INLA 25.10.19, spdep and sf; Python 3.9 with pandas, geopandas, numpy, scipy, matplotlib and python-docx.
