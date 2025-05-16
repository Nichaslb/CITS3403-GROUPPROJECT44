// js/stats.js
document.addEventListener('DOMContentLoaded', function() {
    // Get RiotID
    fetchRiotIdInfo();
    
    // Get game mode statistics
    fetchGameModeStats();
    
    // Analyse button event listener
    document.getElementById('analyze-button').addEventListener('click', function() {
        analyzeMatches();
    });
    
    // Rety analyse button event listener
    document.getElementById('retry-button').addEventListener('click', function() {
        fetchGameModeStats();
    });
});

// Get Riot ID information
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

// function to fetch game mode stats
function fetchGameModeStats() {
    // get game mode stats
    document.getElementById('loading-stats').style.display = 'flex';
    document.getElementById('error-stats').style.display = 'none';
    document.getElementById('stats-container').style.display = 'none';
    document.getElementById('no-matches').style.display = 'none';
    document.getElementById('analyze-button-container').style.display = 'none';
    
    fetch('/api/game_modes_stats')
        .then(response => response.json())
        .then(data => {
            // display game mode stats
            document.getElementById('loading-stats').style.display = 'none';
            
            if (data.status === 'success') {
                if (data.data.total_matches > 0) {
                    // display game mode stats
                    displayGameModeStats(data.data);
                    document.getElementById('stats-container').style.display = 'grid';
                    
                    // if data needs update, show analyse button
                    if (data.needsUpdate) {
                        document.getElementById('analyze-button-container').style.display = 'flex';
                    }
                } else {
                    // When there are no matches
                    document.getElementById('no-matches').style.display = 'block';
                    document.getElementById('analyze-button-container').style.display = 'flex';
                }
            } else if (data.status === 'error') {
                if (data.needsAnalysis) {
                    // if data needs analysis, show analyze button
                    document.getElementById('analyze-button-container').style.display = 'flex';
                } else {
                    // error occurred
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

// Display game mode statistics
function displayGameModeStats(data) {
    // Percentage and progress bar
    document.getElementById('sr-percentage').textContent = `${data.sr_5v5_percentage}%`;
    document.getElementById('sr-bar').style.width = `${data.sr_5v5_percentage}%`;
    
    document.getElementById('aram-percentage').textContent = `${data.aram_percentage}%`;
    document.getElementById('aram-bar').style.width = `${data.aram_percentage}%`;
    
    document.getElementById('fun-percentage').textContent = `${data.fun_modes_percentage}%`;
    document.getElementById('fun-bar').style.width = `${data.fun_modes_percentage}%`;
}

// Function to analyze matches
function analyzeMatches() {
    // Display loading status
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
            // Hide loading status
            document.getElementById('loading-stats').style.display = 'none';
            
            if (data.status === 'success') {
                // Dispaly analysis results
                if (data.data.total_matches > 0) {
                    const statsData = {
                        sr_5v5_percentage: data.data.mode_percentages.SR_5v5,
                        aram_percentage: data.data.mode_percentages.ARAM,
                        fun_modes_percentage: data.data.mode_percentages.Fun_Modes
                    };
                    displayGameModeStats(statsData);
                    document.getElementById('stats-container').style.display = 'grid';
                } else {
                    // If no matches are found
                    document.getElementById('no-matches').style.display = 'block';
                }
            } else {
                // Display error message
                document.getElementById('error-stats').style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error analyzing matches:', error);
            document.getElementById('loading-stats').style.display = 'none';
            document.getElementById('error-stats').style.display = 'block';
        });
}