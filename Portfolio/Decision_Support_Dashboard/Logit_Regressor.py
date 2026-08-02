# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 22:38:39 2026
@author: Calvin King
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import (classification_report, roc_auc_score, 
                             accuracy_score, roc_curve, confusion_matrix)

'''
==================================================================
SECTION 1.1: SETUP AND DATA LOADING
==================================================================
Load all our business datasets and join them together into one place.
'''
pipeline_df = pd.read_csv('Data/sales_pipeline.csv')
accounts_df = pd.read_csv('Data/accounts.csv')
products_df = pd.read_csv('Data/products.csv')

# Combine sales pipeline, account details, and prodinfo into one main dataset
mdata = (pipeline_df
         .merge(accounts_df, on='account', how='left')
         .merge(products_df, on='product', how='left'))

# Check to make sure we don't have duplicate sales opportunities
print(f'''Duplicate Opportunities Post-Merge: 
      {mdata.duplicated(subset=["opportunity_id"]).sum()}\n\n''')
print('Column Review:', mdata.columns.tolist())


'''
==================================================================
SECTION 1.2: DATA CLEANING AND PREPARATION
==================================================================
Filter down to completed deals and handle missing business information.
'''
# Focus only on deals that reached a final result (either Won or Lost)
mdata_dv = mdata[mdata['deal_stage'].isin(['Won', 'Lost'])].copy()

# Fill in missing product and industry sector details with a 'Missing' label
cat_cols = ['product', 'sector']
mdata_dv[cat_cols] = mdata_dv[cat_cols].fillna('Missing')

# Fill missing revenue values using typical (median) values for that industry
if 'revenue' in mdata_dv.columns:
    global_median = mdata_dv['revenue'].median()
    sec_med = ( mdata_dv.groupby('sector')['revenue'].transform('median')
               .fillna(global_median) )
    mdata_dv['revenue'] = mdata_dv['revenue'].fillna(sec_med)

# Convert deal outcomes into numerical format (1 for Won, 0 for Lost)
mdata_dv['deal_stage'] = mdata_dv['deal_stage'].map({'Won': 1, 'Lost': 0})


'''
==================================================================
SECTION 1.3: FEATURE ENGINEERING & INITIAL EXPLORATION
==================================================================
Calculate key timelines and explore how deal size and duration affect win rates.
'''
# Calculate total sales cycle length in days
mdata_dv['engage_date'] = pd.to_datetime(mdata_dv['engage_date'])
mdata_dv['close_date'] = pd.to_datetime(mdata_dv['close_date'])
mdata_dv['close_days'] = (
    (mdata_dv['close_date'] - mdata_dv['engage_date']).dt.days )

# Remove invalid records with missing or negative sales days
mdata_dv = mdata_dv.dropna(subset=['close_days'])
mdata_dv = mdata_dv[mdata_dv['close_days'] >= 0]

# Visualize how win rates change across different deal sizes (Revenue)
mdata_dv['rev_bin'] = pd.qcut(mdata_dv['revenue'], q=10, duplicates='drop')
rev_win_rate = mdata_dv.groupby('rev_bin')['deal_stage'].mean()
plt.figure(figsize=(10, 4))
rev_win_rate.plot(kind='bar', color='blue', edgecolor='black')
plt.title('Win Rate by Revenue Bracket')
plt.ylabel('Win Rate (Proportion)')
plt.xlabel('Revenue Bracket')
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# Visualize how win rates change based on how long the deal stayed open
mdata_dv['days_bin'] = pd.qcut(mdata_dv['close_days'], q=10, duplicates='drop')
days_win_rate = mdata_dv.groupby('days_bin')['deal_stage'].mean()
plt.figure(figsize=(10, 4))
days_win_rate.plot(kind='bar', color='blue', edgecolor='black')
plt.title('Win Rate by Deal Duration (Days)')
plt.ylabel('Win Rate (Proportion)')
plt.xlabel('Deal Days Bracket')
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# Remove temporary chart grouping columns
mdata_dv = mdata_dv.drop(columns=['rev_bin', 'days_bin'])


'''
==================================================================
SECTION 1.4: ENCODING CATEGORICAL VARIABLES
==================================================================
Convert text categories (prodtype and sector) into numbers for modeling.
'''
num_features = ['close_days', 'revenue']
txt_features = ['product', 'sector']
x_feats = mdata_dv[num_features + txt_features].copy()
y = mdata_dv['deal_stage']

# Turn text categories into individual indicator columns (0 or 1)
x_encoded = ( 
    pd.get_dummies(x_feats, columns=txt_features, drop_first=False, dtype=int)
    )

# Remove most common category in each group to serve as baseline reference
basln_exclude = (
    [f'{col}_{x_feats[col].value_counts().idxmax()}' for col in txt_features]
    )
x_encoded = x_encoded.drop(columns=basln_exclude)


'''
==================================================================
SECTION 1.5: TRAINING/TEST SPLIT & FEATURE SCALING
==================================================================
Separate data into training and testing sets, create metrics, and scale revenue.
'''
# Split data: training (80%)/testing (20%) sets; preserv win/loss proportions
x_train, x_test, y_train, y_test = train_test_split(
    x_encoded, y, test_size=0.20, random_state=42, stratify=y
)
x_train, x_test = x_train.copy(), x_test.copy()

# Smooth out extreme dollar amounts using a log transformation
x_train['revenue'] = np.log1p(np.maximum(0, x_train['revenue']))
x_test['revenue'] = np.log1p(np.maximum(0, x_test['revenue']))

# Find avg sales duration for winning deals; flag deals > AVG
mean_win_days = ( mdata_dv.loc[x_train.index]
                 .loc[mdata_dv['deal_stage'] == 1, 'close_days']
                 .mean() )
mean_win_days_tst = ( mdata_dv.loc[x_test.index]
                     .loc[mdata_dv['deal_stage'] == 1, 'close_days']
                     .mean() )
print(f'TRAINING: Average Winning Deal Duration: {mean_win_days:.2f} days')
print(f'TESTING: Average Winning Deal Duration: {mean_win_days_tst:.2f} days')

x_train['is_delayed_deal'] = ( 
    (mdata_dv.loc[x_train.index, 'close_days'] > mean_win_days).astype(int) )
x_test['is_delayed_deal'] = ( 
    (mdata_dv.loc[x_test.index, 'close_days'] > mean_win_days).astype(int) )

# Remove the raw days column since we now use the delayed deal flag
x_train = x_train.drop(columns=['close_days'])
x_test = x_test.drop(columns=['close_days'])

# Keep an unscaled dataset copy for decision tree readability
x_train_tree = x_train.copy()
x_test_tree = x_test.copy()

# Standardize revenue values to a common scale for logistic regression
scaler = StandardScaler()
x_train[['revenue']] = scaler.fit_transform(x_train[['revenue']])
x_test[['revenue']] = scaler.transform(x_test[['revenue']])


'''
==================================================================
SECTION 2.1: CONTINUOUS DISTRIBUTION DIAGNOSTICS
==================================================================
Check the distribution shape of our revenue feature to confirm formatting.
'''
#Shap/Wilk on Scaled Revenue
sample_train_rev = x_train['revenue'].sample(min(5000, len(x_train)), random_state=42)
shapiro_stat, shapiro_p = stats.shapiro(sample_train_rev)

plt.figure(figsize=(9, 5))
plt.hist(x_train['revenue'], bins=40, density=True, color='blue', edgecolor='black', alpha=0.8, label='Histogram')
x_train['revenue'].plot(kind='kde', color='skyblue', linewidth=1.5, label='KDE')
plt.title(f'Scaled Revenue Distribution\nShapiro-Wilk: W = {shapiro_stat:.4f}, P = {shapiro_p:.4e}')
plt.xlabel('Scaled Revenue Z-Score')
plt.ylabel('Density')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()

#Hap/Wilk on Close_Days
close_days_sample = mdata_dv['close_days'].sample(min(5000,len(mdata_dv)), random_state=42)
sw_stat_days, sw_p_days = stats.shapiro(close_days_sample)

plt.figure(figsize=(9,5))
plt.hist(mdata_dv['close_days'],bins=40, density=True, color='blue',
         edgecolor='black',alpha=0.7,label='Histogram')
mdata_dv['close_days'].plot(kind='kde', color='red',linewidth=1.5,label='KDE')
plt.title(f'Close Days Distribution\nShapiro-Wilk: W = {sw_stat_days:.4f}, P = {sw_p_days:.4e}')
plt.xlabel('Close Days (Duration)')
plt.ylabel('Density')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()


'''
==================================================================
SECTION 2.2: MULTICOLLINEARITY CHECKS (VIF)
==================================================================
Ensure our predictor variables do not overlap too heavily with one another.
'''
x_train_sm = sm.add_constant(x_train)
vif_vals = [variance_inflation_factor(x_train_sm.values, i) for i in range(x_train_sm.shape[1])]
vif_data = pd.DataFrame({'Variable': x_train_sm.columns, 'VIF': vif_vals})
vif_filtered = vif_data[vif_data['Variable'] != 'const'].sort_values(by='VIF', ascending=True)

plt.figure(figsize=(10, 6))
colors = ['blue' if v < 5 else 'red' for v in vif_filtered['VIF']]
plt.barh(vif_filtered['Variable'], vif_filtered['VIF'], color=colors, edgecolor='black', alpha=0.8)
plt.axvline(x=5, color='orange', linestyle='--', linewidth=1.5, label='Overlap Threshold (VIF = 5)')
plt.title('Variable Overlap Diagnostic Scores (VIF)')
plt.xlabel('VIF Score (Lower is Better)')
plt.ylabel('Variables')
plt.legend(loc='lower right')
plt.tight_layout()
plt.show()


'''
==================================================================
SECTION 2.4: LOGISTIC REGRESSION MODEL
==================================================================
Fit a statistical model to calculate win probabilities and key business drivers.
'''
x_test_sm = sm.add_constant(x_test)
logm = sm.Logit(y_train, x_train_sm).fit_regularized(alpha=0.01, l1_wt=0)
print(logm.summary(), '\n\n')

'''
Optimization terminated successfully    (Exit mode 0)
            Current function value: 0.6521924792052516
            Iterations: 293
            Function evaluations: 293
            Gradient evaluations: 293
                           Logit Regression Results                           
==============================================================================
Dep. Variable:             deal_stage   No. Observations:                 5368
Model:                          Logit   Df Residuals:                     5355
Method:                           MLE   Df Model:                           12
Date:                Tue, 21 Jul 2026   Pseudo R-squ.:                0.008860
Time:                        21:42:21   Log-Likelihood:                -3501.6
converged:                       True   LL-Null:                       -3532.9
Covariance Type:            nonrobust   LLR p-value:                 7.537e-09
=============================================================================================
                                coef    std err          z      P>|z|      [0.025      0.975]
---------------------------------------------------------------------------------------------
const                         0.3074      0.064      4.806      0.000       0.182       0.433
revenue                            0        nan        nan        nan         nan         nan
product_GTK 500              -0.1307      0.440     -0.297      0.766      -0.993       0.731
product_GTX Plus Basic       -0.0119      0.085     -0.140      0.889      -0.179       0.156
product_GTX Plus Pro          0.1164      0.098      1.182      0.237      -0.077       0.309
product_GTXPro                0.0207      0.083      0.250      0.803      -0.142       0.183
product_MG Advanced                0        nan        nan        nan         nan         nan
product_MG Special            0.1351      0.082      1.656      0.098      -0.025       0.295
sector_employment                  0        nan        nan        nan         nan         nan
sector_entertainment          0.0185      0.126      0.147      0.883      -0.228       0.265
sector_finance               -0.1095      0.103     -1.060      0.289      -0.312       0.093
sector_marketing              0.0203      0.104      0.195      0.846      -0.184       0.225
sector_medical               -0.0005      0.089     -0.005      0.996      -0.174       0.173
sector_services                    0        nan        nan        nan         nan         nan
sector_software                    0        nan        nan        nan         nan         nan
sector_technolgy              0.0478      0.085      0.563      0.574      -0.119       0.214
sector_telecommunications    -0.0620      0.117     -0.528      0.598      -0.292       0.168
is_delayed_deal               0.4242      0.057      7.415      0.000       0.312       0.536
============================================================================================= 
'''

# Calculate Odds Ratios to see how each factor multiplies win likelihood
params = logm.params
conf = logm.conf_int()
conf.columns = ['2.5%', '97.5%']
odds_results = pd.DataFrame({
    'Coef': params, 
    'Odds Ratio': np.exp(params),    
    'p_value': logm.pvalues 
})

print('\nLogistic Regression Impact (Odds Ratios):\n', odds_results.round(4))

'''
Logistic Regression Impact (Odds Ratios):
                              Coef  Odds Ratio  p_value
const                      0.3074      1.3598   0.0000
revenue                    0.0000      1.0000      NaN
product_GTK 500           -0.1307      0.8775   0.7663
product_GTX Plus Basic    -0.0119      0.9881   0.8889
product_GTX Plus Pro       0.1164      1.1234   0.2374
product_GTXPro             0.0207      1.0209   0.8029
product_MG Advanced        0.0000      1.0000      NaN
product_MG Special         0.1351      1.1447   0.0977
sector_employment          0.0000      1.0000      NaN
sector_entertainment       0.0185      1.0187   0.8831
sector_finance            -0.1095      0.8962   0.2893
sector_marketing           0.0203      1.0205   0.8457
sector_medical            -0.0005      0.9995   0.9958
sector_services            0.0000      1.0000      NaN
sector_software            0.0000      1.0000      NaN
sector_technolgy           0.0478      1.0489   0.5737
sector_telecommunications -0.0620      0.9399   0.5976
is_delayed_deal            0.4242      1.5283   0.0000
'''

# Set our decision threshold based on the actual average overall win rate
baseline_cutoff = y_train.mean()

# Calculate predicted probabilities and apply cutoff
logit_test_probs = logm.predict(x_test_sm)
logit_test_preds = (logit_test_probs >= baseline_cutoff).astype(int)

logit_train_probs = logm.predict(x_train_sm)
logit_train_preds = (logit_train_probs >= baseline_cutoff).astype(int)

# Print overall model accuracy
logit_trn_acc = accuracy_score(y_train, logit_train_preds)
logit_tst_acc = accuracy_score(y_test, logit_test_preds)

print('Training Accuracy:', round(logit_trn_acc, 4))
print('Testing Accuracy: ', round(logit_tst_acc, 4), '\n\n')

'''
Training Accuracy: 0.544
Testing Accuracy:  0.5458 
'''

# Display detailed results table (Counts)
class_labels = ['Actual 0 (Lost)', 'Actual 1 (Won)']
col_labels = ['Predicted 0 (Lost)', 'Predicted 1 (Won)']

tst_matrix_raw = pd.DataFrame(
    confusion_matrix(y_test, logit_test_preds, labels=[0, 1]),
    index=class_labels,
    columns=col_labels
)

print('Testing Results (Count Table):\n', tst_matrix_raw, '\n\n')

# Display detailed results table (Percentages)
c_matrix_raw = confusion_matrix(y_test, logit_test_preds, labels=[0, 1])
c_matrix_pct = c_matrix_raw / c_matrix_raw.sum(axis=1, keepdims=True)

tst_confusion_pct_df = pd.DataFrame(
    c_matrix_pct,
    index=class_labels,
    columns=col_labels
).round(3)

'''
Testing Results (Count Table):
                  Predicted 0 (Lost)  Predicted 1 (Won)
Actual 0 (Lost)                 299                196
Actual 1 (Won)                  414                434 
'''

print('Testing Results (Proportion Table):\n', tst_confusion_pct_df, '\n\n')

'''
Testing Results (Proportion Table):
                  Predicted 0 (Lost)  Predicted 1 (Won)
Actual 0 (Lost)               0.604              0.396
Actual 1 (Won)                0.488              0.512 
'''

# Overall predictive power score
auc_logit = roc_auc_score(y_test, logit_test_probs)
print('Overall Performance Score (ROC-AUC):', round(auc_logit, 4), '\n\n')

'''Overall Performance Score (ROC-AUC): 0.5553 '''


'''
==================================================================
SECTION 2.5: DECISION TREE BENCHMARK MODEL
==================================================================
Train a simple, rules-based decision tree model to serve as a benchmark.
'''
tree_model = DecisionTreeClassifier(
    max_depth=3, 
    criterion='gini',
    min_samples_leaf=30,
    random_state=42
)

# Train using unscaled data for readable business rules
tree_model.fit(x_train_tree, y_train)

# Calculate win probabilities for training and testing data
y_train_prob_tree = tree_model.predict_proba(x_train_tree)[:, 1]
y_test_prob_tree = tree_model.predict_proba(x_test_tree)[:, 1]

# Apply the overall win rate threshold to classify outcomes
y_train_pred_tree = (y_train_prob_tree >= baseline_cutoff).astype(int)
y_test_pred_tree = (y_test_prob_tree >= baseline_cutoff).astype(int)

print("\n" + "="*66 + "\n           SECTION 2.5: DECISION TREE RESULTS\n" + "="*66)
print(f"Training Accuracy: {accuracy_score(y_train, y_train_pred_tree):.4f}")
print(f"Testing Accuracy:  {accuracy_score(y_test, y_test_pred_tree):.4f}")
print("\nDetailed Performance Report:")
print(classification_report(y_test, y_test_pred_tree))

# Accuracy Metrics and Feature Importance
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 1. Metric Benchmarks
acc_metrics = {
    'Decision Tree (Train)': accuracy_score(y_train, y_train_pred_tree),
    'Decision Tree (Test)': accuracy_score(y_test, y_test_pred_tree),
    'Target Goal (H1)': 0.70
}

bars = axes[0].bar(acc_metrics.keys(), acc_metrics.values(), 
                   color=['#7fcdbb', '#2c7fb8', '#d9534f'], edgecolor='black', alpha=0.85)
axes[0].axhline(0.70, color='#d9534f', linestyle='--', label='70% Target')
axes[0].set_ylim(0, 1.0)
axes[0].set_ylabel('Accuracy Score')
axes[0].set_title('Decision Tree Accuracy', fontsize=12, fontweight='bold')
axes[0].grid(axis='y', linestyle='--', alpha=0.5)

for bar in bars:
    yval = bar.get_height()
    axes[0].text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f"{yval:.2%}", 
                 ha='center', va='bottom', fontweight='bold')

# 2. Key Drivers (Feature Importance)
importances = tree_model.feature_importances_
top_idx = np.argsort(importances)[-5:] # Top 5 rules
axes[1].barh([x_train_tree.columns[i] for i in top_idx], importances[top_idx], 
             color='#2ca25f', edgecolor='black', alpha=0.85)
axes[1].set_xlabel('Gini Importance')
axes[1].set_title('Top Decision Drivers', fontsize=12, fontweight='bold')
axes[1].grid(axis='x', linestyle='--', alpha=0.5)

plt.suptitle('Decision Tree Model Executive Summary', fontsize=14, y=1.02, fontweight='bold')
plt.tight_layout()
plt.show()

'''
==================================================================
SECTION 2.6: COMPARATIVE MODEL VALIDATION
==================================================================
Plot ROC curves and draw the decision tree diagram for business review.
'''
auc_logit = roc_auc_score(y_test, logit_test_probs)
auc_tree  = roc_auc_score(y_test, y_test_prob_tree)

print("\n" + "="*66 + "\n         SECTION 2.6: PERFORMANCE COMPARISON\n" + "="*66)
print(f"Logistic Regression Overall Score (ROC-AUC): {auc_logit:.4f}")
print(f"Decision Tree Overall Score (ROC-AUC):        {auc_tree:.4f}")

fpr_logit, tpr_logit, _ = roc_curve(y_test, logit_test_probs)
fpr_tree, tpr_tree, _ = roc_curve(y_test, y_test_prob_tree)

# Plot ROC curves to compare predictive performance side-by-side
plt.figure(figsize=(9, 6))
plt.plot(fpr_logit, tpr_logit, color='blue', lw=2, label=f'Logistic Regression (AUC = {auc_logit:.4f})')
plt.plot(fpr_tree, tpr_tree, color='green', lw=2, label=f'Decision Tree (AUC = {auc_tree:.4f})')
plt.plot([0, 1], [0, 1], color='grey', linestyle='--', alpha=0.7, label='Random Baseline')
plt.title('Model Performance Comparison (ROC Curves)', fontsize=14, pad=15)
plt.xlabel('False Positive Rate (Incorrectly Flagged)', fontsize=12)
plt.ylabel('True Positive Rate (Correctly Identified Wins)', fontsize=12)
plt.grid(linestyle='--', alpha=0.5)
plt.legend(loc='lower right', fontsize=11)
plt.tight_layout()
plt.show()

# Render the Decision Tree visual diagram
plt.figure(figsize=(20, 10))
plot_tree(
    tree_model, 
    feature_names=x_train_tree.columns.tolist(), 
    class_names=['Lost', 'Won'], 
    filled=True, 
    rounded=True, 
    impurity=False,    
    fontsize=10
)
plt.title("Sales Win Decision Path", fontsize=16, pad=20)
plt.tight_layout()
plt.show()


'''
==================================================================
SECTION 2.7: ODDS RATIO BAR CHART
==================================================================
Ranking of features that either increase or decrease the likelihood of WON.
'''
odds_no_const = odds_results.drop(index='const', errors='ignore').sort_values(by='Odds Ratio', ascending=True)

plt.figure(figsize=(10, 6))
colors = ['crimson' if or_val < 1 else 'forestgreen' for or_val in odds_no_const['Odds Ratio']]
plt.barh(odds_no_const.index, odds_no_const['Odds Ratio'], color=colors, edgecolor='black', alpha=0.85)
plt.axvline(x=1.0, color='black', linestyle='--', linewidth=1.5, label='No Effect (Odds Ratio = 1.0)')

plt.title('Impact of Features on Deal Win Likelihood', fontsize=14, pad=15)
plt.xlabel('Odds Ratio (Values > 1 Increase Win Likelihood)', fontsize=12)
plt.ylabel('Feature', fontsize=12)
plt.legend(loc='lower right')
plt.grid(axis='x', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()


'''
==================================================================
SECTION 2.8: PREDICTED PROBABILITY CHART
==================================================================
Modeling how wins are separated from losses.
'''
plt.figure(figsize=(9, 5))

# Separate probabilities by actual outcome
probs_lost = logit_test_probs[y_test == 0]
probs_won  = logit_test_probs[y_test == 1]

# Plot density curves using Pandas built-in KDE
probs_lost.plot(kind='kde', color='crimson', linewidth=2, label='Actual Losses (0)')
probs_won.plot(kind='kde', color='forestgreen', linewidth=2, label='Actual Wins (1)')

# Fill area under curves for visual warmth
x_grid = np.linspace(0, 1, 500)
kde_lost = stats.gaussian_kde(probs_lost)(x_grid)
kde_won  = stats.gaussian_kde(probs_won)(x_grid)

plt.fill_between(x_grid, kde_lost, color='crimson', alpha=0.3)
plt.fill_between(x_grid, kde_won, color='forestgreen', alpha=0.3)

# Mark decision threshold line
plt.axvline(x=baseline_cutoff, color='black', linestyle='--', linewidth=1.5, 
            label=f'Decision Cutoff ({baseline_cutoff:.2%})')

plt.xlim(0, 1)
plt.title('Distribution of Predicted Win Probabilities by Actual Outcome', fontsize=14, pad=15)
plt.xlabel('Predicted Probability of Winning', fontsize=12)
plt.ylabel('Density', fontsize=12)
plt.legend(loc='upper right', fontsize=11)
plt.grid(linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

'''
This chart compares the model's predicted win scores against actual deal 
outcomes to see how well it separates successful sales from lost opportunities.
The vertical dashed line shows our cutoff score (63.15%). 
Ideally, lost deals (red line) would stack up on the left of the cutoff, and 
won deals (green line) would stack up on the right. 
Instead, both curves overlap almost completely across two main bumps 
(around 58% and 68%). Because lost and won deals fall into the exact 
same score ranges, the chart shows that predicting outcome probabilities alone 
isn't enough to clearly distinguish a winning deal from a losing one.
'''


'''
==================================================================
SECTION 2.9: CONFUSION HEATMAP
==================================================================
'''
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# 1. Raw Counts Plot
im0 = axes[0].imshow(tst_matrix_raw, cmap='Blues', aspect='auto')
axes[0].set_title('Test Predictions (Counts)', fontsize=13, pad=10)
axes[0].set_xticks([0, 1])
axes[0].set_yticks([0, 1])
axes[0].set_xticklabels(['Predicted Lost', 'Predicted Won'], fontsize=10)
axes[0].set_yticklabels(['Actual Lost', 'Actual Won'], fontsize=10)

# Annotate values inside count boxes
for i in range(2):
    for j in range(2):
        axes[0].text(j, i, f"{tst_matrix_raw.iloc[i, j]}",
                     ha='center', va='center', color='black', fontsize=12, fontweight='bold')

fig.colorbar(im0, ax=axes[0])

# 2. Proportions Plot
im1 = axes[1].imshow(tst_confusion_pct_df, cmap='Greens', aspect='auto')
axes[1].set_title('Test Predictions (% Row Normalized)', fontsize=13, pad=10)
axes[1].set_xticks([0, 1])
axes[1].set_yticks([0, 1])
axes[1].set_xticklabels(['Predicted Lost', 'Predicted Won'], fontsize=10)
axes[1].set_yticklabels(['Actual Lost', 'Actual Won'], fontsize=10)

# Annotate percentages inside proportion boxes
for i in range(2):
    for j in range(2):
        axes[1].text(j, i, f"{tst_confusion_pct_df.iloc[i, j]:.1%}",
                     ha='center', va='center', color='black', fontsize=12, fontweight='bold')

fig.colorbar(im1, ax=axes[1])

plt.suptitle('LogReg Classification Accuracy', fontsize=15, y=1.02)
plt.tight_layout()
plt.show()


'''
==================================================================
SECTION 2.10: ACCURACY SUPPORT VIZZES
==================================================================
'''
# Model Classification Accuracy vs. Target H1 Threshold
# 1. Pull metrics dynamically from active script variables
logit_acc = accuracy_score(y_test, logit_test_preds) 
tree_acc = accuracy_score(y_test, y_test_pred_tree)
baseline_win_rate = y_train.mean()
target_threshold = 0.70  # H1 Goal[cite: 1]

# Dynamic Confusion Matrix Math
tn, fp, fn, tp = confusion_matrix(y_test, logit_test_preds).ravel()
test_total = len(y_test)
correct_count = tp + tn

metrics = {
    'Baseline Win Rate': baseline_win_rate,
    'Null Threshold (H0)': target_threshold,
    'Logistic Regression (Test)': logit_acc,
    'Decision Tree (Test)': tree_acc
}

names = list(metrics.keys())
values = list(metrics.values())

# 2. Render Plot
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(names, values, color=['#8c8c8c', '#d9534f', '#2b5c8f', '#2e8b57'], alpha=0.9, edgecolor='black')

# Target line at 70%
ax.axhline(y=target_threshold, color='#d9534f', linestyle='--', linewidth=2, label=f'H1 Goal: > {target_threshold:.0%} Accuracy')

# Annotate exact percentages above bars
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.01, f"{yval:.2%}", 
            ha='center', va='bottom', fontweight='bold', fontsize=11)

# 3. Dynamic Callout Box (Fixes the contradiction logic)
diff_pct = (logit_acc - target_threshold) * 100

if logit_acc > target_threshold:
    status_text = f"Exceeds 70% Goal by +{diff_pct:.2f}% (H0 Rejected)"
    box_color = '#e6f2ff'
    edge_col = '#2b5c8f'
else:
    status_text = f"Fails 70% Goal by {diff_pct:.2f}% (Fail to Reject H0)"
    box_color = '#ffe6e6'
    edge_col = '#d9534f'

ax.annotate(
    f'CONFUSION MATRIX ACCURACY: {logit_acc:.2%}\n{status_text}',
    xy=(2, logit_acc), 
    xytext=(2, logit_acc + 0.20 if logit_acc < 0.65 else logit_acc + 0.07),
    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
    bbox=dict(boxstyle='round,pad=0.5', facecolor=box_color, edgecolor=edge_col, lw=1.5),
    fontsize=10, fontweight='bold', ha='center'
)

# Formatting
ax.set_ylim(0, 0.90)
ax.set_title('Test Set Confusion Matrix Accuracy vs. Hypothesis Target', fontsize=14, pad=20, fontweight='bold')
ax.set_ylabel('Classification Accuracy Score', fontsize=12)
ax.set_xlabel('Model Evaluation Benchmarks', fontsize=12)
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.legend(loc='lower right', fontsize=10)

# Fully Dynamic Footnote matching actual calculations
plt.figtext(0.5, -0.02, 
            f'Note: Accuracy calculated directly from Test Confusion Matrix: ({correct_count:,} Correct / {test_total:,} Total) = {logit_acc:.2%}', 
            ha='center', fontsize=9, fontstyle='italic', bbox=dict(facecolor='none', edgecolor='gray', boxstyle='round,pad=0.3'))

plt.tight_layout()
plt.show()

# Accuracy across thresholds
# Calculate accuracy across thresholds from 0.0 to 1.0
thresholds = np.linspace(0.01, 0.99, 100)
accuracies = [accuracy_score(y_test, (logit_test_probs >= t).astype(int)) for t in thresholds]

plt.figure(figsize=(8, 5))
plt.plot(thresholds, accuracies, color='blue', linewidth=2, label='Logistic Regression Accuracy')

# Mark chosen cutoff (~0.6315) and 70% target
plt.axvline(x=baseline_cutoff, color='black', linestyle='--', label=f'Chosen Cutoff ({baseline_cutoff:.2%})')
plt.axhline(y=0.70, color='red', linestyle=':', label='70% Hypothesis Goal')

plt.title('Classification Accuracy across Decision Thresholds', fontsize=13, pad=15)
plt.xlabel('Probability Decision Threshold', fontsize=11)
plt.ylabel('Accuracy Score', fontsize=11)
plt.grid(linestyle='--', alpha=0.5)
plt.legend(loc='lower left')
plt.tight_layout()
plt.show()
