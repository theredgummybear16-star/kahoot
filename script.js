const games = [
  {
    id: '654321',
    title: 'Biology Review',
    currentQuestion: 7,
    totalQuestions: 15,
    questionTitle: 'Which organelle is known as the powerhouse of the cell?',
    answers: [
      { label: 'Nucleus', count: 4 },
      { label: 'Mitochondria', count: 19 },
      { label: 'Ribosome', count: 2 },
      { label: 'Golgi apparatus', count: 1 },
    ],
    players: [
      { id: 'p1', name: 'QuizQueen', score: 12450 },
      { id: 'p2', name: 'TrollSlayer', score: 11700 },
      { id: 'p3', name: 'BananaFan99', score: 10850 },
    ],
  },
  {
    id: '778899',
    title: 'World Capitals',
    currentQuestion: 4,
    totalQuestions: 10,
    questionTitle: 'What is the capital city of Canada?',
    answers: [
      { label: 'Toronto', count: 6 },
      { label: 'Montreal', count: 2 },
      { label: 'Ottawa', count: 15 },
      { label: 'Vancouver', count: 3 },
    ],
    players: [
      { id: 'p4', name: 'NorthStar', score: 8450 },
      { id: 'p5', name: 'MapMaster', score: 8300 },
      { id: 'p6', name: 'SneakyFox', score: 7900 },
    ],
  },
  {
    id: '880011',
    title: 'Math Warmup',
    currentQuestion: 2,
    totalQuestions: 12,
    questionTitle: 'Solve: 9 × 7 = ?',
    answers: [
      { label: '54', count: 2 },
      { label: '63', count: 21 },
      { label: '72', count: 1 },
      { label: '56', count: 0 },
    ],
    players: [
      { id: 'p7', name: 'FractionHero', score: 3450 },
      { id: 'p8', name: 'DeltaWave', score: 2900 },
      { id: 'p9', name: 'TornadoKid', score: 2600 },
    ],
  },
];

const blockedWords = ['troll', 'hack', 'badword'];
const activityLog = [
  'Game 654321 started by host Ms. Rivera.',
  'Blocked username "troll_123" from joining lobby 778899.',
  'Live spy mode attached to game 880011.',
];

const els = {
  activeGames: document.querySelector('#active-games-count'),
  playersOnline: document.querySelector('#players-online-count'),
  blockedCount: document.querySelector('#blocked-count'),
  skipGameSelect: document.querySelector('#skip-game-select'),
  skipGameStatus: document.querySelector('#skip-game-status'),
  forceSkipButton: document.querySelector('#force-skip-button'),
  scoreGameSelect: document.querySelector('#score-game-select'),
  scorePlayerSelect: document.querySelector('#score-player-select'),
  scoreDeltaInput: document.querySelector('#score-delta-input'),
  scoreReasonInput: document.querySelector('#score-reason-input'),
  scoreAdjustButton: document.querySelector('#score-adjust-button'),
  spyGameSelect: document.querySelector('#spy-game-select'),
  spyQuestionTitle: document.querySelector('#spy-question-title'),
  spyQuestionMeta: document.querySelector('#spy-question-meta'),
  spyAnswerList: document.querySelector('#spy-answer-list'),
  wordFilterInput: document.querySelector('#word-filter-input'),
  wordFilterAdd: document.querySelector('#word-filter-add'),
  wordFilterList: document.querySelector('#word-filter-list'),
  renameGameSelect: document.querySelector('#rename-game-select'),
  renamePlayerSelect: document.querySelector('#rename-player-select'),
  renameInput: document.querySelector('#rename-input'),
  renameButton: document.querySelector('#rename-button'),
  fakeGameSelect: document.querySelector('#fake-game-select'),
  fakePlayerSelect: document.querySelector('#fake-player-select'),
  fakeMessageInput: document.querySelector('#fake-message-input'),
  fakeResultButton: document.querySelector('#fake-result-button'),
  activityLog: document.querySelector('#activity-log'),
  clearLogButton: document.querySelector('#clear-log-button'),
};

function gameById(id) {
  return games.find((game) => game.id === id);
}

function addLogEntry(message) {
  const stamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  activityLog.unshift(`${stamp} — ${message}`);
  renderLog();
}

function populateGameSelect(select) {
  select.innerHTML = games
    .map((game) => `<option value="${game.id}">${game.id} · ${game.title}</option>`)
    .join('');
}

function populatePlayerSelect(gameSelect, playerSelect) {
  const game = gameById(gameSelect.value);
  playerSelect.innerHTML = game.players
    .map((player) => `<option value="${player.id}">${player.name} · ${player.score} pts</option>`)
    .join('');
}

function renderStats() {
  const totalPlayers = games.reduce((sum, game) => sum + game.players.length, 0);
  els.activeGames.textContent = String(games.length);
  els.playersOnline.textContent = String(totalPlayers);
  els.blockedCount.textContent = String(blockedWords.length);
}

function renderSkipStatus() {
  const game = gameById(els.skipGameSelect.value);
  els.skipGameStatus.textContent = `${game.title} is currently on question ${game.currentQuestion} of ${game.totalQuestions}.`;
}

function renderSpyPanel() {
  const game = gameById(els.spyGameSelect.value);
  const totalAnswers = game.answers.reduce((sum, answer) => sum + answer.count, 0) || 1;

  els.spyQuestionTitle.textContent = game.questionTitle;
  els.spyQuestionMeta.textContent = `Lobby ${game.id} · Question ${game.currentQuestion}/${game.totalQuestions} · ${totalAnswers} live responses captured`;
  els.spyAnswerList.innerHTML = game.answers
    .map((answer) => {
      const percent = Math.round((answer.count / totalAnswers) * 100);
      return `
        <div class="answer-row">
          <div>
            <strong>${answer.label}</strong>
            <progress max="100" value="${percent}"></progress>
          </div>
          <span>${answer.count} votes · ${percent}%</span>
        </div>
      `;
    })
    .join('');
}

function renderWordFilter() {
  els.wordFilterList.innerHTML = blockedWords
    .map(
      (word) => `
        <span class="chip">
          ${word}
          <button type="button" data-word="${word}">×</button>
        </span>
      `,
    )
    .join('');
}

function renderLog() {
  els.activityLog.innerHTML = activityLog.map((entry) => `<li>${entry}</li>`).join('');
}

function initialize() {
  [
    els.skipGameSelect,
    els.scoreGameSelect,
    els.spyGameSelect,
    els.renameGameSelect,
    els.fakeGameSelect,
  ].forEach(populateGameSelect);

  populatePlayerSelect(els.scoreGameSelect, els.scorePlayerSelect);
  populatePlayerSelect(els.renameGameSelect, els.renamePlayerSelect);
  populatePlayerSelect(els.fakeGameSelect, els.fakePlayerSelect);

  renderStats();
  renderSkipStatus();
  renderSpyPanel();
  renderWordFilter();
  renderLog();
}

els.skipGameSelect.addEventListener('change', renderSkipStatus);
els.spyGameSelect.addEventListener('change', () => {
  renderSpyPanel();
  addLogEntry(`Live spy mode switched to lobby ${els.spyGameSelect.value}.`);
});

els.scoreGameSelect.addEventListener('change', () => populatePlayerSelect(els.scoreGameSelect, els.scorePlayerSelect));
els.renameGameSelect.addEventListener('change', () => populatePlayerSelect(els.renameGameSelect, els.renamePlayerSelect));
els.fakeGameSelect.addEventListener('change', () => populatePlayerSelect(els.fakeGameSelect, els.fakePlayerSelect));

els.forceSkipButton.addEventListener('click', () => {
  const game = gameById(els.skipGameSelect.value);
  game.currentQuestion = Math.min(game.currentQuestion + 1, game.totalQuestions);
  renderSkipStatus();
  if (els.spyGameSelect.value === game.id) renderSpyPanel();
  addLogEntry(`Force skipped lobby ${game.id} to results for question ${game.currentQuestion}.`);
});

els.scoreAdjustButton.addEventListener('click', () => {
  const game = gameById(els.scoreGameSelect.value);
  const player = game.players.find(({ id }) => id === els.scorePlayerSelect.value);
  const delta = Number(els.scoreDeltaInput.value || 0);
  const reason = els.scoreReasonInput.value.trim() || 'No reason provided';
  player.score += delta;
  populatePlayerSelect(els.scoreGameSelect, els.scorePlayerSelect);
  addLogEntry(`Adjusted ${player.name} in lobby ${game.id} by ${delta} points. Reason: ${reason}.`);
});

els.wordFilterAdd.addEventListener('click', () => {
  const word = els.wordFilterInput.value.trim().toLowerCase();
  if (!word || blockedWords.includes(word)) return;
  blockedWords.push(word);
  els.wordFilterInput.value = '';
  renderWordFilter();
  renderStats();
  addLogEntry(`Added "${word}" to the username word filter.`);
});

els.wordFilterList.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-word]');
  if (!button) return;
  const word = button.dataset.word;
  const index = blockedWords.indexOf(word);
  if (index === -1) return;
  blockedWords.splice(index, 1);
  renderWordFilter();
  renderStats();
  addLogEntry(`Removed "${word}" from the username word filter.`);
});

els.renameButton.addEventListener('click', () => {
  const game = gameById(els.renameGameSelect.value);
  const player = game.players.find(({ id }) => id === els.renamePlayerSelect.value);
  const newName = els.renameInput.value.trim();
  if (!newName) return;
  const oldName = player.name;
  player.name = newName;
  populatePlayerSelect(els.renameGameSelect, els.renamePlayerSelect);
  populatePlayerSelect(els.scoreGameSelect, els.scorePlayerSelect);
  populatePlayerSelect(els.fakeGameSelect, els.fakePlayerSelect);
  els.renameInput.value = '';
  addLogEntry(`Renamed ${oldName} to ${newName} in lobby ${game.id}.`);
});

els.fakeResultButton.addEventListener('click', () => {
  const game = gameById(els.fakeGameSelect.value);
  const player = game.players.find(({ id }) => id === els.fakePlayerSelect.value);
  const message = els.fakeMessageInput.value.trim() || 'WRONG';
  addLogEntry(`Sent fake result overlay to ${player.name} in lobby ${game.id}: ${message}`);
});

els.clearLogButton.addEventListener('click', () => {
  activityLog.length = 0;
  renderLog();
});

initialize();
