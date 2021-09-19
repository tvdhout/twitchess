// background.js

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Check if tab is loaded completely, and if the domain is lichess.org
    // Inject CSS / javascript on loading lichess
    if (changeInfo.status === 'complete' && /^https?:\/\/(\w*\.)?lichess\.org\//.test(tab.url)) {
        chrome.scripting.insertCSS({
            target: {tabId: tabId},
            files: ['foreground.css']
        })
            .then(() => {
                chrome.scripting.executeScript({
                    target: {tabId: tabId},
                    files: ['foreground.js']
                }, null)
            })
            .catch(error => {
                console.log(error)
            });
    } else if (changeInfo.status === 'complete' &&
        /^https?:\/\/(\w*\.)?twitchess\.app\/setup/.test(tab.url)) {
        console.log("On twitchess setup page.")
        chrome.scripting.executeScript({
            target: {tabId: tabId},
            files: ['twitchess.js']
        }, null)
        // Set user and token
        try{
            const urlParams = new URLSearchParams(tab.url.match(/\?(.*)/)[0]);
            const user = urlParams.get('user');
            const token = urlParams.get('token');
            if(user != null && token != null){
                chrome.storage.sync.set({sessionToken: token}, null);
                chrome.storage.sync.set({user: user}, null);
            }
        } catch (TypeError) {}
    }
});

function checkConnection(sendResponse){
    /**
     * @param sendResponse  {response} function to send a response to the message sent by the popup
     * Check if the user is connected on Twitchess.
     */
    chrome.storage.sync.get(['user', 'sessionToken'], data => {
        if (chrome.runtime.lastError) {
            sendResponse({
                'message': 'failed',
                'reason': 'Could not retrieve [user, sessionToken] from local storage.'
            });
            return;
        }
        fetch(`https://api.twitchess.app/${data.user}/check-token?token=${data.sessionToken}`)
            .then(resp => resp.json())
            .catch(() => {
                sendResponse({
                    'valid': false
                })
            })
            .then(data => {
                sendResponse({
                    'valid': data['valid']
                });
            });
    })
}

function getSubs(sendResponse) {
    /**
     * @param sendResponse  {response} function to send a response to the message sent by the frontend
     * Retrieve a list of lichess names of users that are subscribed on Twitch.
     */
    chrome.storage.sync.get(['user', 'sessionToken'], data => {
        if (chrome.runtime.lastError) {
            sendResponse({
                'message': 'failed',
                'reason': 'Could not retrieve [user, sessionToken] from local storage.'
            });
            return;
        }
        fetch(`https://api.twitchess.app/${data.user}?token=${data.sessionToken}`)
            .then(resp => resp.json())
            .then(subs => {
                sendResponse({
                    'message': 'success',
                    'data': {'subs': subs}
                });
            });
    })
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.message) {
        case 'get_subs':
            getSubs(sendResponse);
            break;
        case 'check_connected':
            checkConnection(sendResponse);
            break;
        default:
    }

    return true;  // Keep communication between foreground and background alive during async code above.
})
