# MediCare+ Hospital Analytics - Data Quality, Measures and Decision Support on 247 Admissions

This project takes the MediCare+ admission register from **raw data** to **decision support**:
raw data → clean data → measures & KPIs → statistical tests → insights → interactive dashboard.

Author:
- KOUAME Koffi Fidèle - WASCAL IMP-EGH, Abdou Moumouni University, Niamey, [koffifidelek59@gmail.com](mailto:koffifidelek59@gmail.com)

## Access this notebook

<a target="_blank" href="https://colab.research.google.com/github/koffifidelek59-collab/piggy-cast/blob/main/MediCare_Hospital_Analytics/MediCare-Hospital-Analytics.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

Estimated time to execute end-to-end: under 1 minute on a CPU.

## Deliverables

| Deliverable | File |
|---|---|
| Analysis notebook (cleaning, KPIs, figures, tests, insights) | `MediCare-Hospital-Analytics.ipynb` |
| Formal report, Times 12 pt, 1.5 spacing | `report.pdf` (source `report.tex`) |
| Interactive dashboard, seven views | `dashboard.html` |
| Real-time WebSocket API for the dashboard (optional) | `websocket_server.py`, `WEBSOCKET.md` |
| Raw register | `data/hospital_raw.csv` |
| Clean register, 247 rows, quality flags kept | `data/hospital_clean.csv` |
| Result tables (KPIs, tests, aggregates) | `results/` |
| Twelve analysis figures, PNG 300 dpi | `figures/` |
| Dashboard captures inserted in the report | `figures/dashboard/` |

## Main findings

1. **195 of 247 bills are placeholders** (999 or 3,852). The raw column sums to 618,995; validated revenue is **153,155** on 52 genuine bills.
2. **Validated revenue is a floor.** Genuine bills sit on short stays; none of the 43 stays longer than 12 days has one (Mann-Whitney p < 0.001).
3. **29 stays end before they begin.** Mean length of stay on the 218 valid stays is **6.74 days**, median 4.
4. **Length of stay drives the bill** (Spearman ρ = 0.62, p < 0.001, about 530 per day); severity drives neither the stay (p = 0.84) nor the bill (p = 0.28).
5. **No significant seasonality** (p = 0.17): a staffing roster should not follow this single year's monthly shape.

## Reproduce

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace MediCare-Hospital-Analytics.ipynb
pdflatex report.tex && pdflatex report.tex
```

Optional live streaming to the dashboard:

```bash
python websocket_server.py   # then click Connect in dashboard.html
```

## License
MIT License.
