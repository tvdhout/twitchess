const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');
const username = urlParams.get('user');
if (token != null && username != null) {
    // Authenticate button
    document.getElementById('twitch-auth-button').hidden = true;
    document.getElementById('authentication-text').innerHTML = '<strike>Authenticate the Twitch API</strike> <span style="color:#ffab61;"><i class="fas fa-check"></i> Authenticated</span>'

    document.getElementById('token').innerHTML = token;
    document.getElementById('token-box').value = token;
    document.getElementById('token-box').hidden = false;
    document.getElementById('token-label').hidden = false;

    const codebox = document.getElementById('nightbot-command');
    codebox.innerHTML = `$(eval ($(urlfetch https://twitchess.app/${username}/create?twitch=$(user)&lichess=$(querystring)&token=${token}))['message'])`
    codebox.hidden = false;
}

function copyToken() {
    const token = document.getElementById('token').innerHTML;
    navigator.clipboard.writeText(token)
        .then(() => {
            const icon = document.getElementById('clipboard-icon');
            icon.classList.replace('far', 'fas');
            icon.classList.replace('fa-clipboard', 'fa-check');
            setTimeout(() => {
                icon.classList.replace('fas', 'far');
                icon.classList.replace('fa-check', 'fa-clipboard');
            }, 1000);
        })
}
