document.addEventListener('DOMContentLoaded', function() {
    fetchRiotIdInfo();
    fetchGameModeStats();

    document.getElementById('analyze-button').addEventListener('click', function() {
        analyzeMatches();
    });

    const retryBtn = document.getElementById('retry-button');
    if (retryBtn) retryBtn.addEventListener('click', fetchGameModeStats);

    const quickBtn = document.getElementById('quick-analyze-button');
    if (quickBtn) quickBtn.addEventListener('click', showAnalyzeConfirmModal);

    const cancelBtn = document.getElementById('cancel-analyze-button');
    if (cancelBtn) cancelBtn.addEventListener('click', () => {
        document.getElementById('analyze-confirm-modal').style.display = 'none';
    });

    const confirmBtn = document.getElementById('confirm-analyze-button');
    if (confirmBtn) confirmBtn.addEventListener('click', () => {
        document.getElementById('analyze-confirm-modal').style.display = 'none';
        analyzeMatches();
    });
});

function fetchRiotIdInfo() {
    fetch('/api/puuid')
        .then(res => res.json())
        .then(data => {
            const el = document.getElementById('riot-id');
            if (data.status === 'success') {
                el.textContent = `${data.data.gameName}#${data.data.tagLine}`;
            } else {
                el.textContent = 'Please set your Riot ID in your profile';
                el.style.color = '#f87171';
            }
        })
        .catch(err => {
            console.error('Error fetching Riot ID:', err);
        });
}

function fetchGameModeStats() {
    document.getElementById('loading-stats').style.display = 'flex';
    document.getElementById('error-stats').style.display = 'none';
    document.getElementById('main-analysis-container').style.display = 'none';
    document.getElementById('fun-stats-container').style.display = 'none';
    document.getElementById('no-matches').style.display = 'none';
    document.getElementById('analyze-button-container').style.display = 'none';

    fetch('/api/game_modes_stats')
        .then(res => res.json())
        .then(data => {
            document.getElementById('loading-stats').style.display = 'none';
            if (data.status === 'success' && data.data.total_matches > 0) {
                displayGameModeStats(data.data);
                if (data.data.detailed_analysis) displayDetailedAnalysis(data.data.detailed_analysis);
                document.getElementById('main-analysis-container').style.display = 'block';
                document.getElementById('fun-stats-container').style.display = 'block';
                if (data.needsUpdate) document.getElementById('analyze-button-container').style.display = 'flex';
            } else if (data.status === 'error') {
                if (data.needsAnalysis) document.getElementById('analyze-button-container').style.display = 'flex';
                else document.getElementById('error-stats').style.display = 'block';
            } else {
                document.getElementById('no-matches').style.display = 'block';
                document.getElementById('analyze-button-container').style.display = 'flex';
            }
        })
        .catch(err => {
            console.error('Error fetching stats:', err);
            document.getElementById('loading-stats').style.display = 'none';
            document.getElementById('error-stats').style.display = 'block';
        });
}

function displayGameModeStats(data) {
    document.getElementById('sr-percentage').textContent = `${data.sr_5v5_percentage}%`;
    document.getElementById('sr-bar').style.width = `${data.sr_5v5_percentage}%`;
    document.getElementById('aram-percentage').textContent = `${data.aram_percentage}%`;
    document.getElementById('aram-bar').style.width = `${data.aram_percentage}%`;
    document.getElementById('fun-percentage').textContent = `${data.fun_modes_percentage}%`;
    document.getElementById('fun-bar').style.width = `${data.fun_modes_percentage}%`;
}


function displayDetailedAnalysis(analysis) {
    const getTopEntry = (obj) => {
        const sorted = Object.entries(obj || {}).sort((a, b) => b[1] - a[1]);
        return sorted.length > 0 ? sorted[0] : null;
    };

    const fc = document.getElementById('favorite-champions-list');
    fc.innerHTML = '';
    const topChampion = getTopEntry(analysis.favorite_champions);
    if (topChampion) {
        const [champ, count] = topChampion;
        fc.innerHTML = `<div class="data-item"><div class="data-name">${champ}</div><div class="data-value">${count}</div></div>`;
    }

    const fp = document.getElementById('favorite-positions-list');
    fp.innerHTML = '';
    const topPosition = getTopEntry(analysis.favorite_positions);
    if (topPosition) {
        const [pos, count] = topPosition;
        fp.innerHTML = `<div class="data-item"><div class="data-name">${pos}</div><div class="data-value">${count}</div></div>`;
    }

    const ac = document.getElementById('top-ally-champion');
    ac.innerHTML = '';
    const topAlly = getTopEntry(analysis.ally_champions);
    if (topAlly) {
        const [champ, count] = topAlly;
        ac.innerHTML = `<div class="data-item"><div class="data-name">${champ}</div><div class="data-value">${count}</div></div>`;
    }

    const ec = document.getElementById('top-enemy-champion');
    ec.innerHTML = '';
    const topEnemy = getTopEntry(analysis.enemy_champions);
    if (topEnemy) {
        const [champ, count] = topEnemy;
        ec.innerHTML = `<div class="data-item"><div class="data-name">${champ}</div><div class="data-value">${count}</div></div>`;
    }

    document.getElementById('double-kills').textContent = analysis.multikill_stats.doubles;
    document.getElementById('triple-kills').textContent = analysis.multikill_stats.triples;
    document.getElementById('quadra-kills').textContent = analysis.multikill_stats.quadras;
    document.getElementById('penta-kills').textContent = analysis.multikill_stats.pentas;

    const nf = new Intl.NumberFormat();
    const safeFormat = (val) => typeof val === 'number' && !isNaN(val) ? nf.format(val) : '0';

    // 平均数据
    document.getElementById('avg-kda').textContent = safeFormat(analysis.fun_stats.avg_kda);
    document.getElementById('avg-vision').textContent = safeFormat(analysis.fun_stats.avg_vision_score);
    document.getElementById('avg-damage').textContent = safeFormat(analysis.fun_stats.avg_damage_per_match);

    // 总值数据
    document.getElementById('total-gold').textContent = safeFormat(analysis.fun_stats.total_gold_earned);
    document.getElementById('total-damage').textContent = safeFormat(analysis.fun_stats.total_damage_dealt_to_champions);
    document.getElementById('total-damage-taken').textContent = safeFormat(analysis.fun_stats.total_damage_taken);
    document.getElementById('total-items').textContent = safeFormat(analysis.fun_stats.total_items_purchased);
}


function showAnalyzeConfirmModal() {
    fetch('/api/can_analyze')
        .then(res => res.json())
        .then(data => {
            const modal = document.getElementById('analyze-confirm-modal');
            const msg = document.getElementById('modal-message');
            const confirmBtn = document.getElementById('confirm-analyze-button');

            if (data.status === 'success' && data.canAnalyze) {
                modal.style.display = 'block';
                msg.textContent = 'Are you sure you want to analyze? We suggest that you analyze after the match is over';
                confirmBtn.style.display = 'inline-block';
            } else {
                modal.style.display = 'block';
                msg.textContent = data.message || 'Unavailable right now';
                confirmBtn.style.display = 'none';
            }

            window.onclick = function(event) {
                if (event.target == modal) modal.style.display = 'none';
            };
        })
        .catch(err => {
            console.error('Error checking analyze status:', err);
            alert('ERROER: Unable to check analyze status');
        });
}

function analyzeMatches() {
    document.getElementById('loading-stats').style.display = 'flex';
    document.getElementById('error-stats').style.display = 'none';
    document.getElementById('main-analysis-container').style.display = 'none';
    document.getElementById('fun-stats-container').style.display = 'none';
    document.getElementById('no-matches').style.display = 'none';
    document.getElementById('analyze-button-container').style.display = 'none';

    fetch('/api/analyze_game_modes', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' } 
    })
        .then(res => res.json())
        .then((data) => {  
            document.getElementById('loading-stats').style.display = 'none';
            if (data.status === 'success' && data.data.total_matches > 0) {
                displayGameModeStats(data.data);
                if (data.data.detailed_analysis) {
                    displayDetailedAnalysis(data.data.detailed_analysis);
                }
                document.getElementById('main-analysis-container').style.display = 'block';
                document.getElementById('fun-stats-container').style.display = 'block';
            } else {
                document.getElementById('error-stats').style.display = 'block';
            }
        })
        .catch((err) => { 
            console.error('Error analyzing matches:', err);
            document.getElementById('loading-stats').style.display = 'none';
            document.getElementById('error-stats').style.display = 'block';
        });
}
