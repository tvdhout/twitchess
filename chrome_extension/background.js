// background.js

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Check if tab is loaded completely, and if the domain is lichess.org
    // Inject CSS / javascript on loading lichess
    if (changeInfo.status === 'complete' && /^https?:\/\/(?:\w*\.)?lichess\.org(?!\/api(\/|#|\?|$))/.test(tab.url)) {
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
        // Set user and token
        try {
            const urlParams = new URLSearchParams(tab.url.match(/\?(.*)/)[0]);
            const user = urlParams.get('user');
            const token = urlParams.get('token');
            if (user != null && token != null) {
                chrome.storage.sync.set({sessionToken: token}, null);
                chrome.storage.sync.set({user: user}, null);
            }
        } catch (TypeError) {
        }
        chrome.scripting.executeScript({
            target: {tabId: tabId},
            files: ['twitchess.js']
        }, null)
    }
});

function checkConnection(sendResponse) {
    /**
     * @param sendResponse  {response} function to send a response to the message sent by the popup
     * Check if the user is connected on Twitchess.
     */
    chrome.storage.sync.get(['user', 'sessionToken'], data => {
        if (chrome.runtime.lastError) {
            sendResponse({
                'valid': false,
                'message': 'failed',
                'reason': 'Could not retrieve [user, sessionToken] from local storage.'
            });
            return;
        }
        fetch(`https://api.twitchess.app/${data.user}/check-auth?token=${data.sessionToken}`)
            .then(resp => resp.json())
            .catch(() => {
                sendResponse({
                    'valid': false
                })
            })
            .then(resp => {
                const valid = resp.valid;
                sendResponse({
                    'valid': valid,
                    'user': valid ? data.user : null,
                    'token': valid ? data.sessionToken : null
                });
            });
    })
}

function retrieveSubs(sendResponse){
    chrome.storage.sync.get(['user', 'sessionToken'], data => {
        if (chrome.runtime.lastError) {
            sendResponse({
                'success': false,
                'reason': 'Could not retrieve [user, sessionToken] from local storage.'
            });
            return;
        }
        fetch(`https://api.twitchess.app/${data.user}?token=${data.sessionToken}`)
            .then(resp => resp.json())
            .then(subs => {
                if (Array.isArray(subs)) {
                    sendResponse({
                        'success': true,
                        'data': {'subs': subs}
                    });
                    chrome.storage.sync.set({subs: subs}, null);
                    chrome.storage.sync.set({subsDate: new Date().toJSON()}, null);
                } else {
                    sendResponse({
                        'success': false,
                        'reason': 'API did not return a list of subscribers.'
                    });
                }
            });
    });
}

function getSubs(sendResponse) {
    /**
     * @param sendResponse  {response} function to send a response to the message sent by the frontend
     * Get a recent list of subs from storage (20 sec), otherwise retrieve them from the API.
     */
    chrome.storage.sync.get(['subs', 'subsDate'], data => {
        if (chrome.runtime.lastError) {
            retrieveSubs(sendResponse);
        } else {
            if (new Date(data.subsDate).getTime() > ((new Date()).getTime() - 10000)) {
                sendResponse({
                    'success': true,
                    'data': {'subs': data.subs}
                });
            } else {
                retrieveSubs(sendResponse);
            }
        }
    });
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
