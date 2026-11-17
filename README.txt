BAN 517 INVENTORY DECISION ANALYTICS AGENT — PREPARED STARTER APPLICATION

Files:
  app.py                     Streamlit user interface, CSV upload, 5 calculators, classification
  inventory_tools.py         Deterministic formulas and validation
  classification.py          Sales/Hits multicriteria classification
  tests/test_inventory_tools.py  Unit tests
  ProjectDataV2_UTF8.csv     Professor's uploaded inventory data
  Inventory_Classification_Methodology.pdf  Professor's reference sheet
  requirements.txt           Packages to install
  classification_summary.csv Computed summary from included dataset
  classified_inventory.csv   Item-by-item classification results

Important: This is a prepared starting point, NOT an already deployed application.
It has menu-based model selection, rather than the lecture's LLM-driven natural-language
router. It must be checked against the course's full lecture and rubric and improved
as necessary before submission. No claim is made that Antigravity has been used.

RUN ON A COMPUTER:
  1. Install Python 3.10+.
  2. Unzip the archive and open a terminal in this folder.
  3. pip install -r requirements.txt
  4. streamlit run app.py
  5. Upload ProjectDataV2_UTF8.csv inside the Streamlit application.
  6. Check class thresholds, boundary convention, totals, and other models.
  7. Deploy per instructor's instructions and use verified deployed results in report.

TESTS ON A COMPUTER:
  python -m unittest discover -s tests -v

CLASSIFICATION:
  1. Independently rank by descending sales and POS hits.
  2. Compute cumulative share including current item; class A <= 60%, B <= 80%,
     C <= 90%, otherwise D. Tie-break by ascending Item Number.
  3. Convert A/B/C/D to 4/3/2/1.
  4. Weighted score = .65 * Sales Score + .35 * Hits Score.
  5. Final A >= 3.25, B >= 2.50, C >= 1.75, otherwise D.

BOUNDARY NOTE:
  The professor's methodology gives rounded percentage bands 0-60/61-80/81-90/91-100
  but does not explicitly define boundary-crossing or tie policy. The code uses the
  inclusive cumulative contribution convention and breaks ties by Item Number.
  Confirm against instructor examples before submitting.
