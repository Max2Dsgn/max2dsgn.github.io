const images = [
  "images/img1.jpg",
  "images/img2.jpg",
  "images/img3.jpg",
  "images/img4.jpg",
  "images/img5.jpg",
  "images/img6.jpg",
  "images/img7.jpg",
  "images/img8.jpg",
  "images/img9.jpg",
  "images/img10.jpg"
];

let ratings = {};
let showCounts = {};
let comparisons = new Set();
let currentPair = [];
let totalRounds = 30;
let round = 0;
const K = 32;
let votingLocked = false;
let lastShown = [];

const imgA = document.getElementById("imgA");
const imgB = document.getElementById("imgB");
const progress = document.getElementById("progress");
const resultsDiv = document.getElementById("results");
const endBtn = document.getElementById("endBtn");
const canvas = document.getElementById("ratingChart");
const ctx = canvas.getContext("2d");

// Инициализация рейтингов и счётчиков показов
images.forEach(img => {
  ratings[img] = 1000;
  showCounts[img] = 0;
});

// Подсчёт ожидаемого результата (Эло)
function expectedScore(rA, rB) {
  return 1 / (1 + Math.pow(10, (rB - rA) / 400));
}

// Обновление рейтингов по системе Эло
function updateElo(winner, loser) {
  const rW = ratings[winner];
  const rL = ratings[loser];

  const expectedW = expectedScore(rW, rL);
  const expectedL = expectedScore(rL, rW);

  ratings[winner] = rW + K * (1 - expectedW);
  ratings[loser] = rL + K * (0 - expectedL);
}

// Взвешенный случайный выбор пары изображений без повторения последних показанных
function getWeightedPair() {
  const weights = images.map(img => {
    const count = showCounts[img] || 0;
    return { img, weight: 1 / (count + 1) }; // реже показывался → выше вес
  });

  function weightedRandom(exclude = []) {
    const available = weights.filter(w => !exclude.includes(w.img));
    if (available.length === 0) {
      // Если все исключены — выбираем из всех
      return weights[Math.floor(Math.random() * weights.length)].img;
    }

    const totalWeight = available.reduce((sum, w) => sum + w.weight, 0);
    let rnd = Math.random() * totalWeight;

    for (const w of available) {
      if (rnd < w.weight) return w.img;
      rnd -= w.weight;
    }
    return available[available.length - 1].img;
  }

  let a, b;
  let attempts = 0;
  do {
    a = weightedRandom(lastShown);
    b = weightedRandom([...lastShown, a]);
    attempts++;
  } while (
    (a === b ||
      comparisons.has(`${a}|${b}`) ||
      comparisons.has(`${b}|${a}`)) &&
    attempts < 30
  );

  comparisons.add(`${a}|${b}`);
  showCounts[a]++;
  showCounts[b]++;
  lastShown = [a, b];
  return [a, b];
}

// Плавная анимация смены изображений
function fadeOutImages(callback) {
  imgA.classList.add("fade-out");
  imgB.classList.add("fade-out");
  setTimeout(() => {
    callback();
    imgA.classList.remove("fade-out");
    imgB.classList.remove("fade-out");
    imgA.classList.add("fade-in");
    imgB.classList.add("fade-in");
    setTimeout(() => {
      imgA.classList.remove("fade-in");
      imgB.classList.remove("fade-in");
    }, 400);
  }, 300);
}

// Показ следующей пары
function showNextPair() {
  if (
    round >= totalRounds ||
    comparisons.size >= images.length * (images.length - 1)
  ) {
    showResults();
    return;
  }

  currentPair = getWeightedPair();
  fadeOutImages(() => {
    imgA.src = currentPair[0];
    imgB.src = currentPair[1];
    progress.textContent = `Сравнение ${round + 1} из ${totalRounds}`;
  });
}

// Извлечение имени файла (для сравнения путей)
function getFilename(path) {
  return path.split("/").pop();
}

// Обработка выбора пользователя
function registerVote(winnerImg) {
  if (votingLocked) return;
  votingLocked = true;

  const [img1, img2] = currentPair;
  const loserImg = winnerImg === img1 ? img2 : img1;

  const winnerEl =
    getFilename(winnerImg) === getFilename(imgA.src) ? imgA : imgB;
  const loserEl = winnerEl === imgA ? imgB : imgA;

  winnerEl.classList.add("selected");
  loserEl.classList.add("loser");

  setTimeout(() => {
    updateElo(winnerImg, loserImg);
    round++;
    winnerEl.classList.remove("selected");
    loserEl.classList.remove("loser");
    showNextPair();
    votingLocked = false;
  }, 600);
}

// Обработчики кликов
imgA.addEventListener("click", () => registerVote(currentPair[0]));
imgB.addEventListener("click", () => registerVote(currentPair[1]));
endBtn.addEventListener("click", showResults);

// Показ финального рейтинга и гистограммы
function showResults() {
  document.getElementById("comparison-container").classList.add("hidden");
  progress.classList.add("hidden");
  endBtn.classList.add("hidden");

  const sorted = Object.entries(ratings).sort((a, b) => b[1] - a[1]);
  let html =
    "<h2>Результаты (рейтинги Эло)</h2><table><tr><th>Изображение</th><th>Рейтинг</th></tr>";
  sorted.forEach(([img, rating]) => {
    html += `<tr><td><img src="${img}" style="max-width:50px; max-height:50px;" /></td><td>${Math.round(
      rating
    )}</td></tr>`;
  });
  html += "</table>";
  resultsDiv.innerHTML = html;
  resultsDiv.classList.remove("hidden");

  drawHistogram(sorted);
}

// Рисование гистограммы рейтингов на canvas
function drawHistogram(ratingsData) {
  const canvas = document.getElementById("ratingChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  canvas.classList.remove("hidden");

  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const barColor = isDark ? "#90caf9" : "#4a90e2";
  const textColor = isDark ? "#e0e0e0" : "#333";
  const axisColor = isDark ? "#666" : "#ccc";

  const dpr = window.devicePixelRatio || 1;
  const logicalWidth = canvas.offsetWidth;
  const logicalHeight = 400;

  canvas.width = logicalWidth * dpr;
  canvas.height = logicalHeight * dpr;
  canvas.style.width = logicalWidth + "px";
  canvas.style.height = logicalHeight + "px";

  ctx.setTransform(1, 0, 0, 1, 0, 0); // сброс transform
  ctx.scale(dpr, dpr); // масштабируем на DPR

  const padding = 50;
  const width = logicalWidth;
  const height = logicalHeight;

  ctx.clearRect(0, 0, width, height);

  const barWidth = (width - padding * 2) / ratingsData.length * 0.7;
  const maxRating = Math.max(...ratingsData.map(r => r[1]));

  // Ось Y
  ctx.strokeStyle = axisColor;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding / 2);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding / 2, height - padding);
  ctx.stroke();

  ctx.font = "12px sans-serif";
  ctx.textAlign = "center";

  ratingsData.forEach(([img, rating], i) => {
    const barHeight = ((rating / maxRating) * (height - padding * 2));
    const x = padding + i * ((width - padding * 2) / ratingsData.length) + barWidth / 2;
    const y = height - padding - barHeight;

    // Бар
    ctx.fillStyle = barColor;
    ctx.fillRect(x, y, barWidth, barHeight);

    // Подпись
    const imgName = img.split("/").pop();
    ctx.fillStyle = textColor;
    ctx.fillText(imgName, x + barWidth / 2, height - padding + 15);

    // Значение
    ctx.fillText(Math.round(rating), x + barWidth / 2, y - 5);
  });
}



// Запуск
showNextPair();
