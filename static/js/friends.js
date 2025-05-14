// js/friends.js

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const searchInput = document.getElementById('search-username');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.getElementById('search-results');
    const friendsList = document.getElementById('friends-list');
    
    // 模板
    const searchResultTemplate = document.getElementById('search-result-template');
    const friendItemTemplate = document.getElementById('friend-item-template');
    
    // 加载好友列表
    loadFriendsList();
    
    // 搜索按钮点击事件
    searchButton.addEventListener('click', function() {
        searchUser();
    });
    
    // 回车键搜索
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchUser();
        }
    });
    
    // 搜索用户函数
    function searchUser() {
        const username = searchInput.value.trim();
        
        if (!username) {
            showSearchMessage('Please enter a username');
            return;
        }
        
        // 显示加载中
        searchResults.innerHTML = '<div class="loading-friends">Searching...</div>';
        
        // 调用API搜索用户
        fetch(`/api/search_user?username=${encodeURIComponent(username)}&exact=true`)
            .then(response => response.json())
            .then(data => {
                searchResults.innerHTML = '';
                
                if (data.status === 'success' && data.data.length > 0) {
                    // 显示搜索结果
                    data.data.forEach(user => {
                        const resultElement = createSearchResultElement(user);
                        searchResults.appendChild(resultElement);
                    });
                } else {
                    // 没有找到用户
                    showSearchMessage('No user found with that exact username');
                }
            })
            .catch(error => {
                console.error('Error searching user:', error);
                showSearchMessage('An error occurred while searching');
            });
    }
    
    // 加载好友列表
    function loadFriendsList() {
        // 显示加载中
        friendsList.innerHTML = '<div class="loading-friends">Loading your friends list...</div>';
        
        // 调用API获取好友列表
        fetch('/api/friends')
            .then(response => response.json())
            .then(data => {
                friendsList.innerHTML = '';
                
                if (data.status === 'success' && data.data.length > 0) {
                    // 显示好友列表
                    data.data.forEach(friend => {
                        const friendElement = createFriendElement(friend);
                        friendsList.appendChild(friendElement);
                    });
                } else {
                    // 没有好友
                    friendsList.innerHTML = '<div class="no-friends-message">You haven\'t added any friends yet</div>';
                }
            })
            .catch(error => {
                console.error('Error loading friends list:', error);
                friendsList.innerHTML = '<div class="error-message">Failed to load friends list</div>';
            });
    }
    
    // 创建搜索结果元素
    function createSearchResultElement(user) {
        const template = searchResultTemplate.content.cloneNode(true);
        
        // 填充数据
        template.querySelector('.result-username').textContent = `${user.username} (ID: ${user.id})`;
        
        const riotIdText = user.riot_id && user.tagline ? 
            `${user.riot_id}#${user.tagline}` : 
            'No Riot ID set';
        
        template.querySelector('.result-riot-id').textContent = riotIdText;
        
        // 添加好友按钮事件
        const addButton = template.querySelector('.add-friend-btn');
        addButton.addEventListener('click', function() {
            addFriend(user.id);
        });
        
        return template;
    }
    
    // 创建好友元素
    function createFriendElement(friend) {
        const template = friendItemTemplate.content.cloneNode(true);
        
        // 填充数据
        template.querySelector('.friend-username').textContent = `${friend.username} (ID: ${friend.id})`;
        
        const riotIdText = friend.riot_id && friend.tagline ? 
            `${friend.riot_id}#${friend.tagline}` : 
            'No Riot ID set';
        
        template.querySelector('.friend-riot-id').textContent = riotIdText;
        
        // 格式化最后登录时间
        const lastLogin = new Date(friend.last_login);
        const formattedDate = lastLogin.toLocaleString();
        template.querySelector('.friend-last-login').textContent = `Last login: ${formattedDate}`;
        
        // 删除好友按钮事件
        const removeButton = template.querySelector('.remove-friend-btn');
        removeButton.addEventListener('click', function() {
            removeFriend(friend.id);
        });
        
        return template;
    }
    
    // 添加好友
    function addFriend(friendId) {
        fetch('/api/add_friend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ friend_id: friendId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 显示成功消息
                showSearchMessage(data.message, 'success');
                // 重新加载好友列表
                loadFriendsList();
            } else {
                // 显示错误消息
                showSearchMessage(data.message || 'Failed to add friend');
            }
        })
        .catch(error => {
            console.error('Error adding friend:', error);
            showSearchMessage('An error occurred while adding friend');
        });
    }
    
    // 删除好友
    function removeFriend(friendId) {
        if (!confirm('Are you sure you want to remove this friend?')) {
            return;
        }
        
        fetch('/api/remove_friend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ friend_id: friendId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 显示成功消息
                const successMessage = document.createElement('div');
                successMessage.className = 'success-message';
                successMessage.textContent = data.message;
                friendsList.insertBefore(successMessage, friendsList.firstChild);
                
                // 短暂显示后删除消息
                setTimeout(() => {
                    successMessage.remove();
                }, 3000);
                
                // 重新加载好友列表
                loadFriendsList();
            } else {
                // 显示错误消息
                const errorMessage = document.createElement('div');
                errorMessage.className = 'error-message';
                errorMessage.textContent = data.message || 'Failed to remove friend';
                friendsList.insertBefore(errorMessage, friendsList.firstChild);
                
                // 短暂显示后删除消息
                setTimeout(() => {
                    errorMessage.remove();
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Error removing friend:', error);
            const errorMessage = document.createElement('div');
            errorMessage.className = 'error-message';
            errorMessage.textContent = 'An error occurred while removing friend';
            friendsList.insertBefore(errorMessage, friendsList.firstChild);
            
            // 短暂显示后删除消息
            setTimeout(() => {
                errorMessage.remove();
            }, 3000);
        });
    }
    
    // 显示搜索消息
    function showSearchMessage(message, type = 'error') {
        searchResults.innerHTML = '';
        const messageElement = document.createElement('div');
        messageElement.className = type === 'success' ? 'success-message' : 'error-message';
        messageElement.textContent = message;
        searchResults.appendChild(messageElement);
    }
});