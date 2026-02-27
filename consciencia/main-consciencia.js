// Firebase
var firebaseConfig = {
  apiKey: "AIzaSyCQ34mqiXRUN-bJ4TosXKrYJbvmyhUYcP8",
  authDomain: "consciencia-7408b.firebaseapp.com",
  projectId: "consciencia-7408b",
  storageBucket: "consciencia-7408b.firebasestorage.app",
  messagingSenderId: "372093197047",
  appId: "1:372093197047:web:e445b11ea26e3c1a87d1f2"
};

firebase.initializeApp(firebaseConfig);

var db = firebase.firestore();

//global variables
var selectedGradeGlobal = null;      // 1 ou 2
var selectedModeGlobal = null;       // "Com Critério" | "Sem Critério"
var evaluationViewOpen = false;      // toggle dentro da carta

// Cores oficiais (aproximações padrão das ODS)
var ODS_COLORS = {
  1: "#E5243B",  2: "#DDA63A",  3: "#4C9F38",  4: "#C5192D",  5: "#FF3A21",
  6: "#26BDE2",  7: "#FCC30B",  8: "#A21942",  9: "#FD6925", 10: "#DD1367",
  11:"#FD9D24", 12:"#BF8B2E", 13:"#3F7E44", 14:"#0A97D9", 15:"#56C02B",
  16:"#00689D", 17:"#19486A"
};

// Utils
function formatLevel(level) {
  switch (level) {
    case 1: 
      return "I";
    case 2: 
      return "II";
    default: 
      return level; //fallback
  }
}

function extractSdgNumber(sdgText) {
  if (!sdgText || typeof sdgText !== "string") return null;

  // pega primeiro número de 1 a 17
  var match = sdgText.match(/\b(1[0-7]|[1-9])\b/);
  if (!match) return null;

  var n = parseInt(match[1], 10);
  if (n >= 1 && n <= 17) return n;
  return null;
}

function generateCriteriaTable(lista) {
  if (!Array.isArray(lista) || lista.length === 0) {
    return `<p class="text-muted">Nenhum critério definido.</p>`;
  }

  return `
    <div class="table-responsive">
      <table class="table table-bordered table-sm mt-2">
        <thead>
          <tr>
            <th>Critério</th>
            <th>Pontuação</th>
          </tr>
        </thead>
        <tbody>
          ${lista.map(c => `
            <tr>
              <td>${c.criterion ?? "—"}</td>
              <td>${c.points ?? "—"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

// nav
function showSystem() {
  var landing = document.getElementById("landing");
  var system = document.getElementById("system");
  if (landing) landing.style.display = "none";
  if (system) system.style.display = "block";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showLanding() {
  var landing = document.getElementById("landing");
  var system = document.getElementById("system");
  if (system) system.style.display = "none";
  if (landing) landing.style.display = "flex"; 
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function goBackToSetup() {
  selectedGradeGlobal = null;
  selectedModeGlobal = null;

  var container = document.getElementById("card-container");
  if (container) container.innerHTML = "";

  var back = document.getElementById("back-container");
  var reload = document.getElementById("reload-container");
  var setup = document.getElementById("setup-container");

  if (back) back.style.display = "none";
  if (reload) reload.style.display = "none";
  if (setup) setup.style.display = "block";

  // reset radios + botão
  document.querySelectorAll('input[name="gradeLevel"]').forEach(r => r.checked = false);
  document.querySelectorAll('input[name="evalMode"]').forEach(r => r.checked = false);

  var btnDraw = document.getElementById("btn-draw-card");
  if (btnDraw) btnDraw.disabled = true;
}

function reloadCard() {
  if (selectedGradeGlobal && selectedModeGlobal) {
    loadCard(selectedGradeGlobal, selectedModeGlobal);
  }
}

function toggleEvaluationView() {
  evaluationViewOpen = !evaluationViewOpen;

  var aluno = document.querySelector(".aluno-view");
  var mediador = document.querySelector(".mediator-view");

  if (aluno) aluno.style.display = evaluationViewOpen ? "none" : "block";
  if (mediador) mediador.style.display = evaluationViewOpen ? "block" : "none";
}


// load card
function loadCard(selectedGrade, selectedMode) {
  var container = document.getElementById("card-container");
  if (!container) return;

  selectedGradeGlobal = selectedGrade;
  selectedModeGlobal = selectedMode;

  // esconder setup e mostrar navegação
  var setup = document.getElementById("setup-container");
  var back = document.getElementById("back-container");
  var reload = document.getElementById("reload-container");
  if (setup) setup.style.display = "none";
  if (back) back.style.display = "block";
  if (reload) reload.style.display = "block";

  container.innerHTML = `<p class="text-muted">Carregando carta...</p>`;

  db.collection("actionCards")
    .where("level", "==", selectedGrade)
    .get()
    .then((querySnapshot) => {
      if (querySnapshot.empty) {
        container.innerHTML = `<p class="text-muted">Nenhuma carta encontrada para este nível.</p>`;
        return;
      }

      var docs = querySnapshot.docs;

      // modo avaliação:
      // com critério => precisa ter mediator (e idealmente critérios)
      // sem critério => NÃO filtra; só oculta o "Como avaliar"
      if (selectedMode === "withCriteria") {
        docs = docs.filter(doc => {
          const d = doc.data();
          // considera mediator válido se existir e tiver evaluationCriteria com algum item
          return !!(d.mediator && Array.isArray(d.mediator.evaluationCriteria) && d.mediator.evaluationCriteria.length > 0);
        });
      } else {
        // sem critério => mantém todas as cartas
      }

      if (!docs || docs.length === 0) {
        container.innerHTML = `<p class="text-muted">Nenhuma carta encontrada para este modo de avaliação.</p>`;
        return;
      }

      var randomDoc = docs[Math.floor(Math.random() * docs.length)];
      var data = randomDoc.data();

      var levelRoman = formatLevel(data.level);
      var hasMediator = !!data.mediator;
      var showEvaluation = (selectedMode === "withCriteria") && hasMediator;

      var criterios = hasMediator ? (data.mediator.evaluationCriteria || []) : [];
      var tabelaCriterios = hasMediator ? generateCriteriaTable(criterios) : "";

      // ODS
      var sdgText = data.sdg || "ODS —";
      var sdgNum = extractSdgNumber(sdgText);
      var headerColor = sdgNum ? (ODS_COLORS[sdgNum] || "#2a2c39") : "#2a2c39";
      var odsIconPath = sdgNum ? `img/ods${sdgNum}.png` : null;

      container.innerHTML = `
        <div class="action-card">
          <div class="action-card__header" style="background:${headerColor}">
            <h4 class="action-card__sdg-title">${sdgText}</h4>
            ${odsIconPath ? `<img class="action-card__ods-icon" src="${odsIconPath}" alt="ODS ${sdgNum}">` : ``}
          </div>

          <div class="action-card__content">
            <div class="aluno-view">
              <p><strong>Desafio:</strong><br>${data.challengeDescription || "—"}</p>

              ${data.hint
                ? `<p><strong>Dica:</strong><br>Seu prompt deve conter: ${data.hint}</p>`
                : ``}

              ${showEvaluation ? `<button class="action-card__btn" onclick="toggleEvaluationView()" style="margin-top:6px;">
                Como avaliar
              </button>` : ``}

            </div>

            ${showEvaluation ? `
              <div class="mediator-view" style="display:none;">
                <button class="action-card__btn secondary" onclick="toggleEvaluationView()" style="margin-bottom:10px;">
                  Voltar
                </button>

                <p><strong>Desafio:</strong><br>${data.challengeDescription || "—"}</p>

                ${data.mediator?.suggestedCommand
                  ? `<p><strong>Comando sugerido:</strong><br>${data.mediator.suggestedCommand}</p>`
                  : ``}

                ${data.mediator?.expectedOutput
                  ? `<p><strong>Saída esperada:</strong><br>${data.mediator.expectedOutput}</p>`
                  : ``}

                <p class="mb-1"><strong>Critérios de avaliação:</strong></p>
                ${tabelaCriterios}
              </div>
            ` : ``}
          </div>

          <div class="action-card__footer">
            <span class="level-badge">
              <i class="bi bi-mortarboard"></i> Nível ${levelRoman}
            </span>

            <span class="brand-mark">
              <img src="img/Logo_ConsCiencIA.png" alt="ConsCiêncIA">
            </span>
          </div>
        </div>
      `;
    })
    .catch((error) => {
      console.error("Erro ao buscar carta:", error);
      container.innerHTML = `<p class="text-danger">Erro ao carregar a carta.</p>`;
    });
}

// Boot: listeners
document.addEventListener("DOMContentLoaded", function () {
  // Landing -> sistema
  var btnOpen = document.getElementById("btn-open-system");
  if (btnOpen) {
    btnOpen.addEventListener("click", showSystem);
  }

  // habilitar botão sortear só quando nível + modo selecionados
  function refreshDrawButtonState() {
  var grade = document.querySelector('input[name="gradeLevel"]:checked');
  var mode = document.querySelector('input[name="evalMode"]:checked');
  var btnDraw = document.getElementById("btn-draw-card");
  if (!btnDraw) return;

  btnDraw.disabled = !(grade && mode);
}

  document.querySelectorAll('input[name="gradeLevel"]').forEach(r => {
    r.addEventListener("change", refreshDrawButtonState);
  });

  document.querySelectorAll('input[name="evalMode"]').forEach(r => {
    r.addEventListener("change", refreshDrawButtonState);
  });

  // Sortear
var btnDraw = document.getElementById("btn-draw-card");
if (btnDraw) {
  btnDraw.addEventListener("click", function () {
    var grade = document.querySelector('input[name="gradeLevel"]:checked');
    var mode = document.querySelector('input[name="evalMode"]:checked');
    if (!grade || !mode) return;

    selectedGradeGlobal = parseInt(grade.value, 10);
    selectedModeGlobal = mode.value; // com critério | wsem critério

    loadCard(selectedGradeGlobal, selectedModeGlobal);
  });
}
});