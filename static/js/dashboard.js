/**
 * League of Stats - Dashboard
 * Handles display of player stats and match history
 */

// Configuration
const MATCHES_PER_PAGE = 5; // Number of matches to display per page

// State
let allMatches = []; // Will store all match data
let currentPage = 1; // Current page number

// On document load
document.addEventListener('DOMContentLoaded', function() {
    // Show example matches immediately
    showSampleData();
    
    // Check if rankInfo is available (from riotApi.js)
    // Use a small delay to ensure riotApi.js has time to fetch data
    setTimeout(function() {
        if (window.rankInfo && window.rankInfo.length > 0) {
            updatePlayerCard(window.rankInfo[0]);
        }
    }, 1000);
});

/**
 * Update player card with rank information
 * @param {Object} rankData - Player rank data from API
 */
function updatePlayerCard(rankData) {
    if (!rankData) return;
    
    // Update summoner ID
    document.getElementById('summoner-id').textContent = `Summoner ID: ${rankData.summonerId.substring(0, 8)}...`;
    
    // Update rank name
    const tier = rankData.tier.charAt(0) + rankData.tier.slice(1).toLowerCase();
    document.getElementById('rank-name').textContent = `${tier} ${rankData.rank}`;
    
    // Update rank image
    const rankImg = document.getElementById('rank-img');
    rankImg.src = `assets/ranks/${rankData.tier.toLowerCase()}.png`;
    rankImg.alt = `${tier} ${rankData.rank}`;
    
    // Calculate win rate
    const totalGames = rankData.wins + rankData.losses;
    const winRate = Math.round((rankData.wins / totalGames) * 100);
    
    // Update statistics
    document.getElementById('win-rate').textContent = `${winRate}%`;
    document.getElementById('games-played').textContent = totalGames;
    // KDA is not available in this API response
    document.getElementById('league-points').textContent = `${rankData.leaguePoints} LP`;
    
    // Update welcome message with queue type
    const queueTypes = {
        'RANKED_SOLO_5x5': 'Solo/Duo',
        'RANKED_FLEX_SR': 'Flex 5v5',
        'RANKED_TFT': 'TFT'
    };
    const queueType = queueTypes[rankData.queueType] || rankData.queueType;
    document.getElementById('queue-type').textContent = queueType;
}

/**
 * Show sample match data until real data is loaded
 */
function showSampleData() {
    // Remove the loading indicator
    const loadingElement = document.querySelector('.loading-matches');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
    
    // Sample match data
    const sampleMatches = [
        {
            win: true,
            champion: { name: 'Akali', icon: 'assets/champions/akali.png' },
            kills: 12, deaths: 3, assists: 7,
            cs: 187,
            gameDuration: 1542, // 25:42
            gameId: 'sample1'
        },
        {
            win: false,
            champion: { name: 'Yasuo', icon: 'assets/champions/yasuo.png' },
            kills: 5, deaths: 8, assists: 3,
            cs: 143,
            gameDuration: 1937, // 32:17
            gameId: 'sample2'
        },
        {
            win: true,
            champion: { name: 'Jinx', icon: 'assets/champions/jinx.png' },
            kills: 15, deaths: 4, assists: 9,
            cs: 231,
            gameDuration: 2165, // 36:05
            gameId: 'sample3'
        },
        {
            win: false,
            champion: { name: 'Lee Sin', icon: 'assets/champions/leesin.png' },
            kills: 3, deaths: 6, assists: 11,
            cs: 156,
            gameDuration: 1790, // 29:50
            gameId: 'sample4'
        },
        {
            win: true,
            champion: { name: 'Lux', icon: 'assets/champions/lux.png' },
            kills: 7, deaths: 2, assists: 14,
            cs: 103,
            gameDuration: 1653, // 27:33
            gameId: 'sample5'
        }
    ];
    
    // Load the sample matches
    initializeMatchList(sampleMatches);
}

/**
 * Initialize the match list with data and pagination
 * @param {Array} matchData - Array of match objects from API
 */
function initializeMatchList(matchData) {
    if (!matchData || !Array.isArray(matchData)) {
        console.error("No valid match data provided");
        displayErrorMessage("Could not load match data");
        return;
    }

    // Store the matches
    allMatches = matchData;
    
    // Initial render
    renderMatches();
    renderPagination();
}

/**
 * Render matches for the current page
 */
function renderMatches() {
    const matchListContainer = document.querySelector('.match-list-container');
    if (!matchListContainer) {
        console.error("Match list container not found");
        return;
    }
    
    // Clear previous matches
    matchListContainer.innerHTML = '';
    
    // Calculate which matches to show
    const startIndex = (currentPage - 1) * MATCHES_PER_PAGE;
    const endIndex = Math.min(startIndex + MATCHES_PER_PAGE, allMatches.length);
    const currentMatches = allMatches.slice(startIndex, endIndex);
    
    // If no matches, show message
    if (currentMatches.length === 0) {
        matchListContainer.innerHTML = '<div class="no-matches">No matches found</div>';
        return;
    }
    
    // Create and append match elements
    currentMatches.forEach(match => {
        const matchElement = createMatchElement(match);
        matchListContainer.appendChild(matchElement);
    });
}

/**
 * Create a match element from match data
 * @param {Object} match - Match data object
 * @returns {HTMLElement} - The created match element
 */
function createMatchElement(match) {
    const matchItem = document.createElement('div');
    matchItem.className = `match-item ${match.win ? 'match-win' : 'match-loss'}`;
    
    // Match result
    const resultDiv = document.createElement('div');
    resultDiv.className = 'match-result';
    resultDiv.textContent = match.win ? 'WIN' : 'LOSS';
    matchItem.appendChild(resultDiv);
    
    // Champion info
    const championDiv = document.createElement('div');
    championDiv.className = 'match-champion';
    
    const championIcon = document.createElement('div');
    championIcon.className = 'champion-icon';
    if (match.champion && match.champion.icon) {
        const img = document.createElement('img');
        img.src = match.champion.icon;
        img.alt = match.champion.name;
        championIcon.appendChild(img);
    }
    
    championDiv.appendChild(championIcon);
    const championName = document.createElement('div');
    championName.textContent = match.champion ? match.champion.name : 'Unknown';
    championDiv.appendChild(championName);
    matchItem.appendChild(championDiv);
    
    // Match stats
    const statsDiv = document.createElement('div');
    statsDiv.className = 'match-stats';
    
    const kdaDiv = document.createElement('div');
    kdaDiv.className = 'match-kda';
    kdaDiv.textContent = `${match.kills}/${match.deaths}/${match.assists}`;
    statsDiv.appendChild(kdaDiv);
    
    if (match.cs !== undefined) {
        const csDiv = document.createElement('div');
        csDiv.className = 'match-cs';
        csDiv.textContent = `${match.cs} CS`;
        statsDiv.appendChild(csDiv);
    }
    
    matchItem.appendChild(statsDiv);
    
    // Match time
    const timeDiv = document.createElement('div');
    timeDiv.className = 'match-time';
    timeDiv.textContent = formatMatchDuration(match.gameDuration);
    matchItem.appendChild(timeDiv);
    
    // Add click event to view match details if needed
    matchItem.addEventListener('click', () => {
        console.log(`Match clicked: ${match.gameId}`);
    });
    
    return matchItem;
}

/**
 * Format match duration from seconds to MM:SS
 * @param {number} durationInSeconds - Match duration in seconds
 * @returns {string} - Formatted duration string
 */
function formatMatchDuration(durationInSeconds) {
    if (!durationInSeconds) return '--:--';
    
    const minutes = Math.floor(durationInSeconds / 60);
    const seconds = durationInSeconds % 60;
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

/**
 * Render pagination controls
 */
function renderPagination() {
    const paginationContainer = document.querySelector('.pagination');
    if (!paginationContainer) {
        console.error("Pagination container not found");
        return;
    }
    
    // Clear previous pagination
    paginationContainer.innerHTML = '';
    
    // Calculate total pages
    const totalPages = Math.ceil(allMatches.length / MATCHES_PER_PAGE);
    
    // Don't show pagination if only one page
    if (totalPages <= 1) {
        return;
    }
    
    // Create previous button
    const prevButton = document.createElement('button');
    prevButton.className = 'pagination-button prev';
    prevButton.textContent = 'Previous';
    prevButton.disabled = currentPage === 1;
    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            updatePage();
        }
    });
    paginationContainer.appendChild(prevButton);
    
    // Create page indicators
    // We'll show up to 5 page numbers for simplicity
    const maxVisiblePages = 5;
    const startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    for (let i = startPage; i <= endPage; i++) {
        const pageButton = document.createElement('button');
        pageButton.className = `pagination-button page ${i === currentPage ? 'active' : ''}`;
        pageButton.textContent = i;
        pageButton.addEventListener('click', () => {
            currentPage = i;
            updatePage();
        });
        paginationContainer.appendChild(pageButton);
    }
    
    // Create next button
    const nextButton = document.createElement('button');
    nextButton.className = 'pagination-button next';
    nextButton.textContent = 'Next';
    nextButton.disabled = currentPage === totalPages;
    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            updatePage();
        }
    });
    paginationContainer.appendChild(nextButton);
}

/**
 * Update the page content when changing pages
 */
function updatePage() {
    renderMatches();
    renderPagination();
    
    // Scroll to top of match list for better UX
    const matchList = document.querySelector('.match-list');
    if (matchList) {
        matchList.scrollTop = 0;
    }
}

/**
 * Display error message in the match list
 * @param {string} message - Error message to display
 */
function displayErrorMessage(message) {
    const matchListContainer = document.querySelector('.match-list-container');
    if (matchListContainer) {
        matchListContainer.innerHTML = `<div class="error-message">${message}</div>`;
    }
}