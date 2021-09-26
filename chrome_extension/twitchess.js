document.getElementById('install-extension').innerHTML = '<strike>Install the Twitchess Chrome extension</strike> <span style="color:#ffab61;"><i class="fas fa-check"></i> Installed</span>'

chrome.runtime.sendMessage({'message': 'check_connected'}, response => {
    if(response.valid){
        document.getElementById('twitch-button-text').innerHTML = 'Generate new token';
        document.getElementById('authenticate-button').onclick = () => newToken(response.user, response.token);
        document.getElementById('authentication-text').innerHTML = '<strike>Authenticate the Twitch API</strike> <span style="color:#ffab61;"><i class="fas fa-check"></i> Authenticated</span>'

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
