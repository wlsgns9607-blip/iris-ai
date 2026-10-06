"""2단계: DB에서 데이터를 읽어 머신러닝 + 신경망 모델을 학습하고 저장한다."""
import json, sqlite3, joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

df = pd.read_sql("SELECT sepal_len, sepal_w, petal_len, petal_w, species FROM flowers",
                 sqlite3.connect("iris.db"))
X, y = df.iloc[:, :4].values, df["species"].values  # .values: 이름표 없이 숫자만 사용
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

models = {
    "rf": RandomForestClassifier(n_estimators=200, random_state=42),            # 머신러닝
    "nn": make_pipeline(StandardScaler(),                                        # 딥러닝(신경망)
                        MLPClassifier(hidden_layer_sizes=(16, 8), max_iter=3000, random_state=42)),
}
metrics = {}
for key, model in models.items():
    model.fit(X_tr, y_tr)
    metrics[key] = round(model.score(X_te, y_te), 3)
    joblib.dump(model, f"model_{key}.joblib")
json.dump(metrics, open("metrics.json", "w"))
print("테스트 정확도:", metrics)
