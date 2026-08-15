# Research Bibliography — Algorithm Selection & Meta-Learning

Sources consulted during PRD discovery for TFM (2026-07-26).
Note: sources marked [READ] were fetched and read by the research agent; sources marked [FOUND] were located via search but not fully read — verify independently.

---

## Algorithm Selection — Foundational

1. **Rice, J. R.** (1976). The algorithm selection problem. *Advances in Computers*, 15, 65–118.
   - https://www.researchgate.net/figure/The-Algorithm-Selection-Problem-of-Rice-1976_fig1_335995943
   - *The conceptual backbone: given features F of problem i, find algorithm a maximizing performance P(i,a).*

## Practical Flowcharts / Cheat Sheets

2. ⭐️ **Scikit-learn contributors** (2024, v1.9.0). Choosing the right estimator. *Scikit-learn documentation*.
   - https://scikit-learn.org/stable/machine_learning_map.html
   - *Flowchart gating on sample size (~50, ~10k, ~100k), feature types, and task type.*

3. **Microsoft** (2021). Machine Learning Algorithm Cheat Sheet for Azure Machine Learning designer. *Microsoft Learn*.
   - [FOUND] https://learn.microsoft.com/en-us/azure/machine-learning/algorithm-cheat-sheet?view=azureml-api-1

4. **Microsoft** (undated). How to select a machine learning algorithm. *Azure ML documentation*.
   - http://techcommunity.microsoft.com/blog/educatordeveloperblog/how-to-select-algorithms-for-azure-machine-learning/1235687

## AutoML Systems

5. **Thornton, C., Hutter, F., Hoos, H. H., & Leyton-Brown, K.** (2013). Auto-WEKA: Combined selection and hyperparameter optimization of classification algorithms. *KDD 2013*, pp. 847–855.
   - [FOUND] https://arxiv.org/abs/1208.3719

6. **Kotthoff, L., Thornton, C., Hoos, H. H., Hutter, F., & Leyton-Brown, K.** (2017). Auto-WEKA 2.0: Automatic model selection and hyperparameter optimization in WEKA. *JMLR*, 18(25), 1–5.
   - [FOUND] https://www.jmlr.org/papers/v18/16-261.html

7. **Garouani, M., Ahmad, A., Bouneffa, M., & Hamlich, M.** (2022). AMLBID: An auto-explained Automated Machine Learning tool for Big Industrial Data. *SoftwareX*, 17, 100919.
   - [FOUND] https://www.sciencedirect.com/science/article/pii/S2352711021001631
   - *Directly referenced in the thesis proposal as the meta-learning upper bound baseline.*

## Meta-Features / Meta-Learning

8. **Rivolli, A., Garcia, L. P. F., Soares, C., Vanschoren, J., & de Carvalho, A. C. P. L. F.** (2022). Meta-features for meta-learning. *Knowledge-Based Systems*, 240, 108101.
   - [FOUND] https://www.sciencedirect.com/science/article/abs/pii/S0950705121011631

9. **Alcobaça, E. et al.** (2020). MFE: Towards reproducible meta-feature extraction. *JMLR*, 21(111), 1–5.
   - [FOUND] https://pymfe.readthedocs.io/en/latest/auto_examples/01_introductory_examples/plot_groups.html

10. **Khan, I., Zhang, X., Rehman, M., & Ali, R.** (2020). A literature survey and empirical study of meta-learning for classifier selection. *IEEE Access*, 8, 10262–10281.
    - [FOUND] https://doaj.org/article/e10bd3a9a5da4450986e0b6adaea33d8

11. **Brazdil, P., van Rijn, J. N., Soares, C., & Vanschoren, J.** (2022). *Metalearning: Applications to Automated Machine Learning and Data Mining* (2nd ed.). Springer. Ch. 4: Dataset Characteristics (Metafeatures), pp. 53–75.
    - [FOUND] https://link.springer.com/content/pdf/10.1007/978-3-030-67024-5_4

12. **Basgalupp, M. P. et al.** (2020). An extensive experimental evaluation of automated machine learning methods for recommending classification algorithms. arXiv:2009.07430.
    - [FOUND] https://arxiv.org/abs/2009.07430

13. **Wever, M., Tornede, A., Mohr, F., & Hullermeier, E.** (2023). AutoML for Lifelong Machine Learning. *Machine Learning*, 112, 1253–1286.
    - [FOUND] DOI: 10.1007/s10994-022-06161-4

14. **Reif, M., Shafait, F., Goldstein, M., Breuel, T., & Dengel, A.** (2014). Automatic classifier selection for non-experts. *Pattern Analysis and Applications*, 17(1), 83–96.
    - [FOUND] https://www.researchgate.net/publication/321882946_On_the_predictive_power_of_meta-features_in_OpenML

## To Investigate

15. **PyBrain** — Python machine learning library.
    - [TO INVESTIGATE] Relevance to TFM (e.g. as a candidate implementation/benchmark library, or as related prior work) not yet assessed — needs follow-up.

16. **caret** (Classification And REgression Training) — R package.
    - [TO INVESTIGATE] Unified interface for training/comparing many ML models in R; relevant as prior art for the recommender's "compare methods on your dataset" mode — needs follow-up.

17. **KNIME** — visual/no-code data analytics and ML platform.
    - [TO INVESTIGATE] Possible prior art as a GUI-driven tool letting non-experts build and compare ML workflows — relevance to the playground/gap analysis not yet assessed — needs follow-up.

18. **tidyverse** — R package collection for data science.
    - [TO INVESTIGATE] Relevance not yet assessed — needs follow-up.

19. **Apple Neural Engine** — Apple's on-device ML accelerator hardware.
    - [TO INVESTIGATE] Relevance not yet assessed — needs follow-up.
