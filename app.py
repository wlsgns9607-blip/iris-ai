# -*- coding: utf-8 -*-
"""3단계: 웹 서버. HTML 화면 + JSON API + Vercel 서버리스 완벽 호환."""
import os, json, sqlite3, joblib
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

rf = joblib.load(os.path.join(BASE_DIR, 'model_rf.joblib'))
nn = joblib.load(os.path.join(BASE_DIR, 'model_nn.joblib'))
NAMES = ['세토사', '버시컬러', '버지니카']
FIELDS = ('sepal_len', 'sepal_w', 'petal_len', 'petal_w')

# Vercel 서버리스(Read-only 파일시스템) 대비 메모리 히스토리 버퍼
memory_history = []

DATA_RANGES = {
    'sepal_len': {'name': '꽃받침 길이', 'min': 4.3, 'max': 7.9, 'avg': 5.84, 'unit': 'cm'},
    'sepal_w':   {'name': '꽃받침 너비', 'min': 2.0, 'max': 4.4, 'avg': 3.05, 'unit': 'cm'},
    'petal_len': {'name': '꽃잎 길이',   'min': 1.0, 'max': 6.9, 'avg': 3.76, 'unit': 'cm'},
    'petal_w':   {'name': '꽃잎 너비',   'min': 0.1, 'max': 2.5, 'avg': 1.20, 'unit': 'cm'}
}

SPECIES_BENCHMARKS = {
    0: {'name': '세토사',   'icon': '🌸', 'sepal_len': 5.0, 'sepal_w': 3.4, 'petal_len': 1.5, 'petal_w': 0.2, 'desc': '꽃잎이 매우 작고 폭이 좁은 아담형'},
    1: {'name': '버시컬러', 'icon': '🌿', 'sepal_len': 5.9, 'sepal_w': 2.8, 'petal_len': 4.3, 'petal_w': 1.3, 'desc': '중간 크기의 표준 균형형'},
    2: {'name': '버지니카', 'icon': '🌺', 'sepal_len': 6.6, 'sepal_w': 3.0, 'petal_len': 5.6, 'petal_w': 2.0, 'desc': '꽃받침과 꽃잎이 모두 크고 길쭉한 대형'}
}

def db():
    con = sqlite3.connect(os.path.join(BASE_DIR, 'iris.db'))
    con.row_factory = sqlite3.Row
    return con

@app.get('/')
def index():
    metrics_path = os.path.join(BASE_DIR, 'metrics.json')
    metrics = json.load(open(metrics_path, encoding='utf-8'))
    return render_template('index.html', metrics=metrics, data_ranges=DATA_RANGES, benchmarks=SPECIES_BENCHMARKS)

@app.get('/api/data_specs')
def data_specs():
    return jsonify({
        'ranges': DATA_RANGES,
        'benchmarks': SPECIES_BENCHMARKS
    })

@app.get('/api/random_sample')
def random_sample():
    try:
        with db() as con:
            row = con.execute('SELECT sepal_len, sepal_w, petal_len, petal_w, species FROM flowers ORDER BY RANDOM() LIMIT 1').fetchone()
        if row:
            d = dict(row)
            d['species_name'] = NAMES[d['species']]
            return jsonify(d)
    except Exception:
        pass
    import random
    sp = random.choice([0, 1, 2])
    b = SPECIES_BENCHMARKS[sp]
    return jsonify({
        'sepal_len': b['sepal_len'], 'sepal_w': b['sepal_w'],
        'petal_len': b['petal_len'], 'petal_w': b['petal_w'],
        'species': sp, 'species_name': b['name']
    })

@app.post('/api/predict')
def predict():
    try:
        data = request.get_json()
        x = [[float(data[k]) for k in FIELDS]]
        if not all(0 < v < 15 for v in x[0]):
            raise ValueError
    except (TypeError, KeyError, ValueError):
        return jsonify(error='네 칸 모두 실제 붓꽃 수치(꽃받침: 2.0~7.9cm, 꽃잎: 0.1~6.9cm)를 입력해 주세요.'), 400

    out = {}
    for key, model in (('rf', rf), ('nn', nn)):
        p = model.predict_proba(x)[0]
        best = int(p.argmax())
        out[key] = {'label': best, 'name': NAMES[best], 'prob': [round(float(v), 3) for v in p]}

    val = x[0]
    comparison = {
        'sepal_len': {'value': val[0], 'avg': DATA_RANGES['sepal_len']['avg'], 'diff': round(val[0] - DATA_RANGES['sepal_len']['avg'], 2)},
        'sepal_w':   {'value': val[1], 'avg': DATA_RANGES['sepal_w']['avg'], 'diff': round(val[1] - DATA_RANGES['sepal_w']['avg'], 2)},
        'petal_len': {'value': val[2], 'avg': DATA_RANGES['petal_len']['avg'], 'diff': round(val[2] - DATA_RANGES['petal_len']['avg'], 2)},
        'petal_w':   {'value': val[3], 'avg': DATA_RANGES['petal_w']['avg'], 'diff': round(val[3] - DATA_RANGES['petal_w']['avg'], 2)},
    }
    out['comparison'] = comparison

    record = {
        'sepal_len': x[0][0], 'sepal_w': x[0][1],
        'petal_len': x[0][2], 'petal_w': x[0][3],
        'rf_pred': out['rf']['label'], 'nn_pred': out['nn']['label']
    }
    try:
        with db() as con:
            con.execute('INSERT INTO predictions(sepal_len,sepal_w,petal_len,petal_w,rf_pred,nn_pred) '
                        'VALUES (?,?,?,?,?,?)', (*x[0], out['rf']['label'], out['nn']['label']))
    except Exception:
        pass
    memory_history.insert(0, record)
    if len(memory_history) > 10:
        memory_history.pop()

    return jsonify(out)

@app.get('/api/history')
def history():
    try:
        rows = db().execute('SELECT * FROM predictions ORDER BY id DESC LIMIT 8').fetchall()
        if rows:
            return jsonify([dict(r) for r in rows])
    except Exception:
        pass
    return jsonify(memory_history[:8])

@app.get('/api/stats')
def stats():
    try:
        rows = db().execute('SELECT species, COUNT(*) AS n, '
                            'ROUND(AVG(sepal_len),2) AS sepal_len, ROUND(AVG(sepal_w),2) AS sepal_w, '
                            'ROUND(AVG(petal_len),2) AS petal_len, ROUND(AVG(petal_w),2) AS petal_w '
                            'FROM flowers GROUP BY species').fetchall()
        if rows:
            return jsonify([dict(r) for r in rows])
    except Exception:
        pass
    default_stats = [
        {'species': 0, 'n': 50, 'sepal_len': 5.01, 'sepal_w': 3.43, 'petal_len': 1.46, 'petal_w': 0.24},
        {'species': 1, 'n': 50, 'sepal_len': 5.94, 'sepal_w': 2.77, 'petal_len': 4.26, 'petal_w': 1.33},
        {'species': 2, 'n': 50, 'sepal_len': 6.59, 'sepal_w': 2.97, 'petal_len': 5.55, 'petal_w': 2.03}
    ]
    return jsonify(default_stats)

if __name__ == '__main__':
    app.run(debug=True)
