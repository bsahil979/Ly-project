# Project Report: AI-Driven Multi-Asset Portfolio Intelligence & Risk Analytics Platform

## Table of Contents

**List of Figures** .......................................................................................................................... v  
**List of Tables** ........................................................................................................................... vi  
**List of Formulae** ....................................................................................................................... vii  
**Nomenclature** ........................................................................................................................... viii

**1. Introduction** .......................................................................................................................... 1  
   1.1. Introduction ...................................................................................................................... 1  
   1.2. Motivation ........................................................................................................................ 2  
   1.3. Scope ............................................................................................................................... 3  
   1.4. Organization of the report ................................................................................................ 3

**2. Literature Survey** .................................................................................................................. 4

**3. Text Mining Methods** ............................................................................................................ 9  
   3.1. Text Pre-processing ........................................................................................................... 9  
   3.2. News Polarity Labeling ................................................................................................... 12  
   3.3. Classification Techniques ................................................................................................ 13  
      3.3.1. Random Forest ........................................................................................................ 13  
      3.3.2. Naïve Bayes ............................................................................................................ 14  
      3.3.3. Support Vector Machine (SVM) ............................................................................. 15  
   3.4. Evaluation Metrics ........................................................................................................... 19  
      3.4.1. Confusion Matrix ..................................................................................................... 19  
      3.4.2. Accuracy .................................................................................................................. 19  
      3.4.3. Precision and Recall ................................................................................................ 20  
      3.4.4. ROC Area ................................................................................................................. 20

**4. Proposed Methodology and Results** ..................................................................................... 22  
   4.1. Proposed System Design ................................................................................................. 22  
      4.1.1. Data Collection ........................................................................................................ 23  
      4.1.2. Training Dataset Labeling ....................................................................................... 24  
      4.1.3. Text Pre-processing ................................................................................................. 26  
      4.1.4. Convert Text to DTM (Document-Term Matrix) .................................................... 26  
      4.1.5. Building Classifier Models ....................................................................................... 27  
      4.1.6. Testing and Evaluation ............................................................................................ 27  
   4.2. Observations ................................................................................................................... 36

**5. Conclusion** ............................................................................................................................ 38

**6. Future Work** ......................................................................................................................... 39

**7. References** ............................................................................................................................ 40

**8. Authors Publication** .............................................................................................................. 43

**9. Acknowledgments** ................................................................................................................ 44

---

## List of Figures
- 3.1 Random Forest Architecture
- 3.2 Support Vector Machine (Hyperplane Separation)
- 3.3 Non-linear Separable Problem
- 4.1 System Design - Training Phase Workflow
- 4.2 System Design - Testing Phase Workflow
- 4.3 Original News Dataset (Headlines and Content)
- 4.4 Sentiment Detection Algorithm Output
- 4.5 Data Pre-processing Pipeline
- 4.6 Plot of News Sentiment Score vs. Actual Stock Price for Train Dataset
- 4.7 Plot of News Sentiment Score vs. Actual Stock Price for Validation Data
- 4.8 Plot of News Sentiment Score vs. Actual Stock Price for Test Dataset

## List of Tables
- 3.1 Confusion Matrix for Sentiment Classification
- 4.1 Comparison of Different Classifier Models (RF vs. SVM vs. NB)
- 4.2 Result of Testing Models with Real-time Market News

## List of Formulae
- **Relative Strength Index (RSI):** $RSI = 100 - \frac{100}{1 + RS}$
- **Moving Average Convergence Divergence (MACD):** $MACD = EMA_{12} - EMA_{26}$
- **TF-IDF Calculation:** $TFIDF = TF \times \log(\frac{N}{df})$
- **Accuracy Metric:** $Accuracy = \frac{TP + TN}{TP + TN + FP + FN}$
- **Sharpe Ratio:** $Sharpe = \frac{R_p - R_f}{\sigma_p}$

---

## 1. Introduction

### 1.1 Introduction
The "AI-Driven Multi-Asset Portfolio Intelligence & Risk Analytics Platform" is an advanced financial technology solution designed to empower retail investors with institutional-grade insights. While modern brokerage platforms have simplified the act of buying and selling assets, they often lack the analytical depth required for effective risk management and strategy optimization. This project bridges that gap by integrating technical analysis, sentiment intelligence from news sources, and machine learning models to provide a holistic view of portfolio health.

### 1.2 Motivation
Retail investors often face "information overload" without having the tools to filter significant market signals from noise. The motivation behind this project is to democratize financial intelligence. By automating the extraction of sentiment from financial news and correlating it with historical price action, we can provide predictive insights that were previously available only to quantitative hedge funds.

### 1.3 Scope
The scope of this system includes:
- **Assets Supported:** Stocks, ETFs, and Indices (Phase 1).
- **Data Analysis:** Real-time and historical data fetching via Yahoo Finance.
- **Intelligence Layer:** Sentiment analysis of news, technical indicator computation, and RL-based strategy simulation.
- **Optimization:** Suggesting asset allocation based on Modern Portfolio Theory.

### 1.4 Organization of the Report
The report is organized into nine chapters. Chapter 2 surveys existing literature in the field. Chapter 3 details the text mining methods used for sentiment analysis. Chapter 4 describes the proposed methodology, system architecture, and experimental results. Chapters 5 and 6 present the conclusion and potential for future enhancements.

---

## 2. Literature Survey
Recent studies have shown that market prices are not only influenced by historical numerical data but also by public sentiment and news events. Research by Bollen et al. (2011) demonstrated that social media sentiment can predict changes in the Dow Jones Industrial Average. Traditional models like ARIMA and GARCH have been superseded by hybrid models that combine technical indicators with NLP-based sentiment scores. This project builds upon these findings by utilizing modern NLP architectures like FinBERT and traditional classifiers like SVM for robust sentiment extraction.

---

## 3. Text Mining Methods

### 3.1 Text Pre-processing
To extract meaningful information from raw financial news, the text undergoes several cleaning steps:
1. **Lowercasing:** Standardizing the text.
2. **Stopword Removal:** Filtering out common words (e.g., "the", "is") that do not carry sentiment.
3. **Tokenization:** Breaking sentences into individual words/tokens.
4. **Lemmatization:** Reducing words to their root forms (e.g., "rising" to "rise").

### 3.2 News Polarity Labeling
Each processed headline is assigned a sentiment score (Polarity) ranging from -1 (Extremely Bearish) to +1 (Extremely Bullish). This labeling is performed using a combination of lexicon-based methods and pre-trained financial transformers.

### 3.3 Classification Techniques
#### 3.3.1 Random Forest
An ensemble learning method that constructs multiple decision trees. It is robust against overfitting and handles non-linear relationships between sentiment scores and price movements effectively.

#### 3.3.2 Naïve Bayes
A probabilistic classifier based on Bayes' Theorem. It is computationally efficient and performs well on text classification tasks where features (words) are assumed to be independent.

#### 3.3.3 Support Vector Machine (SVM)
SVM finds the optimal hyperplane that separates data points into distinct classes (Bullish/Bearish). It is particularly effective in high-dimensional spaces, making it ideal for vectorized text data.

### 3.4 Evaluation Metrics
We evaluate our sentiment engine using:
- **Confusion Matrix:** To visualize true vs. false predictions.
- **Accuracy:** The ratio of correct predictions to total predictions.
- **Precision and Recall:** To measure the exactness and completeness of the model.
- **ROC Area:** To evaluate the model's ability to distinguish between classes across various thresholds.

---

## 4. Proposed Methodology and Results

### 4.1 Proposed System Design
The system follows a microservices architecture:
1. **Frontend:** Next.js for interactive dashboards.
2. **Backend Gateway:** Spring Boot for security and portfolio management.
3. **Analytics Engine:** Python (FastAPI) for ML/DL computations.

#### 4.1.1 Data Collection
Market data (OHLCV) and dividends are fetched using the `yfinance` API. Financial news is gathered through specialized news crawlers or external news APIs.

#### 4.1.2 Training Dataset Labeling
Historical news data is labeled by cross-referencing news publication times with subsequent stock price movements (e.g., if a headline precedes a 2% price jump, it is labeled 'Positive').

#### 4.1.3 Text Pre-processing
(Details as described in Section 3.1)

#### 4.1.4 Convert Text to DTM
The cleaned text is converted into a Document-Term Matrix using **TF-IDF (Term Frequency-Inverse Document Frequency)** to weigh the importance of specific financial keywords.

#### 4.1.5 Building Classifier Models
Models (RF, SVM, NB) are trained on the DTM to recognize patterns between text and sentiment. Additionally, an LSTM layer is used for price sequence prediction.

#### 4.1.6 Testing and Evaluation
The system is tested using a 70/15/15 split for training, validation, and testing.

### 4.2 Observations
Initial results indicate that combining technical indicators (RSI, MACD) with sentiment scores significantly improves the prediction accuracy of price trends compared to using numerical data alone. The plots in Figures 4.6 - 4.8 demonstrate a strong correlation between "Bullish" news clusters and upward price momentum.

---

## 5. Conclusion
The "AI-Driven Multi-Asset Portfolio Intelligence Platform" successfully integrates diverse data sources—market prices and financial news—to provide comprehensive investment intelligence. The use of robust text mining methods combined with state-of-the-art machine learning models ensures that users receive actionable, data-driven insights for better portfolio management.

## 6. Future Work
- **Live Trading Integration:** Expanding the platform to support direct order execution via broker APIs.
- **Advanced NLP:** Implementing Transformer-based models (e.g., GPT-4/BERT) for deeper contextual understanding of financial reports.
- **Multi-lingual Support:** Analyzing news from international markets in various languages.

---

## 7. References
1. Bollen, J., Mao, H., & Zeng, X. (2011). Twitter mood predicts the stock market. *Journal of Computational Science*.
2. Markowitz, H. (1952). Portfolio Selection. *The Journal of Finance*.
3. Yahoo Finance API Documentation.
4. TensorFlow and Scikit-learn Documentation.

---

## 8. Authors Publication
(Details regarding any papers or articles published during the development of this project)

## 9. Acknowledgments
We would like to thank our mentors and the open-source community for providing the tools and guidance necessary to complete this project. We also acknowledge the use of Yahoo Finance for providing the essential data for our analytics engine.
