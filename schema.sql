-- 꽃 원본 데이터 (실행할 때마다 새로 만듦)
DROP TABLE IF EXISTS flowers;
CREATE TABLE flowers (
  id INTEGER PRIMARY KEY,
  sepal_len REAL, sepal_w REAL,   -- 꽃받침 길이, 폭
  petal_len REAL, petal_w REAL,   -- 꽃잎 길이, 폭
  species INTEGER                 -- 0 세토사 / 1 버시컬러 / 2 버지니카
);
-- 사용자가 예측한 기록 (유지됨)
CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sepal_len REAL, sepal_w REAL, petal_len REAL, petal_w REAL,
  rf_pred INTEGER, nn_pred INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
