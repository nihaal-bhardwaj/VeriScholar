import json
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def main():
    # 1. Load Data
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'datasets', 'synthetic_papers.json')
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    texts = [item['text'] for item in data]
    labels = [item['label'] for item in data] # 0 = legitimate, 1 = suspicious
    
    # In real world, we'd split. Here we train on all to guarantee the mock works
    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)
    
    # 2. Build Pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=1000)),
        ('clf', RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42))
    ])
    
    # 3. Train
    print("Training TF-IDF + RandomForest baseline model...")
    pipeline.fit(X_train, y_train)
    
    # 4. Evaluate
    y_pred = pipeline.predict(X_test)
    print("Wait, evaluating on test split:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
    
    # Retrain on full dataset for the API
    pipeline.fit(texts, labels)
    
    # 5. Save model
    save_dir = os.path.join(os.path.dirname(__file__), '..', 'saved_models')
    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(save_dir, 'rf_baseline.joblib')
    
    joblib.dump(pipeline, model_path)
    print(f"Model successfully saved to {model_path}")

if __name__ == "__main__":
    main()
