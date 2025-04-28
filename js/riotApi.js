// =================== 全局配置 ===================
const API_KEY = "RGAPI-2e331ea0-5e3d-43a7-a068-0f008a9001e9";
const puuid = "pD5CBI55v1gVhok8UzWzabRjgfF0fmVLmYUTc07OGemfBQAKxmy5GmygJmTbPhtXTKxI-aObyPkgYg";

// 全局变量保存结果
let rankInfo = null;
let matchList = [];

function getRiotHeaders() {
    return {
        "User-Agent": navigator.userAgent,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": API_KEY
    };
}

// =================== 段位信息 API ===================
async function fetchRankInfo(puuid) {
    const url = `https://oc1.api.riotgames.com/lol/league/v4/entries/by-puuid/${puuid}`;
    try {
        const response = await fetch(url, { headers: getRiotHeaders() });
        if (!response.ok) {
            throw new Error(`段位请求失败：${response.status}`);
        }

        const data = await response.json();
        rankInfo = data;
        console.log("✅ 段位信息获取成功：", rankInfo);

        // 你可以在页面中显示
        document.getElementById("rank-data").innerText = JSON.stringify(rankInfo, null, 2);
    } catch (error) {
        console.error("❌ 获取段位失败：", error);
    }
}

// =================== Match ID 列表 API ===================
async function fetchMatchList(puuid, count = 20) {
    const url = `https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/${puuid}/ids?start=0&count=${count}`;
    try {
        const response = await fetch(url, { headers: getRiotHeaders() });
        if (!response.ok) {
            throw new Error(`比赛ID请求失败：${response.status}`);
        }

        const data = await response.json();
        matchList = data;
        console.log(`✅ 获取 ${data.length} 场 matchId 成功：`, matchList);

        // 同样也可以显示到页面
        document.getElementById("match-data").innerText = JSON.stringify(matchList, null, 2);
    } catch (error) {
        console.error("❌ 获取 matchId 列表失败：", error);
    }
}

// =================== 初始化调用 ===================
window.onload = function () {
    fetchRankInfo(puuid);
    fetchMatchList(puuid, 20); // 默认取20场，之后你也可以换成10/30等
    console.log(rankInfo);
    console.log(matchList);
};
