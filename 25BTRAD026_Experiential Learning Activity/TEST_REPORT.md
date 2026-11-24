# Test & Verification Report

**Project:** Local PDF Semantic Search & Q&A System  
**Test Environment:** Windows 11, Python 3.10+, CPU only  
**Test Dataset:** Physics & Chemistry Academic Notes (5–10 pages each)

---

## 1. Summary of Test Results
- **Total Test Queries:** 10
- **Top-1 Success Rate (Direct Match at Rank 1):** 90%
- **Top-3 Recall (Target Answer in Top 3 Results):** 100%
- **Average Query Response Time:** ~35 ms
- **False Positive Handling:** Out-of-domain questions correctly flagged by low-confidence warning.

---

## 2. Test Execution Log

| # | Test Question | Category | Target Topic / Concept | Retrieved Rank | Confidence Score | Status |
|---|---|---|---|:---:|:---:|:---:|
| 1 | *What is the first law of thermodynamics?* | Factual (Physics) | Conservation of energy equation $\Delta U = Q - W$ | **Rank 1** | **84.2%** |  PASS |
| 2 | *Define Le Chatelier's principle.* | Factual (Chemistry) | Equilibrium response to changes in condition | **Rank 1** | **86.1%** |  PASS |
| 3 | *What is the SI unit of electric capacitance?* | Factual (Physics) | Farad definition and equation $C = Q/V$ | **Rank 1** | **79.5%** |  PASS |
| 4 | *What is an exothermic vs endothermic reaction?* | Factual (Chemistry) | Enthalpy change $\Delta H$ and heat release/absorption | **Rank 1** | **81.7%** |  PASS |
| 5 | *State Heisenberg's uncertainty principle.* | Factual (Physics/Chem) | Position and momentum limitation $\Delta x \cdot \Delta p \ge \hbar/2$ | **Rank 1** | **88.3%** |  PASS |
| 6 | *Why does higher temperature speed up reaction rate?* | Conceptual (Chemistry) | Kinetic energy and collision theory | **Rank 1** | **73.4%** |  PASS |
| 7 | *How does an object keep moving in deep space without fuel?* | Conceptual (Physics) | Newton's First Law / Inertia | **Rank 2** | **68.9%** |  PASS |
| 8 | *Why do noble gases rarely form chemical bonds?* | Conceptual (Chemistry) | Complete valence octet stability | **Rank 1** | **75.2%** |  PASS |
| 9 | *How is energy conserved in a swinging pendulum?* | Conceptual (Physics) | Potential vs. kinetic energy interchange | **Rank 1** | **71.8%** |  PASS |
| 10 | *What factors affect whether a salt dissolves in water?* | Conceptual (Chemistry) | Lattice energy vs. hydration enthalpy | **Rank 1** | **70.6%** |  PASS |

---

## 3. Negative & Boundary Testing

| Scenario | Input Tested | System Behavior | Result |
|---|---|---|---|
| **Unrelated Query** | *"Who won the FIFA World Cup?"* | Top score fell to 28.4%. System displayed yellow warning banner: *"No directly relevant answer found..."* |  PASS |
| **No Documents Uploaded** | Typed question without indexing | Yellow warning banner: *"Please upload and index PDF documents first..."* |  PASS |
| **Short PDF (< 3 Paragraphs)** | Single-page notice PDF | `k = min(3, len(chunks))` prevented index out-of-bounds error. |  PASS |
| **Scanned / Image PDF** | Image-only scan of notes | Detected 0 valid text characters. Displayed sidebar notice: *"No readable text found..."* |  PASS |

---

## 4. Conclusion
The system meets all functional, accuracy, and latency benchmarks for local offline semantic retrieval. It handles both direct definitions and paraphrased conceptual inquiries reliably without fabricating information.
