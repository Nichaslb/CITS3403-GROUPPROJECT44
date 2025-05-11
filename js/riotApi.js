// =================== 全局变量 ===================
let rankInfo = null;
let matchList = [];

// 用户的PUUID - 可以从服务器获取或存储在用户资料中
// 这里我们还是使用静态值作为示例
const puuid = "pD5CBI55v1gVhok8UzWzabRjgfF0fmVLmYUTc07OGemfBQAKxmy5GmygJmTbPhtXTKxI-aObyPkgYg";

// =================== 获取用户资料 ===================
async function fetchUserProfile() {
    try {
        const response = await fetch('/api/user_profile');
        if (!response.ok) {
            throw new Error(`获取用户资料失败：${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === "success") {
            console.log("✅ 用户资料获取成功：", result.data);
            
            // 如果用户设置了Riot ID和Tagline，可以使用
            if (result.data.riot_id && result.data.tagline) {
                // 使用用户设置的信息进行后续操作
                console.log(`用户Riot ID: ${result.data.riot_id}#${result.data.tagline}`);
            }
            
            return result.data;
        } else {
            throw new Error(result.message || "获取用户资料失败");
        }
    } catch (error) {
        console.error("❌ 获取用户资料失败：", error);
        return null;
    }
}

// =================== 段位信息 API ===================
async function fetchRankInfo(puuid) {
    try {
        const response = await fetch(`/api/rank/${puuid}`);
        if (!response.ok) {
            throw new Error(`段位请求失败：${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === "success") {
            rankInfo = result.data;
            console.log("✅ 段位信息获取成功：", rankInfo);
            
            // 更新段位显示
            updateRankDisplay(rankInfo);
            
            return rankInfo;
        } else {
            throw new Error(result.message || "段位请求失败");
        }
    } catch (error) {
        console.error("❌ 获取段位失败：", error);
        // 显示错误信息
        document.getElementById("rank-name").innerText = "无法获取段位";
        return null;
    }
}

// =================== Match ID 列表 API ===================
async function fetchMatchList(puuid, count = 20) {
    try {
        const response = await fetch(`/api/matches/${puuid}?count=${count}`);
        if (!response.ok) {
            throw new Error(`比赛ID请求失败：${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === "success") {
            matchList = result.data;
            console.log(`✅ 获取 ${matchList.length} 场 matchId 成功：`, matchList);
            
            // 如果需要，获取单场比赛详情
            if (matchList.length > 0) {
                // 获取最近一场比赛详情
                fetchMatchDetails(matchList[0]);
            }
            
            return matchList;
        } else {
            throw new Error(result.message || "比赛ID请求失败");
        }
    } catch (error) {
        console.error("❌ 获取 matchId 列表失败：", error);
        return null;
    }
}

// =================== 单场比赛详情 API ===================
async function fetchMatchDetails(matchId) {
    try {
        const response = await fetch(`/api/match/${matchId}`);
        if (!response.ok) {
            throw new Error(`比赛详情请求失败：${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === "success") {
            const matchDetails = result.data;
            console.log("✅ 比赛详情获取成功：", matchDetails);
            
            // 处理并显示比赛详情
            displayMatchDetails(matchDetails, puuid);
            
            return matchDetails;
        } else {
            throw new Error(result.message || "比赛详情请求失败");
        }
    } catch (error) {
        console.error("❌ 获取比赛详情失败：", error);
        return null;
    }
}

// =================== 显示数据的辅助函数 ===================

// 更新段位显示
function updateRankDisplay(rankData) {
    // 根据段位数据更新页面显示
    if (rankData && rankData.length > 0) {
        // 查找排位赛段位 (RANKED_SOLO_5x5)
        const soloRank = rankData.find(queue => queue.queueType === "RANKED_SOLO_5x5");
        
        if (soloRank) {
            // 更新段位图标和名称
            const rankName = `${soloRank.tier} ${soloRank.rank}`;
            document.getElementById("rank-name").innerText = rankName;
            
            // 更新段位图标 (假设您有对应的图片)
            const rankImg = document.getElementById("rank-img");
            if (rankImg) {
                rankImg.src = `../assets/dashboard/ranks/Season_2023_-_${soloRank.tier}.webp`;
                rankImg.alt = rankName;
            }
            
            // 更新其他统计信息
            document.getElementById("win-rate").innerText = calculateWinRate(soloRank.wins, soloRank.losses) + "%";
            document.getElementById("games-played").innerText = soloRank.wins + soloRank.losses;
            document.getElementById("league-points").innerText = soloRank.leaguePoints + " LP";
        } else {
            // 未找到排位赛数据
            document.getElementById("rank-name").innerText = "未定级";
        }
    } else {
        // 无段位数据
        document.getElementById("rank-name").innerText = "未定级";
    }
}

// 计算胜率
function calculateWinRate(wins, losses) {
    const total = wins + losses;
    if (total === 0) return 0;
    return Math.round((wins / total) * 100);
}

// 显示比赛详情
function displayMatchDetails(matchData, playerPuuid) {
    // 获取比赛容器
    const container = document.querySelector(".match-list-container");
    if (!container) return;
    
    // 清除加载动画
    const loading = container.querySelector(".loading-matches");
    if (loading) loading.remove();
    
    // 提取玩家的比赛数据
    const participants = matchData.info.participants;
    const player = participants.find(p => p.puuid === playerPuuid);
    
    // 创建比赛元素
    const matchElement = document.createElement("div");
    matchElement.className = "match-item " + (player.win ? "victory" : "defeat");
    
    // 填充比赛信息
    matchElement.innerHTML = `
        <div class="match-result">${player.win ? "胜利" : "失败"}</div>
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
    
    // 添加到容器
    container.appendChild(matchElement);
}

// KDA计算
function calculateKDA(kills, deaths, assists) {
    if (deaths === 0) deaths = 1; // 避免除以零
    return ((kills + assists) / deaths).toFixed(2) + " KDA";
}

// 获取游戏模式
function getQueueType(queueId) {
    const queueTypes = {
        400: "普通",
        420: "排位赛",
        430: "无限火力",
        440: "灵活排位",
        450: "极地大乱斗",
        // 添加更多游戏模式...
    };
    return queueTypes[queueId] || "其他模式";
}

// 格式化游戏时长
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}分${secs}秒`;
}

// 格式化日期
function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString("zh-CN");
}

// =================== 初始化调用 ===================
window.onload = async function () {
    // 首先获取用户资料
    const userProfile = await fetchUserProfile();
    
    // 然后获取段位和比赛信息
    await fetchRankInfo(puuid);
    await fetchMatchList(puuid, 10); // 默认获取10场比赛
};