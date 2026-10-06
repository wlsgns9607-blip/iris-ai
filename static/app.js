const NAMES = ["세토사", "버시컬러", "버지니카"];
const FIELDS = ["sepal_len", "sepal_w", "petal_len", "petal_w"];
const FIELD_NAMES = {
  sepal_len: "꽃받침 길이",
  sepal_w:   "꽃받침 너비",
  petal_len: "꽃잎 길이",
  petal_w:   "꽃잎 너비"
};

const PRESETS = {
  setosa:     { sepal_len: 5.0, sepal_w: 3.4, petal_len: 1.5, petal_w: 0.2 },
  versicolor: { sepal_len: 5.9, sepal_w: 2.8, petal_len: 4.3, petal_w: 1.3 },
  virginica:  { sepal_len: 6.6, sepal_w: 3.0, petal_len: 5.6, petal_w: 2.0 }
};

const $ = id => document.getElementById(id);

// 1. 슬라이더 & 숫자 입력창 양방향 동기화
FIELDS.forEach(f => {
  const numInput = $(f);
  const rangeInput = $(f + "_range");

  if (numInput && rangeInput) {
    rangeInput.addEventListener("input", e => {
      numInput.value = e.target.value;
    });

    numInput.addEventListener("input", e => {
      let val = parseFloat(e.target.value);
      const min = parseFloat(numInput.min);
      const max = parseFloat(numInput.max);
      if (isNaN(val)) return;
      if (val < min) val = min;
      if (val > max) val = max;
      rangeInput.value = val;
    });
  }
});

// 2. 프리셋 버튼 클릭 이벤트
document.querySelectorAll(".btn-preset[data-preset]").forEach(btn => {
  btn.addEventListener("click", () => {
    const key = btn.dataset.preset;
    const values = PRESETS[key];
    if (values) {
      FIELDS.forEach(f => {
        $(f).value = values[f];
        $(f + "_range").value = values[f];
      });
      $("randomNotice").hidden = true;
      triggerPredict();
    }
  });
});

// 3. 실제 데이터셋에서 랜덤 1건 추출
$("btnRandom").addEventListener("click", async () => {
  try {
    const res = await fetch("/api/random_sample");
    const data = await res.json();
    if (res.ok) {
      FIELDS.forEach(f => {
        $(f).value = data[f];
        $(f + "_range").value = data[f];
      });
      $("randomNotice").textContent = `🎲 실제 DB 데이터 추출: 정답은 [${data.species_name}]`;
      $("randomNotice").hidden = false;
      triggerPredict();
    }
  } catch (err) {
    console.error(err);
  }
});

// 4. AI 판별 결과 렌더링
function show(id, r) {
  $(id).innerHTML = `
    <div class="pick-wrap">
      <span class="pick-label">최종 판정</span>
      <span class="pick">${r.name}</span>
    </div>
    <div class="bars-container">
      ${r.prob.map((p, i) => `
        <div class="bar-row ${i === r.label ? 'is-best' : ''}">
          <span class="bar-name">${NAMES[i]}</span>
          <div class="bar-track"><i style="width: ${Math.round(p * 100)}%"></i></div>
          <span class="bar-pct">${Math.round(p * 100)}%</span>
        </div>
      `).join("")}
    </div>
  `;
}

// 5. 데이터 지표 비교 렌더링
function renderComparison(comp) {
  const container = $("compGrid");
  if (!container || !comp) return;

  container.innerHTML = Object.keys(comp).map(f => {
    const item = comp[f];
    const diffSign = item.diff > 0 ? `+${item.diff}` : `${item.diff}`;
    const diffColor = item.diff > 0 ? "var(--accent-red)" : (item.diff < 0 ? "var(--accent-blue)" : "var(--muted)");

    return `
      <div class="comp-card">
        <div class="comp-title">${FIELD_NAMES[f]}</div>
        <div class="comp-val"><strong>${item.value}</strong> cm</div>
        <div class="comp-avg">전체 평균 ${item.avg} cm</div>
        <div class="comp-diff" style="color: ${diffColor}">
          평균 대비 <b>${diffSign} cm</b>
        </div>
      </div>
    `;
  }).join("");
}

// 6. 예측 실행
async function triggerPredict() {
  $("err").textContent = "";
  const body = Object.fromEntries(FIELDS.map(f => [f, $(f).value]));

  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  const data = await res.json();
  if (!res.ok) {
    $("err").textContent = data.error;
    return;
  }

  show("rf", data.rf);
  show("nn", data.nn);
  renderComparison(data.comparison);

  const consensus = $("consensusBadge");
  if (consensus) {
    if (data.rf.label === data.nn.label) {
      consensus.textContent = `✅ 두 모델 일치: ${data.rf.name}`;
      consensus.className = "panel-tip tip--match";
    } else {
      consensus.textContent = `⚠️ 모델 의견 분분: ML(${data.rf.name}) vs DL(${data.nn.name})`;
      consensus.className = "panel-tip tip--diff";
    }
  }

  $("result").hidden = false;
  loadHistory();
}

$("go").addEventListener("click", triggerPredict);

// 7. 최근 기록 로드
async function loadHistory() {
  const res = await fetch("/api/history");
  const rows = await res.json();
  if (rows && rows.length) {
    $("history").innerHTML = rows.map(r => `
      <li class="history-item">
        <div class="h-specs">
          <span class="h-tag">입력</span>
          꽃받침 ${r.sepal_len}×${r.sepal_w}cm · 꽃잎 ${r.petal_len}×${r.petal_w}cm
        </div>
        <div class="h-pred">
          <span>ML: <b>${NAMES[r.rf_pred]}</b></span>
          <span>DL: <b>${NAMES[r.nn_pred]}</b></span>
        </div>
      </li>
    `).join("");
  }
}

// 8. 통계 지표 요약표 로드
async function loadStats() {
  const res = await fetch("/api/stats");
  const rows = await res.json();
  if (rows && rows.length) {
    document.querySelector("#stats tbody").innerHTML = rows.map(r => `
      <tr>
        <td><strong>${NAMES[r.species]}</strong></td>
        <td>${r.n}건</td>
        <td>${r.sepal_len || '-'} cm</td>
        <td>${r.sepal_w || '-'} cm</td>
        <td>${r.petal_len || '-'} cm</td>
        <td>${r.petal_w || '-'} cm</td>
      </tr>
    `).join("");
  }
}

// 초기화
loadHistory();
loadStats();
triggerPredict(); // 첫 화면 로드 시 즉시 예측 지표 보여주기
