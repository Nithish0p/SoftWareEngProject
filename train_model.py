import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split

def train():
    try:
        df = pd.read_csv("expenses_dataset.csv")
    except FileNotFoundError:
        return print("❌ Run generate_data.py first!")

    X_train, X_test, y_train, y_test = train_test_split(df['Description'], df['Category'], test_size=0.2, random_state=42)
    
    # Logistic Regression with N-Grams (learns "Masala Tea" as a phrase)
    model = make_pipeline(TfidfVectorizer(ngram_range=(1,2)), LogisticRegression(max_iter=1000))
    model.fit(X_train, y_train)

    with open("expense_model.pkl", 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ Model Trained & Saved! Accuracy: {model.score(X_test, y_test)*100:.2f}%")

if __name__ == "__main__":
    train()