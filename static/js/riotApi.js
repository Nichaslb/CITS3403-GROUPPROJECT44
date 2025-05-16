// =================== Global Variables ===================
let rankInfo = null;
let matchList = [];

// User PUUID can be obtained from server or stored in user profile
// Here we still use a static value as an example
const puuid = "pD5CBI55v1gVhok8UzWzabRjgfF0fmVLmYUTc07OGemfBQAKxmy5GmygJmTbPhtXTKxI-aObyPkgYg";

// =================== 获取用户资料 ===================
async function fetchUserProfile() {
    try {
        const response = await fetch('/api/user_profile');
        if (!response.ok) {
            throw new Error(`Failed to obtain user data：${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === "success") {
            console.log("✅ User data obtained successfully：", result.data);
            
            // If user has no Riot ID and Tagline, able to use
            if (result.data.riot_id && result.data.tagline) {
                // prints the full Riot ID (in Riot’s new format) to the console
                console.log(`User Riot ID: ${result.data.riot_id}#${result.data.tagline}`);
            }
            
            return result.data;
        } else {
            throw new Error(result.message || "Failed to obtain user data");
        }
    } catch (error) {
        console.error("❌ Failed to obtain user data：", error);
        return null;
    }
}

// =================== Rank Information API ===================
async function fetchRankInfo(puuid) {
    try {
        const response = await fetch(`/api/rank/${puuid}`);
        if (!response.ok) {
            throw new Error(`Unable to fetch Rank details：${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === "success") {
            rankInfo = result.data;
            console.log("✅ Rank details successfully loaded!：", rankInfo);
            
            // Update the rank display
            updateRankDisplay(rankInfo);
            
            return rankInfo;
        } else {
            throw new Error(result.message || "Unable to fetch Rank details");
        }
    } catch (error) {
        console.error("❌ Unable to fetch Rank details", error);
        // Display error message
        document.getElementById("rank-name").innerText = "Unaable to fetch Rank details"
        return null;
    }
}

// =================== Fetch the Match ID from API ===================
async function fetchMatchList(puuid, count = 20) {
    try {
        const response = await fetch(`/api/matches/${puuid}?count=${count}`);
        if (!response.ok) {
            throw new Error(`Unable to fetch Match ID：${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === "success") {
            matchList = result.data;
            console.log(`✅ Successfully obtained ${matchList.length} Match ID：`, matchList);
            
            // If needed, get individual match details
            if (matchList.length > 0) {
                // Obtain the latest match details
                fetchMatchDetails(matchList[0]);
            }
            
            return matchList;
        } else {
            throw new Error(result.message || "Unable to fetch Match ID");
        }
    } catch (error) {
        console.error("❌ Unable to fetch Match ID：", error);
        return null;
    }
}

// =================== Obtaining single match IDs from the API ===================
async function fetchMatchDetails(matchId) {
    try {
        const response = await fetch(`/api/match/${matchId}`);
        if (!response.ok) {
            throw new Error(`Unable to fetch Match ID：${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === "success") {
            const matchDetails = result.data;
            console.log("✅ Successfully obtained match results：", matchDetails);
            
            // Process and display match details
            displayMatchDetails(matchDetails, puuid);
            
            return matchDetails;
        } else {
            throw new Error(result.message || "Unable to obtain match results");
        }
    } catch (error) {
        console.error("❌ Unable to obtain match results", error);
        return null;
    }
}

// =================== Additional function to display data ===================

// Update the rank display
function updateRankDisplay(rankData) {
    // update the display based on the rank data
    if (rankData && rankData.length > 0) {
        // Rank Teir (RANKED_SOLO_5x5)
        const soloRank = rankData.find(queue => queue.queueType === "RANKED_SOLO_5x5");
        
        if (soloRank) {
            // Update rank name and image
            const rankName = `${soloRank.tier} ${soloRank.rank}`;
            document.getElementById("rank-name").innerText = rankName;
            
            // Updated rank name and image (assuming you have corresponding image))
            const rankImg = document.getElementById("rank-img");
            if (rankImg) {
                rankImg.src = `../assets/dashboard/ranks/Season_2023_-_${soloRank.tier}.webp`;
                rankImg.alt = rankName;
            }
            
            // Update rank statistics
            document.getElementById("win-rate").innerText = calculateWinRate(soloRank.wins, soloRank.losses) + "%";
            document.getElementById("games-played").innerText = soloRank.wins + soloRank.losses;
            document.getElementById("league-points").innerText = soloRank.leaguePoints + " LP";
        } else {
            // No rank data found
            document.getElementById("rank-name").innerText = "No rating";
        }
    } else {
        // No rank data found
        document.getElementById("rank-name").innerText = "No rating";
    }
}

// Calculate the win rate
function calculateWinRate(wins, losses) {
    const total = wins + losses;
    if (total === 0) return 0;
    return Math.round((wins / total) * 100);
}

// Show match details
function displayMatchDetails(matchData, playerPuuid) {
    // Get the match list container
    const container = document.querySelector(".match-list-container");
    if (!container) return;
    
    // Loading
    const loading = container.querySelector(".loading-matches");
    if (loading) loading.remove();
    
    // Extract the player's match details
    const participants = matchData.info.participants;
    const player = participants.find(p => p.puuid === playerPuuid);
    
    // Create a new match item element
    const matchElement = document.createElement("div");
    matchElement.className = "match-item " + (player.win ? "victory" : "defeat");
    
    // Match details such as KDA, champion, game type, etc.
    matchElement.innerHTML = `
        <div class="match-result">${player.win ? "Victory" : "Defeat"}</div>
        <div class="champion-info">
            <img src="../assets/champions/${player.championName.toLowerCase()}.png" alt="${player.championName}">
            <div class="champion-name">${player.championName}</div>
        </div>
        <div class="match-stats">
            <div class="kda">${player.kills}/${player.deaths}/${player.assists}</div>
            <div class="kda-ratio">${calculateKDA(player.kills, player.deaths, player.assists)}</div>
        </div>
        <div class="match-details">
            <div class="game-type">${getQueueType(matchData.info.queueId)}</div>
            <div class="game-duration">${formatDuration(matchData.info.gameDuration)}</div>
            <div class="game-date">${formatDate(matchData.info.gameCreation)}</div>
        </div>
    `;
    
    // Add the match element to the container
    container.appendChild(matchElement);
}

// Calculation of KDA
function calculateKDA(kills, deaths, assists) {
    if (deaths === 0) deaths = 1; // Avoid division by zero
    return ((kills + assists) / deaths).toFixed(2) + " KDA";
}

// Get the game type based on queueId
function getQueueType(queueId) {
    const queueTypes = {
        400: "Normal",
        420: "Ranked",
        430: "Unlimited Firepower",
        440: "Flex Queue",
        450: "Rumble",
        // Add more game modes...
    };
    return queueTypes[queueId] || "Other game modes";
}

// Game duration formatting
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}minutes${secs}seconds`;
}

// Date formatting
function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString("zh-CN");
}

// =================== Initialization call ===================
window.onload = async function () {
    // Obtain user information
    const userProfile = await fetchUserProfile();
    
    // Rank and match information
    await fetchRankInfo(puuid);
    await fetchMatchList(puuid, 10); // As a defualt, 10 matches obtained
};