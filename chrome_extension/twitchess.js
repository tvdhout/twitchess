document.getElementById('install-extension').innerHTML = '<span style="text-decoration: line-through;">Install the Twitchess Chrome extension</span> <span style="color:#ffab61;"><i class="fas fa-check"></i> Installed</span>'

try {
    const urlParams = new URLSearchParams(location.href.match(/\?(.*)/)[0]);
    const user = urlParams.get('user');
    const token = urlParams.get('token');
    if (user != null && token != null) {
        chrome.storage.sync.set({sessionToken: token}, null);
        chrome.storage.sync.set({user: user}, null);
    }
} catch (TypeError) {
}

chrome.runtime.sendMessage({'message': 'check_connected'}, response => {
    if(response.valid){
        document.getElementById('twitch-button-text').innerHTML = 'Generate new token';
        document.getElementById('authenticate-button').onclick = () => newToken(response.user, response.token);
        document.getElementById('authentication-text').innerHTML = '<span style="text-decoration: line-through;">Authenticate the Twitch API</span> <span style="color:#ffab61;"><i class="fas fa-check"></i> Authenticated</span>'

        const codebox = document.getElementById('nightbot-command');
        codebox.innerHTML = `$(eval ($(urlfetch https://api.twitchess.app/${response.user}/create?twitch=$(user)&lichess=$(querystring)&token=${response.token})))`
        document.getElementById('nightbot-box').hidden = false;
    } else {
        console.log("Not connected")
    }
});

function newToken(user, token){
    document.getElementById('twitch-button-text').innerHTML = "Please wait...";
    location.href = `https://api.twitchess.app/${user}/new-token?token=${token}`;
}
