"""1단계: CSV -> SQLite DB. 빈칸(NA)은 SQL로 평균값을 채운다."""
import csv, sqlite3

con = sqlite3.connect("iris.db")
con.executescript(open("schema.sql", encoding="utf-8").read())

with open("data/iris2.csv", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    next(reader)  # 헤더 건너뛰기
    # 원본 파일은 앞 두 칼럼 이름이 '꽃잎'으로 되어 있지만 실제 값은 꽃받침이라
    # 값의 위치(순서)대로 sepal_len, sepal_w, petal_len, petal_w에 넣는다.
    rows = [[float(v) if v else None for v in r[:4]] + [int(r[4])] for r in reader]

con.executemany(
    "INSERT INTO flowers(sepal_len, sepal_w, petal_len, petal_w, species) VALUES (?,?,?,?,?)", rows)

for col in ("sepal_len", "sepal_w", "petal_len", "petal_w"):
    con.execute(f"UPDATE flowers SET {col} = (SELECT AVG({col}) FROM flowers "
                f"WHERE {col} IS NOT NULL) WHERE {col} IS NULL")
con.commit()
n, na = con.execute("SELECT COUNT(*), SUM(sepal_w IS NULL) FROM flowers").fetchone()
print(f"저장 완료: {n}송이, 남은 빈칸 {na}개")
