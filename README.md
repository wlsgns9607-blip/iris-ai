# 붓꽃 품종 판별기 (ML + 딥러닝 + SQL + Flask)

## 실행 방법 (처음 한 번)
    pip install -r requirements.txt
    python init_db.py     # CSV -> DB (SQL로 빈칸 채우기)
    python train.py       # 모델 학습 및 저장
## 서버 켜기
    python app.py         # 브라우저에서 http://127.0.0.1:5000

## 파일 역할
- data/iris2.csv : 원본 데이터        - schema.sql : DB 테이블 설계(SQL)
- init_db.py : DB 만들기              - train.py : 머신러닝/딥러닝 학습
- app.py : 서버 + JSON API            - templates/index.html, static/ : 화면(HTML, CSS, JS)
