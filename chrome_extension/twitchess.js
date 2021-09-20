document.getElementById('install-extension').innerHTML = '<strike>Install the Twitchess Chrome extension</strike> <span style="color:#ffab61;"><i class="fas fa-check"></i> Installed</span>'

chrome.runtime.sendMessage({'message': 'check_connected'}, response => {
    if(response.valid){
        document.getElementById('twitch-button-text').innerHTML = 'Generate new token';
        document.getElementById('authentication-text').innerHTML = '<strike>Authenticate the Twitch API</strike> <span style="color:#ffab61;"><i class="fas fa-check"></i> Authenticated</span>'

        // document.getElementById('token').innerHTML = response['token'];
        // document.getElementById('token-box').value = response['token'];
        // document.getElementById('token-box').hidden = false;
        // document.getElementById('token-label').hidden = false;

        const codebox = document.getElementById('nightbot-command');
        codebox.innerHTML = `$(eval ($(urlfetch https://api.twitchess.app/${response['user']}/create?twitch=$(user)&lichess=$(querystring)&token=${response['token']})))`
        document.getElementById('nightbot-box').hidden = false;
    }
});
