document.addEventListener('DOMContentLoaded', function() {
    const friendsListContainer = document.getElementById('friends-list-share-container');
    const friendStatsDisplayContainer = document.getElementById('friend-stats-display-container');
    const friendInfoCard = document.getElementById('friend-info-card');
    const friendUsernameDisplay = document.getElementById('friend-username-display');
    const friendFaveChampsList = document.getElementById('friend-fave-champs-list');
    const friendTotalMultikillsValue = document.getElementById('friend-total-multikills-value');
    const friendFaveGamemodeValue = document.getElementById('friend-fave-gamemode-value');
    const initialMessageElement = friendStatsDisplayContainer.querySelector('.initial-message');
    const friendStatsMessageElement = document.getElementById('friend-stats-message');

    let currentSelectedFriendElement = null;

    function showStatusMessage(message, isError = false, isLoading = false) {
        friendInfoCard.style.display = 'none'; // Hide actual data card
        initialMessageElement.style.display = 'none'; // Hide initial prompt

        friendStatsMessageElement.textContent = message;
        friendStatsMessageElement.className = 'info-message'; // Reset classes
        if (isError) {
            friendStatsMessageElement.classList.add('error');
        }
        if (isLoading) {
            // You could add a 'loading' class for spinner or specific styling
        }
        friendStatsMessageElement.style.display = 'block';
    }

    function showFriendDataCard() {
        initialMessageElement.style.display = 'none';
        friendStatsMessageElement.style.display = 'none';
        friendInfoCard.style.display = 'block';
    }

    function showInitialPrompt() {
        friendInfoCard.style.display = 'none';
        friendStatsMessageElement.style.display = 'none';
        initialMessageElement.style.display = 'block';
    }

    async function fetchAndDisplayFriends() {
        try {
            friendsListContainer.innerHTML = '<p class="loading-message">Loading friends...</p>';
            const response = await fetch('/api/friends');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();

            if (result.status === 'success' && result.data) {
                friendsListContainer.innerHTML = ''; // Clear loading/error message
                if (result.data.length > 0) {
                    result.data.forEach(friend => {
                        const friendElement = document.createElement('div');
                        friendElement.classList.add('friend-item-share');
                        friendElement.dataset.friendId = friend.id;
                        friendElement.dataset.friendUsername = friend.username;

                        const iconPlaceholder = document.createElement('div');
                        iconPlaceholder.classList.add('friend-icon-placeholder-share');
                        iconPlaceholder.textContent = friend.username.substring(0, 1).toUpperCase();

                        const usernameSpan = document.createElement('span');
                        usernameSpan.classList.add('friend-username-share');
                        usernameSpan.textContent = friend.username;
                        
                        friendElement.appendChild(iconPlaceholder);
                        friendElement.appendChild(usernameSpan);

                        friendElement.addEventListener('click', function() {
                            if (currentSelectedFriendElement) {
                                currentSelectedFriendElement.classList.remove('active');
                            }
                            this.classList.add('active');
                            currentSelectedFriendElement = this;
                            fetchAndDisplayFriendSummary(this.dataset.friendId, this.dataset.friendUsername);
                        });
                        friendsListContainer.appendChild(friendElement);
                    });
                } else {
                    friendsListContainer.innerHTML = '<p class="no-friends-message">You have no friends yet. Add some from the Friends page!</p>';
                }
            } else {
                throw new Error(result.message || 'Failed to load friends data.');
            }
        } catch (error) {
            console.error('Error loading friends list:', error);
            friendsListContainer.innerHTML = `<p class="error-message">Could not load friends: ${error.message}</p>`;
        }
    }

    async function fetchAndDisplayFriendSummary(friendId, friendUsername) {
        showStatusMessage(`Loading stats for ${friendUsername}...`, false, true);

        try {
            const response = await fetch(`/api/friend_summary/${friendId}`);
            if (!response.ok) {
                const errorResult = await response.json().catch(() => ({ message: `HTTP error! Status: ${response.status}` }));
                throw new Error(errorResult.message || `HTTP error! Status: ${response.status}`);
            }
            const result = await response.json();

            if (result.status === 'success' && result.data) {
                const data = result.data;
                friendUsernameDisplay.textContent = data.username || friendUsername;

                friendFaveChampsList.innerHTML = ''; // Clear previous list
                if (data.favorite_champions && data.favorite_champions.length > 0) {
                    data.favorite_champions.forEach(champName => {
                        const li = document.createElement('li');
                        li.textContent = champName;
                        friendFaveChampsList.appendChild(li);
                    });
                } else {
                    const li = document.createElement('li');
                    li.textContent = 'No champion data available.';
                    friendFaveChampsList.appendChild(li);
                }

                friendTotalMultikillsValue.textContent = data.total_multikills !== undefined ? data.total_multikills : 'N/A';
                friendFaveGamemodeValue.textContent = data.favorite_game_mode || 'N/A';
                
                showFriendDataCard();

            } else if (result.status === 'info') {
                 // Display info message (e.g. friend data not analyzed yet)
                showStatusMessage(result.message || `Stats for ${friendUsername} are currently unavailable.`, false, false);
                // Optionally, you could still display some basic info if available
                friendUsernameDisplay.textContent = result.data.username || friendUsername;
                friendFaveChampsList.innerHTML = '<li>Data not fully available.</li>';
                friendTotalMultikillsValue.textContent = 'N/A';
                friendFaveGamemodeValue.textContent = 'N/A';
                // Keep the card visible but with placeholder data
                 showFriendDataCard(); 
            }
            else { // Handles 'error' status from our API
                throw new Error(result.message || `Could not load summary for ${friendUsername}.`);
            }
        } catch (error) {
            console.error(`Error fetching summary for friend ${friendId}:`, error);
            showStatusMessage(`Failed to load stats for ${friendUsername}: ${error.message}`, true, false);
        }
    }

    // Initialize the page
    fetchAndDisplayFriends();
    showInitialPrompt(); // Show the initial prompt in the right panel
});