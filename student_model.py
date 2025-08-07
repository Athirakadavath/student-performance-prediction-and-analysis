#student performance prediction and analysis
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, explained_variance_score, mean_absolute_percentage_error
import joblib
import numpy as np
import matplotlib.pyplot as plt

# Load dataset
dataset_file = 'student_performance_modified.xlsx'
try:
    data = pd.read_excel(dataset_file)
except FileNotFoundError:
    print(f"Error: {dataset_file} not found. Ensure the file is in the project folder.")
    exit()

# Feature Selection
X = data[['Gender', 'Age', 'Address', 'Parent_Edu', 'Travel Time',
          'Study Time', 'Failures', 'Extra Classes', 'Extra Curricular Activities',
          'Internet Access', 'Health', 'Absences', 'Sub1 Mark', 'Sub2 Mark', 'Sub3 Mark']]

# Encode categorical features
X = pd.get_dummies(X, drop_first=True)

# Target Values (Final Marks)
y = data[['Sub1 Final Mark', 'Sub2 Final Mark', 'Sub3 Final Mark']]

# Calculate statistics for z-score calculation
subject_stats = {
    'Sub1': {'mean': data['Sub1 Final Mark'].mean(), 'std': data['Sub1 Final Mark'].std()},
    'Sub2': {'mean': data['Sub2 Final Mark'].mean(), 'std': data['Sub2 Final Mark'].std()},
    'Sub3': {'mean': data['Sub3 Final Mark'].mean(), 'std': data['Sub3 Final Mark'].std()}
}
joblib.dump(subject_stats, 'subject_stats.pkl')

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the Model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate Model
y_pred = model.predict(X_test)

# Accuracy Metrics
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
ev = explained_variance_score(y_test, y_pred)
mape = mean_absolute_percentage_error(y_test, y_pred)

print(f"R-squared (Accuracy): {r2:.2f}")
print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Explained Variance Score (EVS): {ev:.2f}")
print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}")

# Save Model
joblib.dump(model, 'student_model.pkl')

# Visualizing Actual vs Predicted Marks
plt.figure(figsize=(8, 5))
plt.plot(y_test.values.flatten(), label='Actual Marks', marker='o')
plt.plot(y_pred.flatten(), label='Predicted Marks', marker='x')
plt.title('Actual vs Predicted Marks')
plt.xlabel('Student Index')
plt.ylabel('Marks')
plt.legend()
plt.grid(True)
plt.show()

# Sample Prediction with Weak Subject Identification using Z-Score approach
model = joblib.load('student_model.pkl')
subject_stats = joblib.load('subject_stats.pkl')

# Sample Input for Testing
sample_input = np.array([[1, 16, 1, 3, 2, 3, 0, 1, 1, 1, 5, 3, 21, 17, 45]])
predicted_marks = model.predict(sample_input)[0]

# Z-score threshold for weak subject identification
Z_SCORE_THRESHOLD = -0.75

# Identify Weak Subjects using Z-scores
weak_subjects = []
z_scores = []

# Calculate z-score for each subject
z_score_sub1 = (predicted_marks[0] - subject_stats['Sub1']['mean']) / subject_stats['Sub1']['std']
z_score_sub2 = (predicted_marks[1] - subject_stats['Sub2']['mean']) / subject_stats['Sub2']['std']
z_score_sub3 = (predicted_marks[2] - subject_stats['Sub3']['mean']) / subject_stats['Sub3']['std']

# Store z-scores for reporting
z_scores = [z_score_sub1, z_score_sub2, z_score_sub3]

# Identify weak subjects based on z-scores
if z_score_sub1 < Z_SCORE_THRESHOLD:
    weak_subjects.append("Subject 1")
if z_score_sub2 < Z_SCORE_THRESHOLD:
    weak_subjects.append("Subject 2")
if z_score_sub3 < Z_SCORE_THRESHOLD:
    weak_subjects.append("Subject 3")

print(f"Predicted Marks: {predicted_marks}")
print(f"Z-scores: Subject 1: {z_score_sub1:.2f}, Subject 2: {z_score_sub2:.2f}, Subject 3: {z_score_sub3:.2f}")
print(f"Weak Subject(s): {', '.join(weak_subjects) if weak_subjects else 'None'}")

# Visualization of Z-scores
plt.figure(figsize=(10, 6))
subjects = ['Subject 1', 'Subject 2', 'Subject 3']
plt.bar(subjects, z_scores)
plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
plt.axhline(y=Z_SCORE_THRESHOLD, color='red', linestyle='--', label=f'Threshold ({Z_SCORE_THRESHOLD})')
plt.title('Subject Performance Z-Scores')
plt.ylabel('Z-Score')
plt.legend()
plt.grid(True, axis='y', alpha=0.3)

# Highlight weak subjects in red
for i, z in enumerate(z_scores):
    if z < Z_SCORE_THRESHOLD:
        plt.bar(subjects[i], z, color='red')

plt.show()