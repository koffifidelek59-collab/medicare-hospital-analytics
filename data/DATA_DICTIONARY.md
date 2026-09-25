# Data dictionary

**Hospital Analytics** &middot; 247 admission episodes, January to December 2023

Three editions of the data are delivered:

| Edition | File | Rows | Columns |
| :--- | :--- | ---: | ---: |
| Original, as supplied | `Hospital_Analytics_original.xlsx` | 248 | 10 |
| Cleaned, values in Arabic | `hospital_clean.csv` | 247 | 27 |
| Cleaned, values in English | `hospital_clean_en.csv` | 247 | 23 |

The two cleaned editions hold identical data. Only the labels differ, and an
integrity check in the notebook confirms that ages, bills, dates, stays and every
quality flag are carried across untouched.

Rows are in **admission date order**. `EpisodeID` is assigned on that order, so it is
stable if the file is re-sorted.

---

## Columns

| # | Column | Type | Can be empty | Meaning |
| ---: | :--- | :--- | :---: | :--- |
| 1 | `EpisodeID` | Text | no | Primary key. Assigned on admission date order, so it is stable if the file is re-sorted. |
| 2 | `PatientName` | Text | no | Patient name. 75 distinct names across 247 episodes: a patient may be admitted more than once. |
| 3 | `Age` | Whole number | no | Age in years at admission. Range 1 to 90. |
| 4 | `AgeBand` | Text | no | Age grouped into six bands. Sort it by AgeBandOrder, not alphabetically. |
| 5 | `AgeBandOrder` | Whole number | no | Sort key for AgeBand, 1 for 0-18 up to 6 for 76+. |
| 6 | `Gender` | Text | no | As recorded. **Carries no usable signal**: it agrees with the patient name on 48.4% of episodes (p = 0.743). Not used as an analytical dimension. |
| 7 | `Diagnosis` | Text | no | Admitting diagnosis, one of ten. |
| 8 | `Severity` | Text | no | Severity grade: Low, Medium or High. Sort by SeverityRank. |
| 9 | `SeverityRank` | Whole number | no | Sort key for Severity, 1 Low to 3 High. |
| 10 | `Doctor` | Text | no | Attending physician, one of seven. Caseloads run from 24 to 44 episodes. |
| 11 | `AdmitDate` | Date | no | Admission date, ISO format. 2023-01-01 to 2023-12-28. |
| 12 | `DischargeDate` | Date | no | Discharge date, ISO format. **29 values precede the admission date**; see DateError. |
| 13 | `LengthOfStay` | Whole number | yes | Days between admission and discharge. **Empty on the 29 episodes where the dates are impossible.** Empty, not zero: zero would mean a same-day discharge, which is a real clinical event. |
| 14 | `AdmitMonth` | Whole number | no | Month of admission, 1 to 12. Use as the sort key for AdmitMonthName. |
| 15 | `AdmitMonthName` | Text | no | Three-letter month abbreviation. Sort by AdmitMonth. |
| 16 | `AdmitQuarter` | Whole number | no | Calendar quarter of admission, 1 to 4. |
| 17 | `AdmitWeekday` | Text | no | Day of the week of admission. |
| 18 | `Bill` | Whole number | no | The billed amount as recorded. **78.6% of values are one of two constants**, 999 and 3852. Do not aggregate this column; use BillValid. |
| 19 | `BillValid` | Whole number | yes | The billed amount where it is genuine, empty where it is a placeholder. **52 episodes, 21.1%.** This is the column every revenue figure must use. |
| 20 | `Insurance` | Text | no | Cover status: Uninsured, Private insurance or Government insurance. |
| 21 | `IsInsured` | True/False | no | True where Insurance is not Uninsured. 70.9% of episodes. |
| 22 | `DateError` | True/False | no | True where the discharge date precedes the admission date. **29 episodes, 11.7%.** Exclude these from any length-of-stay measure. |
| 23 | `BillIsPlaceholder` | True/False | no | True where Bill is 999 or 3852. **195 episodes, 78.6%.** Exclude these from any financial measure. |

### Present in the Arabic edition only

| Column | Meaning |
| :--- | :--- |
| `GenderEN` | English label for the corresponding Arabic column, for charts |
| `SeverityEN` | English label for the corresponding Arabic column, for charts |
| `InsuranceEN` | English label for the corresponding Arabic column, for charts |
| `DiagnosisEN` | English label for the corresponding Arabic column, for charts |

---

## The three columns to read before using the file

**`BillIsPlaceholder`.** Two amounts, 999 and 3852, cover 78.6% of the billing column.
Both are legal values inside a plausible range, so no validity rule reaches them and no
completeness audit sees them. `BillValid` holds the amount only where it is genuine.
Any revenue figure must use `BillValid` and state the 21.1% coverage.

**`DateError`.** 29 episodes record a discharge before the admission. These are recording
errors, not outliers: a stay cannot be negative. `LengthOfStay` is empty on those rows,
and any stay measure must exclude them.

**`Gender`.** The field agrees with the patient name on 48.4% of the episodes whose given
name is unambiguously gendered, and a chi-square test cannot reject independence
(p = 0.743). It is delivered because it is in the source, and it is not used as an
analytical dimension anywhere in this study.

---

## Sort keys

Three columns are text with a meaningful order. Sorted alphabetically they mislead:
`0-18` lands after `19-30`, and `Apr` before `Jan`. Each has a numeric partner.

| Text column | Sort by |
| :--- | :--- |
| `AgeBand` | `AgeBandOrder` |
| `Severity` | `SeverityRank` |
| `AdmitMonthName` | `AdmitMonth` |

In Power BI: select the text column, **Column tools**, **Sort by column**, choose its
partner. In pandas: pass the order to `pd.Categorical`.

---

## Encoding

`hospital_clean.csv` is written as **UTF-8 with BOM**, so Excel opens the Arabic values
correctly on a double-click. `hospital_clean_en.csv` is plain **UTF-8**.

Empty cells are written as empty, never as `NaN` or `NULL`. Whole numbers carry no
decimal point: a length of stay reads `4`, not `4.0`.

---

**KOUAME Koffi Fidèle** &middot; Data Analysis Internship &middot; koffifidelek59@gmail.com
