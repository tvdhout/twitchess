// background.js

function checkConnection(sendResponse) {
    /**
     * @param sendResponse  {response} function to send a response to the message sent by the popup
     * Check if the user is connected on Twitchess.
     */
    chrome.storage.local.get(['user', 'sessionToken'], data => {
        if (typeof data.user === 'undefined' || typeof data.sessionToken === 'undefined') {
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

    });
}

function retrieveSubsFromAPI(sendResponse) {
    chrome.storage.local.get(['user', 'sessionToken'], data => {
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
                    chrome.storage.local.set({subs: subs}, null);
                    chrome.storage.local.set({subsDate: new Date().toJSON()}, null);
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
    chrome.storage.local.get(['subs', 'subsDate'], data => {
        if (chrome.runtime.lastError) {  // Data not found in storage
            retrieveSubsFromAPI(sendResponse);
        } else {
            if (new Date(data.subsDate).getTime() > ((new Date()).getTime() - 10000)) {
                sendResponse({
                    'success': true,
                    'data': {'subs': data.subs}
                });
            } else {  // Data in storage older than 10 seconds
                retrieveSubsFromAPI(sendResponse);
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

    return true;  // Keep communication between foreground and background alive during alocal code above.
})
