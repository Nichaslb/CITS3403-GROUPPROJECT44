// js/stats.js
document.addEventListener('DOMContentLoaded', function() {
    // 获取Riot ID信息
    fetchRiotIdInfo();
    
    // 尝试获取游戏模式统计数据
    fetchGameModeStats();
    
    // 分析按钮事件监听
    document.getElementById('analyze-button').addEventListener('click', function() {
        analyzeMatches();
    });
    
    // 重试按钮事件监听
    document.getElementById('retry-button').addEventListener('click', function() {
        fetchGameModeStats();
    });
});

// 获取Riot ID信息
function fetchRiotIdInfo() {
    fetch('/api/puuid')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const riotIdElement = document.getElementById('riot-id');
                riotIdElement.textContent = `${data.data.gameName}#${data.data.tagLine}`;
            } else if (data.status === 'error' && data.needsUpdate) {
                const riotIdElement = document.getElementById('riot-id');
                riotIdElement.textContent = 'Please set your Riot ID in your profile';
                riotIdElement.style.color = '#f87171';
            }
        })
        .catch(error => {
            console.error('Error fetching Riot ID:', error);
            const riotIdElement = document.getElementById('riot-id');
            riotIdElement.textContent = 'Could not fetch Riot ID information';
            riotIdElement.style.color = '#f87171';
        });
}

// 获取游戏模式统计数据
function fetchGameModeStats() {
    // 显示加载状态
    document.getElementById('loading-stats').style.display = 'flex';
    document.getElementById('error-stats').style.display = 'none';
    document.getElementById('stats-container').style.display = 'none';
    document.getElementById('no-matches').style.display = 'none';
    document.getElementById('analyze-button-container').style.display = 'none';
    
    fetch('/api/game_modes_stats')
        .then(response => response.json())
        .then(data => {
            // 隐藏加载状态
            document.getElementById('loading-stats').style.display = 'none';
            
            if (data.status === 'success') {
                if (data.data.total_matches > 0) {
                    // 显示统计数据
                    displayGameModeStats(data.data);
                    document.getElementById('stats-container').style.display = 'grid';
                    
                    // 如果数据需要更新，显示分析按钮
                    if (data.needsUpdate) {
                        document.getElementById('analyze-button-container').style.display = 'flex';
                    }
                } else {
                    // 没有比赛记录
                    document.getElementById('no-matches').style.display = 'block';
                    document.getElementById('analyze-button-container').style.display = 'flex';
                }
            } else if (data.status === 'error') {
                if (data.needsAnalysis) {
                    // 需要分析数据
                    document.getElementById('analyze-button-container').style.display = 'flex';
                } else {
                    // 显示错误信息
                    document.getElementById('error-stats').style.display = 'block';
                }
            }
        })
        .catch(error => {
            console.error('Error fetching game mode stats:', error);
            document.getElementById('loading-stats').style.display = 'none';
            document.getElementById('error-stats').style.display = 'block';
        });
}

// 显示游戏模式统计数据
function displayGameModeStats(data) {
    // 设置百分比值和进度条
    document.getElementById('sr-percentage').textContent = `${data.sr_5v5_percentage}%`;
    document.getElementById('sr-bar').style.width = `${data.sr_5v5_percentage}%`;
    
    document.getElementById('aram-percentage').textContent = `${data.aram_percentage}%`;
    document.getElementById('aram-bar').style.width = `${data.aram_percentage}%`;
    
    document.getElementById('fun-percentage').textContent = `${data.fun_modes_percentage}%`;
    document.getElementById('fun-bar').style.width = `${data.fun_modes_percentage}%`;
}

// 触发比赛分析
function analyzeMatches() {
    // 显示加载状态
    document.getElementById('loading-stats').style.display = 'flex';
    document.getElementById('error-stats').style.display = 'none';
    document.getElementById('stats-container').style.display = 'none';
    document.getElementById('no-matches').style.display = 'none';
    document.getElementById('analyze-button-container').style.display = 'none';
    
    fetch('/api/analyze_game_modes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            // 隐藏加载状态
            document.getElementById('loading-stats').style.display = 'none';
            
            if (data.status === 'success') {
                // 显示分析结果
                if (data.data.total_matches > 0) {
                    const statsData = {
                        sr_5v5_percentage: data.data.mode_percentages.SR_5v5,
                        aram_percentage: data.data.mode_percentages.ARAM,
                        fun_modes_percentage: data.data.mode_percentages.Fun_Modes
                    };
                    displayGameModeStats(statsData);
                    document.getElementById('stats-container').style.display = 'grid';
                } else {
                    // 没有比赛记录
                    document.getElementById('no-matches').style.display = 'block';
                }
            } else {
                // 显示错误信息
                document.getElementById('error-stats').style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error analyzing matches:', error);
            document.getElementById('loading-stats').style.display = 'none';
            document.getElementById('error-stats').style.display = 'block';
        });
}