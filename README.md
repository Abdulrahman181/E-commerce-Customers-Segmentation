### E-commerce Customers Segmentation

# 📌 Project Overview
- This project focuses on segmenting customers for an e-commerce platform based on their transactional behavior using unsupervised machine learning techniques. The goal is to identify different customer segments to optimize coupon offerings, thereby enhancing customer loyalty and satisfaction.
  The project is divided into two main tasks:

- Building a Dashboard for Stakeholders to provide insights into customer demographics, coupon usage, top-performing branches/cities, and customer retention.
  Customer Segmentation Using Unsupervised Learning to identify customer groups sharing similar behaviors and proposing strategies for increasing customer satisfaction.
  
# 📁 Dataset Overview
   - The dataset consists of five interrelated tables that provide detailed information about customers, transactions, branches, and merchants:

# Customers Table:
 - customer_id: Unique ID for each customer.
 - join_date: The date the customer joined.
 - city_id: Represents the customer’s city.
 - gender_id: Represents the customer’s gender.
   
# Genders Table:
 - gender_id: Unique ID for each gender.
 - gender_name: Name of the gender (e.g., male, female).
   
# Cities Table:
 - city_id: Unique ID for each city.
 - city_name: Name of the city.
   
# Transactions Table:
 - transaction_id: Unique ID for each transaction.
 - customer_id: ID of the customer who made the transaction.
 - transaction_date: Date the transaction occurred.
 - transaction_status: Status of the coupon (e.g., claimed, burnt).
 - coupon_name: Name of the coupon used.
 - burn_date: Date the coupon was burnt.
 - branch_id: ID of the branch where the coupon was used.
   
# Branches Table:
 - branch_id: Unique ID for each branch.
 - merchant_id: ID of the merchant that owns the branch.
   
# Merchants Table:
 - merchant_id: Unique ID for each merchant.
 - merchant_name: Name of the merchant.
   
# 🛠️ Project Requirements
Part 1: Dashboard for Stakeholders
The dashboard aims to present key insights from the dataset, targeted at stakeholders like business managers and marketing teams. The dashboard includes the following visualizations:
Customer Demographics: Distribution by gender and city.
Coupon Usage: Insights into the status of coupons over time (claimed vs burnt).
Top-performing Cities/Branches: Cities/branches with the highest coupon burns.
Customer Retention and Loyalty: Coupon usage trends and customer retention patterns.
Recommended visualizations include pie charts, time-series line charts, bar charts, heatmaps, and histograms.

# Part 2: Customer Segmentation Using Unsupervised Learning
The second part of the project focuses on developing an unsupervised machine learning model to segment customers based on transactional behavior.

# Key steps:

Feature Selection: Utilize customer demographics (e.g., gender, city) and transactional features (e.g., coupon usage, status).
Model Development: Train models like K-Means, DBSCAN, or hierarchical clustering, exploring different numbers of clusters.
Model Evaluation: Use evaluation metrics such as the Silhouette score and Inertia (for K-Means).
Segment Analysis: Analyze each segment to identify which groups should receive coupons to maximize loyalty.

# 🔍 Evaluation Metrics
Silhouette Score: Measures how similar an object is to its own cluster compared to other clusters.
Inertia: Sum of squared distances between each point and its assigned cluster’s centroid (used for K-Means).

# 💡 Key Findings
Segments of customers with high coupon usage frequency were identified, suggesting they should be targeted with more loyalty incentives.
Geographic and gender-specific preferences were discovered, helping tailor marketing strategies for different demographics.

# 🚀 Getting Started
To run the project:
Clone the repository from GitHub.
Install the necessary dependencies listed in requirements.txt.
Open the Jupyter Notebook to explore the data and train the models.

# 🧰 Tools and Libraries
Python: Core programming language used.
Pandas: For data manipulation and analysis.
Matplotlib/Seaborn: For data visualization.
Scikit-learn: For machine learning algorithms.
Plotly/Dash: For creating interactive dashboards.

# 📁 Repository Structure
├── data/                        # Contains dataset files
├── notebooks/                   # Jupyter Notebooks for data exploration and model development
├── dashboard/                   # Dashboard code and screenshots
├── README.md                    # Project overview and instructions
└── requirements.txt             # List of dependencies for the project

# 🔗 References
  Dataset description and structure as per the project documentation.

# 💻 Authors
££- Abdul Rahman Ahmed Mahmoud Hassan
 ££- abdulrahmannassar202@gmail.com
