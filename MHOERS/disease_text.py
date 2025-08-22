import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.naive_bayes import CategoricalNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Load dataset
df = pd.read_csv("C:/Users/User/Desktop/Project-Capstone/MHO-ERS/MHOERS/sample_datasets/Disease_symptom_and_patient_profile_dataset.csv")

# Preparing the Data (Label Encoding) to numbers
label_encoders = {}
data = df.copy()
for column in data.columns:
    if data[column].dtype == 'object':
        LE = LabelEncoder()
        data[column] = LE.fit_transform(data[column])
        label_encoders[column] = LE

# For example, "Yes" → 1, "No" → 0

# Features and target
X = data.drop(columns=["Outcome Variable"])
y = data["Outcome Variable"]




# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize models
models = {
    "Naive Bayes": CategoricalNB(),

    "Random Forest": RandomForestClassifier(random_state=42),
    "SVM": SVC(random_state=42)
}

# Train and evaluate models
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    print(f"\n{name} Results:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print(f"Precision: {precision_score(y_test, y_pred):.2f}")
    print(f"Recall: {recall_score(y_test, y_pred):.2f}")
    print(f"F1 Score: {f1_score(y_test, y_pred):.2f}")






