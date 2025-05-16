// js/friends.js

document.addEventListener('DOMContentLoaded', function() {
    // Get the DOM element
    const searchInput = document.getElementById('search-username');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.getElementById('search-results');
    const friendsList = document.getElementById('friends-list');
    
    // template
    const searchResultTemplate = document.getElementById('search-result-template');
    const friendItemTemplate = document.getElementById('friend-item-template');
    
    // loading friends list on page load
    loadFriendsList();
    
    // Search button click event
    searchButton.addEventListener('click', function() {
        searchUser();
    });
    
    // Search input keypress eventt
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchUser();
        }
    });
    
    // Function to search for a user
    function searchUser() {
        const username = searchInput.value.trim();
        
        if (!username) {
            showSearchMessage('Please enter a username');
            return;
        }
        
        //Display loading message
        searchResults.innerHTML = '<div class="loading-friends">Searching...</div>';
        
        // Fetching user data from the API
        fetch(`/api/search_user?username=${encodeURIComponent(username)}&exact=true`)
            .then(response => response.json())
            .then(data => {
                searchResults.innerHTML = '';
                
                if (data.status === 'success' && data.data.length > 0) {
                    // Results found
                    data.data.forEach(user => {
                        const resultElement = createSearchResultElement(user);
                        searchResults.appendChild(resultElement);
                    });
                } else {
                    // User not found
                    showSearchMessage('No user found with that exact username');
                }
            })
            .catch(error => {
                console.error('Error searching user:', error);
                showSearchMessage('An error occurred while searching');
            });
    }
    
    // Function to load the friends list
    function loadFriendsList() {
        // Display loading message
        friendsList.innerHTML = '<div class="loading-friends">Loading your friends list...</div>';
        
        // Fetching friends list from the API
        fetch('/api/friends')
            .then(response => response.json())
            .then(data => {
                friendsList.innerHTML = '';
                
                if (data.status === 'success' && data.data.length > 0) {
                    // Successfully loaded friends list
                    data.data.forEach(friend => {
                        const friendElement = createFriendElement(friend);
                        friendsList.appendChild(friendElement);
                    });
                } else {
                    // No friends found
                    friendsList.innerHTML = '<div class="no-friends-message">You haven\'t added any friends yet</div>';
                }
            })
            .catch(error => {
                console.error('Error loading friends list:', error);
                friendsList.innerHTML = '<div class="error-message">Failed to load friends list</div>';
            });
    }
    
    // Search results element creationn
    function createSearchResultElement(user) {
        const template = searchResultTemplate.content.cloneNode(true);
        
        // Filing data
        template.querySelector('.result-username').textContent = `${user.username} (ID: ${user.id})`;
        
        const riotIdText = user.riot_id && user.tagline ? 
            `${user.riot_id}#${user.tagline}` : 
            'No Riot ID set';
        
        template.querySelector('.result-riot-id').textContent = riotIdText;
        
        // Add friend button event
        const addButton = template.querySelector('.add-friend-btn');
        addButton.addEventListener('click', function() {
            addFriend(user.id);
        });
        
        return template;
    }
    
    // Add friend element creation
    function createFriendElement(friend) {
        const template = friendItemTemplate.content.cloneNode(true);
        
        // Filling data
        template.querySelector('.friend-username').textContent = `${friend.username} (ID: ${friend.id})`;
        
        const riotIdText = friend.riot_id && friend.tagline ? 
            `${friend.riot_id}#${friend.tagline}` : 
            'No Riot ID set';
        
        template.querySelector('.friend-riot-id').textContent = riotIdText;
        
        // Last login date formatting
        const lastLogin = new Date(friend.last_login);
        const formattedDate = lastLogin.toLocaleString();
        template.querySelector('.friend-last-login').textContent = `Last login: ${formattedDate}`;
        
        // Delete friend button event
        const removeButton = template.querySelector('.remove-friend-btn');
        removeButton.addEventListener('click', function() {
            removeFriend(friend.id);
        });
        
        return template;
    }
    
    // Add friend function
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
                // Success message
                showSearchMessage(data.message, 'success');
                // Reload friends list
                loadFriendsList();
            } else {
                // Error message
                showSearchMessage(data.message || 'Failed to add friend');
            }
        })
        .catch(error => {
            console.error('Error adding friend:', error);
            showSearchMessage('An error occurred while adding friend');
        });
    }
    
    // Remove friend function
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
                // Success message
                const successMessage = document.createElement('div');
                successMessage.className = 'success-message';
                successMessage.textContent = data.message;
                friendsList.insertBefore(successMessage, friendsList.firstChild);
                
                // Temporary display and remove
                setTimeout(() => {
                    successMessage.remove();
                }, 3000);
                
                // Reload friends list
                loadFriendsList();
            } else {
                // Error message
                const errorMessage = document.createElement('div');
                errorMessage.className = 'error-message';
                errorMessage.textContent = data.message || 'Failed to remove friend';
                friendsList.insertBefore(errorMessage, friendsList.firstChild);
                
                // Temporary display and remove
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
            
            // Temporary display message
            setTimeout(() => {
                errorMessage.remove();
            }, 3000);
        });
    }
    
    // Show search message function
    function showSearchMessage(message, type = 'error') {
        searchResults.innerHTML = '';
        const messageElement = document.createElement('div');
        messageElement.className = type === 'success' ? 'success-message' : 'error-message';
        messageElement.textContent = message;
        searchResults.appendChild(messageElement);
    }
});