# Improving a URL Credibility Scoring Algorithm

**Christine Donahue**  
CS676  
Pace University  

## 1. Introduction

Evaluating the credibility of online information is difficult because credibility cannot be determined from a single feature of a website or URL. A domain may provide useful information about the organization responsible for a source, but domain type alone does not establish whether an individual page is reliable. Similarly, characteristics such as HTTPS, scholarly identifiers, and recognizable publication domains can provide useful evidence, but each has limitations. Moreover, with the rapid growth of AI-generated content and misinformation online, tools that can systematically evaluate signals associated with source credibility are increasingly useful.

The baseline system provided for this project estimates the credibility of a URL using a combination of rule-based signals and, optionally, an evaluation from a large language model (LLM). The rule-based component considers features such as known domains, top-level domains, HTTPS usage, DOI patterns, and selected terms appearing in the URL path. The resulting score ranges from 0 to 1 and is categorized as LOW, MEDIUM, or HIGH credibility.

My goal was to improve the rule-based component while preserving the required `score_url()` interface and avoiding an approach that simply added more websites to a manually curated lookup table. I focused on signals that could generalize to URLs that the program had not previously encountered. The improvements included distinguishing preprint repositories from peer-reviewed publication signals, obtaining independent scholarly metadata from Crossref, recognizing the restricted `.int` top-level domain, identifying limited forms of sensational URL language, improving failure handling for external metadata requests, and making the final explanation easier for users to interpret.

The original rule-based algorithm achieved a mean absolute error (MAE) of 0.142, a credibility-band accuracy of 66.7%, and a worst individual error of 0.410 on the 24 labeled URLs supplied with the project. After the modifications described in this report, the rule-based system achieved an MAE of 0.094, band accuracy of 83.3%, and a worst error of 0.230. All 24 automated tests, including three additional tests written for the new behavior, passed.

## 2. Baseline Credibility-Scoring Algorithm

The original `credibility.py` implementation used a rule-based scoring system with an optional LLM component. I first evaluated the rule-based system independently by running `evaluate.py` without the LLM. This provided a reproducible baseline that did not require an external paid model.

### 2.1 Rule-Based Scoring

The baseline algorithm extracted the domain and path from each URL and generated a series of credibility signals. If the domain appeared in a manually defined `DOMAIN_SCORES` table, the corresponding value became the starting score. For example, established scientific and medical sources such as Nature, the New England Journal of Medicine, and PubMed received relatively high starting values, while platforms such as Reddit and Medium received lower values.

For domains that were not included in the lookup table, the algorithm instead used the URL's top-level domain (TLD). Domains ending in `.gov` or `.edu`, for example, received higher starting values than generic `.com`, `.net`, or `.info` domains.

Additional adjustments were then applied. HTTPS produced a small positive adjustment, while HTTP produced a penalty. Terms such as `/blog`, `/opinion`, `/sponsored`, `/press-release`, and `/advertorial` in the URL path reduced the score. A URL containing a pattern resembling a Digital Object Identifier (DOI) received a positive adjustment.

The individual signals were combined arithmetically and the final value was constrained to the interval from 0 to 1. Scores of at least 0.70 were classified as HIGH credibility, scores from 0.40 to less than 0.70 as MEDIUM, and scores below 0.40 as LOW.

### 2.2 Optional LLM Evaluation

The supplied implementation could also request an independent credibility estimate from an Anthropic language model. When available, the final score combined the rule-based estimate and the LLM estimate using fixed weights of 0.60 and 0.40, respectively.

For development of my algorithm, I concentrated primarily on improving the deterministic rule-based component. This allowed changes to be evaluated without incurring API costs and made it easier to determine which specific algorithmic modifications were responsible for changes in performance.

### 2.3 Baseline Performance and Error Analysis

Before modifying the algorithm, I ran the supplied contract tests and evaluation script. All 21 original tests passed. On the 24 labeled evaluation URLs, the baseline rule-based algorithm produced:

| Metric | Baseline |
|---|---:|
| Mean absolute error (MAE) | 0.142 |
| Band accuracy | 66.7% |
| Worst individual error | 0.410 |
| Original automated tests passed | 21/21 |

Examining the individual errors was more informative than considering the aggregate metrics alone. The largest error occurred for a JAMA URL, which had an expected score of 0.93 but received only 0.52. A World Health Organization URL similarly received 0.52 compared with an expected value of 0.88. These examples illustrated an important limitation of the manually curated domain table: reputable organizations that were not explicitly included could receive relatively ordinary scores.

The baseline also overestimated some sources. A bioRxiv preprint URL received 0.82 compared with an expected value of 0.50, while a low-credibility `.info` URL containing phrases such as `miracle-cure` and `doctors-hate` received 0.32 compared with an expected value of 0.05.

These errors suggested that improvement required more than simply changing numerical weights. The algorithm needed additional information about the type of source represented by a URL and more nuanced interpretation of the evidence already present in the URL.

## 3. Algorithm Improvements

Rather than making all modifications at once, I changed the algorithm incrementally and reran both the automated tests and `evaluate.py` after each major change. This allowed me to determine whether a proposed modification actually improved performance and reduced the risk of introducing changes that only appeared beneficial.

### 3.1 Distinguishing Preprints from Peer-Reviewed Sources

One of the largest baseline errors involved bioRxiv. The baseline algorithm assigned the test URL a credibility score of 0.82, substantially higher than its labeled value of 0.50. Examination of the scoring logic showed that the algorithm recognized bioRxiv as a scholarly source but did not adequately distinguish a preprint from a peer-reviewed journal article.

I added a small set of known preprint repositories, initially including bioRxiv and arXiv, and introduced a modest penalty of 0.10 when a URL belonged to one of these repositories. The purpose of the penalty was not to characterize preprints as unreliable. Preprints can contain high-quality scientific work, but they generally have not completed the same peer-review process as a published journal article. Therefore, preprint status was treated as one piece of evidence rather than as a determination of credibility.

This first modification reduced MAE from 0.142 to 0.134 and increased band accuracy from 66.7% to 70.8%, while all original tests continued to pass.

### 3.2 Refining the DOI Signal

The baseline algorithm added 0.10 whenever the URL path contained a pattern resembling a DOI. During error analysis, I realized that this rule could partially undo the new preprint adjustment because preprints can also have DOIs.

I therefore modified the DOI rule so that a DOI receives the positive adjustment only when the source is not a recognized preprint repository. This change reflects an important limitation of DOI-based inference: a DOI is a persistent identifier for a digital object, but the presence of a DOI does not by itself demonstrate that an article has undergone peer review or that its conclusions are correct.

After this modification, MAE decreased further from 0.134 to 0.130 and band accuracy increased from 70.8% to 75.0%. The worst individual error remained 0.410, indicating that additional problems still needed to be addressed.

### 3.3 Using Crossref as Independent Scholarly Evidence

The JAMA result exposed another weakness in the baseline algorithm. JAMA is an established peer-reviewed medical journal, but because `jamanetwork.com` was not included in the manually curated domain table, the algorithm assigned the example URL a score of only 0.52. One simple solution would have been to add JAMA to `DOMAIN_SCORES`. However, that approach would improve only URLs that I had already identified and would not address the underlying generalization problem.

Instead, I added a function that queries the Crossref REST API for scholarly metadata when the algorithm encounters an unknown domain. Crossref maintains structured metadata associated with scholarly publications and DOIs. The purpose of this addition was to obtain evidence about an unfamiliar scholarly source from an independent metadata service rather than teaching the algorithm the answer for a specific evaluation URL.

The implementation deliberately applies several checks before accepting Crossref evidence. The returned item must be identified as a `journal-article`, and the domain of Crossref's primary resource URL must match the domain being evaluated. This domain validation is important because a search result merely mentioning a URL or returning an unrelated scholarly work should not increase the credibility score.

When these conditions are satisfied, the algorithm adds a 0.20 scholarly-evidence adjustment and includes the journal identified by Crossref in the explanation. For example, Crossref identified the JAMA test domain as hosting an article in *JAMA*. This increased the JAMA score from 0.52 to 0.72 without adding `jamanetwork.com` to the manually curated domain table.

After introducing the Crossref signal, overall MAE decreased from 0.130 to 0.121, band accuracy increased from 75.0% to 79.2%, and the worst individual error decreased from 0.410 to 0.360.

Crossref also introduced a new engineering problem: dependence on an external web service. During repeated evaluation, I observed a transient Crossref request failure that caused the JAMA score to revert to its rules-only value. I initially investigated in-memory caching, but this did not solve the problem because the cache did not persist between separate executions of the evaluation program and could also preserve a failed result. Instead, I implemented one retry after a request failure, with a three-second timeout on each request. If Crossref remains unavailable, the function returns `None` and the scorer continues using the other available signals rather than crashing.

This approach improves robustness but does not make the system completely deterministic. A persistent network or Crossref failure can still change the score of a URL that would otherwise receive scholarly metadata evidence. This remains an important limitation of the final implementation.

### 3.4 Recognizing the Restricted `.int` Domain

The World Health Organization example revealed a different problem. The baseline TLD rules did not include `.int`, causing the WHO test URL to receive a score of only 0.52 rather than its labeled value of 0.88.

Unlike generic TLDs such as `.com` or `.info`, `.int` is a restricted top-level domain intended for organizations established by international treaties or certain related entities. I therefore added `.int` to the TLD scoring rules with a starting score of 0.85.

This change is more general than adding `who.int` to the known-domain table because it applies the same rule to other qualifying `.int` organizations. After this modification, the WHO score increased from 0.52 to 0.87. Overall MAE decreased from 0.121 to 0.107, band accuracy increased from 79.2% to 83.3%, and the worst error decreased from 0.360 to 0.270.

### 3.5 Sensational Language as a Weak Negative Signal

The baseline evaluation also revealed that obviously promotional or sensational URL paths could receive scores that were too high. For example, the evaluation set contained a low-credibility `.info` URL with phrases such as `miracle-cure` and `doctors-hate`. The baseline system assigned it a score of 0.32 compared with its labeled value of 0.05.

The original algorithm already penalized structural terms such as `sponsored`, `advertorial`, and `opinion`. I extended this idea by creating a separate category for a small number of sensational phrases appearing in the URL path. Each detected phrase produces only a modest negative adjustment of 0.10.

I intentionally treated sensational language as a weak signal rather than proof that information is false. Legitimate sources can use attention-getting language, and an unreliable source can use completely neutral language. Therefore, this feature contributes evidence to the overall score but does not determine the classification by itself.

After this modification, the `health-truth-daily.info` example decreased from 0.32 to 0.12 and another low-credibility `.xyz` example decreased from 0.20 to 0.10. Overall MAE decreased from 0.107 to 0.094. Band accuracy remained 83.3%, while the worst individual error improved from 0.270 to 0.230.

### 3.6 Improving the User-Facing Explanation

The original function returned an explanation containing the individual scoring signals, but the result required the user to interpret those signals and the numerical score independently. I modified the explanation so that it begins with the final credibility band and numerical score, followed by the evidence that contributed to the result.

For example, rather than returning only a sequence of observations about a `.info` URL, the application can now begin with `LOW credibility (0.12)` and then describe the TLD, HTTPS, and sensational-language signals that produced the score.

This modification did not change MAE or band accuracy because it changed presentation rather than the scoring calculation. However, it made the output more interpretable in the integrated Streamlit application and made it easier for a user to understand why the algorithm produced a particular result.

### 3.7 Environment Configuration for the LLM Layer

The starter project expected an `ANTHROPIC_API_KEY` environment variable for the optional Claude layer and provided an `.env.example` file. However, the credibility module did not explicitly load the local `.env` file. As a result, running `evaluate.py --llm` could report that the LLM layer was enabled while silently falling back to rules-only scoring because the API key was unavailable to the process.

I added `python-dotenv` loading when the credibility module is initialized. This allows the application and evaluation script to obtain the API key from the local `.env` file while keeping the key out of the source code and version control. The existing graceful fallback behavior remains intact if no key is available or an API call fails.

# 4. Experimental Evaluation and Results

I evaluated each major modification using the same 24 labeled URLs in `evaluate.py`. I also reran the automated contract tests after each change to ensure that improvements in evaluation performance did not break the required `score_url()` interface or malformed-input handling.

The experiments were performed incrementally rather than evaluating only the final implementation. This made it possible to determine the effect of each modification.

| Version | MAE | Band Accuracy | Worst Error |
|---|---:|---:|---:|
| Baseline | 0.142 | 66.7% | 0.410 |
| + Preprint status | 0.134 | 70.8% | 0.410 |
| + DOI/preprint distinction | 0.130 | 75.0% | 0.410 |
| + Crossref metadata | 0.121 | 79.2% | 0.360 |
| + `.int` recognition | 0.107 | 83.3% | 0.270 |
| + Sensational-path signal | **0.094** | **83.3%** | **0.230** |
| + Crossref retry handling | **0.094** | **83.3%** | **0.230** |
| + Improved explanation | **0.094** | **83.3%** | **0.230** |
| + Claude LLM layer | **0.058** | **91.7%** | **0.140** |

The final rule-based implementation reduced MAE from 0.142 to 0.094, a reduction of approximately 33.8%. Band accuracy increased from 66.7% to 83.3%, corresponding to an increase from 16 of 24 URLs assigned to the correct credibility band to 20 of 24. The largest individual error decreased from 0.410 to 0.230.

When the Claude LLM layer was enabled, performance improved further. The combined rule-based and LLM system achieved an MAE of 0.058, band accuracy of 91.7% (22 of 24 URLs), and a worst single error of 0.140. Compared with the original rules-only baseline, this represents an approximately 59.2% reduction in MAE, a 25.0 percentage-point increase in band accuracy, and a reduction in the worst single error from 0.410 to 0.140. These results suggest that the deterministic rules and the LLM provide complementary information: the rules supply transparent, reproducible signals, while the LLM can incorporate broader contextual knowledge when evaluating a source.

Not every modification was expected to change the numerical evaluation metrics. The Crossref retry logic addressed robustness rather than scoring under normal conditions, while the explanation changes addressed interpretability. Both were retained because performance metrics alone do not capture all requirements of a usable credibility-scoring application.

### 4.1 Additional Tests

The original project contained 21 automated tests. I retained all of these tests and added three tests specifically targeting behavior introduced during development.

The additional tests verify that a restricted `.int` source receives a higher score than an otherwise comparable generic `.org` source, that the presence of a DOI does not artificially increase the score of a known preprint repository, and that a sensational URL path receives a lower score than a neutral path on an otherwise comparable unknown domain.

The final implementation passes all 24 tests.

### 4.2 Integrated Application Testing

I also tested the modified scorer through the supplied Streamlit interface rather than evaluating it only from the command line. A low-credibility test URL containing sensational language produced a score of 0.12, a LOW classification, and an explanation identifying the `.info` domain, HTTPS connection, and sensational path phrases.

I additionally entered malformed input (`not a url`). The application returned a score of 0.00 with an explanation that the input was not a valid HTTP(S) URL and did not crash.

These tests confirmed that the modified `score_url()` function remained compatible with the existing application and that its explanations were displayed legibly to the user.

## 5. Approaches Investigated but Not Adopted

Several possible improvements were investigated but were not included in the final scoring algorithm. Rejecting these approaches was part of the development process because an additional feature was retained only when its rationale and likely generalizability justified the added complexity.

### 5.1 OpenAlex Citation Metrics

I investigated OpenAlex as a possible source of external information about scholarly journals. OpenAlex provides bibliometric information such as citation measures and source-level statistics, which initially appeared useful for distinguishing highly established journals from less established scholarly sources.

I ultimately did not incorporate these metrics into the final score. Citation frequency measures scholarly influence or attention, but it is not equivalent to credibility. A highly cited article can be controversial or incorrect, while a new but methodologically strong article may have few citations. In addition, within the supplied evaluation set, this approach appeared likely to improve only a small number of specific cases. Incorporating it therefore risked tuning the algorithm to the evaluation data rather than producing a broadly useful credibility signal.

### 5.2 PubMed Indexing

I also investigated whether PubMed indexing could provide evidence for biomedical sources. A JAMA article could be identified through PubMed, demonstrating that this approach could provide useful evidence in some cases.

However, PubMed is specialized for biomedical and life-science literature. Using PubMed as a major credibility signal would therefore favor biomedical sources while providing little information about credible publications in fields such as economics, computer science, physics, or general news. Because the assignment requires a general URL credibility scorer rather than a biomedical literature classifier, I did not incorporate this approach.

### 5.3 In-Memory Caching of Crossref Results

When I observed a transient Crossref request failure, I tested in-memory caching as a possible solution. Caching successfully prevented repeated API requests for the same URL during a single Python process.

However, `evaluate.py` is executed as a new process, so the cache disappears between runs. More importantly, a simple cache could store a failed Crossref lookup (`None`) and continue returning that failure even if the external service recovered. I therefore removed the caching approach and used a limited retry with timeout and safe fallback instead.

### 5.4 Expanding the Known-Domain Table

The simplest way to reduce several remaining evaluation errors would have been to add domains such as JAMA, ProPublica, or the IMF directly to `DOMAIN_SCORES`. I intentionally avoided doing this merely because those domains appeared in the evaluation set.

Such changes could improve the reported metrics without demonstrating that the algorithm generalizes to previously unseen websites. Instead, I prioritized features such as Crossref metadata and the restricted `.int` domain that encode information applicable to broader categories of URLs.

This decision means that several remaining evaluation errors are larger than they could be if the algorithm were explicitly tuned to the 24 supplied examples. I considered that preferable to reporting artificially improved performance produced by memorizing the evaluation set.

## 6. Limitations and Remaining Challenges

Although the modified algorithm substantially improved performance on the supplied evaluation set, several important limitations remain.

### 6.1 Credibility Is Not the Same as Factual Accuracy

The most important limitation is that the system estimates source credibility rather than determining whether an individual claim is true. A highly reputable journal can publish a study that is later contradicted or retracted, while a less established source can publish accurate information. Features such as domain reputation, publication type, DOI presence, and scholarly metadata should therefore be interpreted as evidence about a source rather than as proof of factual correctness.

### 6.2 Limited Page-Level Evidence

The current rule-based system primarily evaluates information available from the URL and external scholarly metadata. It does not systematically retrieve and analyze the actual content of the page.

As a result, it cannot directly evaluate potentially useful page-level evidence such as author credentials, references, publication and revision dates, disclosure statements, corrections, or the quality of evidence supporting specific claims. Page retrieval and structured content analysis would be an important direction for future development.

### 6.3 Hand-Selected Scores and Weights

Several numerical values in the algorithm remain manually selected. Examples include the starting scores assigned to known domains and TLDs, the 0.10 preprint adjustment, the 0.20 Crossref adjustment, and the penalties associated with selected URL-path features.

These values produced improved performance, but they were not estimated statistically from a large independent training dataset. A more mature system could learn feature weights from labeled data and evaluate calibration on a separate validation or test set.

The optional combination of rule-based and LLM scores has a similar limitation. The supplied implementation weights the rule-based score at 0.60 and the LLM score at 0.40, but these weights are fixed rather than learned or empirically calibrated.

### 6.4 Dependence on External Metadata

Crossref improved the algorithm's ability to recognize unfamiliar scholarly domains, but it also introduced dependence on an external service. Network failures, timeouts, changes to the API, or incomplete metadata can prevent the scholarly signal from being obtained.

The retry and safe-fallback logic prevents these failures from crashing the application, but a URL can still receive a different score depending on whether Crossref metadata is available at the time of evaluation.

### 6.5 Heuristic Signals Can Produce False Positives and False Negatives

Features such as TLD type and URL wording are useful heuristics but are imperfect. A `.edu` page, for example, does not necessarily represent an institution's official scholarly position; it could contain personal or outdated material. Similarly, sensational wording may be associated with promotional or low-quality content but does not establish that the information itself is false.

For this reason, the algorithm combines multiple signals and uses relatively modest adjustments for individual heuristic features rather than allowing a single feature to determine the result.

### 6.6 Evaluation-Set Limitations

The supplied evaluation set contains 24 labeled URLs. This is useful for comparing algorithm versions consistently, but it is too small to establish performance across the diversity of websites encountered on the internet.

In addition, credibility labels necessarily involve judgment. A difference between an algorithmic score and a labeled score does not always imply that one numerical value is objectively correct. A larger independently labeled dataset, preferably involving multiple human evaluators and a held-out test set, would provide a stronger basis for evaluating and calibrating the system.

Future work could therefore combine URL-level features, page-level evidence, external metadata, learned feature weights, uncertainty estimates, and evaluation on a substantially larger independent dataset.

## 7. Literature Review

Research on web credibility supports the idea that credibility should be evaluated using multiple signals rather than a single characteristic of a URL or website. The Stanford Web Credibility Project, based on research involving more than 4,500 participants, identified several characteristics associated with perceived website credibility. These included making information verifiable through citations and references, demonstrating that a legitimate organization is responsible for the site, identifying relevant expertise, keeping information current, and limiting or clearly distinguishing promotional content (Fogg, 2002). These principles support a multi-signal approach in which organizational identity, scholarly evidence, and promotional characteristics contribute separately to a credibility assessment.

Research on online health information further demonstrates the difficulty of reducing credibility to a single feature. Sbaffi and Rowley (2017) reviewed 73 studies of trust and credibility in web-based health information and found that characteristics such as the authority of the website owner and author were positively associated with credibility, while advertising was negatively associated with it. This is consistent with the baseline algorithm's use of source identity and sponsored-content penalties, while also suggesting that future versions should examine page-level authorship and content rather than relying primarily on the URL.

A larger systematic review by Daraz et al. (2019) examined 153 studies covering 11,785 websites and found substantial variation in the quality of online health information. The results also varied according to the assessment instrument and type of source. These findings reinforce an important limitation of automated credibility scoring: credibility is multidimensional, and a numerical score should not be interpreted as a direct measurement of whether an individual claim is true.

External scholarly metadata provides another source of evidence. Crossref maintains structured metadata deposited by scholarly publishers and other trusted sources and makes this metadata available through a REST API. Available records can identify publication types such as journal articles and provide bibliographic and identifier information (Crossref, n.d.). In the present project, Crossref metadata was therefore used as independent evidence that an unfamiliar domain was associated with scholarly journal content. Importantly, this evidence was treated as one scoring signal rather than proof that the conclusions of an individual article were correct.

The use of the `.int` top-level domain also has an external basis. The Internet Assigned Numbers Authority (IANA) restricts `.int` registrations to qualifying intergovernmental organizations, including specialized agencies of the United Nations and organizations established through international treaties (IANA, n.d.). This makes `.int` different from an unrestricted generic domain suffix. The algorithm therefore treats `.int` as evidence about organizational status, although it does not assume that every individual page on such a domain is necessarily accurate.

Taken together, the literature supports a credibility model based on converging evidence rather than a single indicator. The final algorithm follows this approach by combining source-level reputation, domain characteristics, publication status, scholarly metadata, transport security, and selected URL-path characteristics. At the same time, the literature highlights information that the current implementation does not yet capture, particularly authorship, citations within the page, disclosure information, currency, and actual content quality. These provide clear directions for future development.

## 8. Conclusion

This project improved a baseline URL credibility-scoring algorithm by identifying specific failure modes and testing incremental modifications designed to address them. The final rule-based implementation incorporates preprint status, more careful interpretation of DOI evidence, external scholarly metadata from Crossref, recognition of the restricted `.int` domain, limited detection of sensational URL language, more robust handling of external metadata failures, and clearer user-facing explanations.

Across the supplied 24-URL evaluation set, the rule-based improvements reduced mean absolute error from 0.142 to 0.094, increased credibility-band accuracy from 66.7% to 83.3%, and reduced the worst individual error from 0.410 to 0.230. The final rule-based implementation also passed all 21 original automated tests plus three additional tests developed for the new behavior.

When the Claude LLM layer was enabled, performance improved further. The combined system achieved a mean absolute error of 0.058, credibility-band accuracy of 91.7%, and a worst individual error of 0.140. Thus, the strongest performance was obtained by combining the transparent, reproducible rule-based signals with the broader contextual assessment provided by the LLM.

An important design goal was to improve generalization rather than simply memorize the evaluation set. For this reason, I did not add individual high-error domains to the known-domain table merely to improve their scores. The use of Crossref illustrates this approach: an unfamiliar scholarly domain can receive additional evidence from an independent metadata source without having to be manually added to the program.

The resulting system remains a heuristic credibility estimator rather than a fact-checking system. Its numerical weights are not statistically learned, it does not yet systematically analyze page content, and its Crossref feature depends on an external service. Nevertheless, the experiments demonstrate that combining multiple independent signals can substantially improve the baseline algorithm while preserving its required interface and compatibility with the existing Streamlit application.

Future development could extend this approach by retrieving page-level evidence, analyzing authorship and citations, checking corrections or retractions, learning feature weights from a substantially larger labeled dataset, estimating uncertainty, and evaluating calibration on a held-out test set.

## References

Crossref. (n.d.). *REST API*. Crossref. https://www.crossref.org/documentation/retrieve-metadata/rest-api/

Daraz, L., Morrow, A. S., Ponce, O. J., Beuschel, B., Farah, M. H., Katabi, A., Alsawas, M., Majzoub, A. M., Benkhadra, R., Seisa, M. O., Ding, J., Prokop, L., & Murad, M. H. (2019). Can patients trust online health information? A meta-narrative systematic review addressing the quality of health information on the Internet. *Journal of General Internal Medicine, 34*(9), 1884–1891. https://doi.org/10.1007/s11606-019-05109-0

Fogg, B. J. (2002). *Stanford guidelines for web credibility*. Stanford Persuasive Technology Lab, Stanford University. https://credibility.stanford.edu/guidelines/

Internet Assigned Numbers Authority. (n.d.). *Eligibility for a .INT domain*. https://www.iana.org/help/int-eligibility

Sbaffi, L., & Rowley, J. (2017). Trust and credibility in web-based health information: A review and agenda for future research. *Journal of Medical Internet Research, 19*(6), e218. https://doi.org/10.2196/jmir.7579