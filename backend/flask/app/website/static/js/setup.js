function copyCommand() {
    const token = document.getElementById('nightbot-command').innerText;
    const copied = document.getElementById('copied')
    navigator.clipboard.writeText(token)
        .then(() => {
            const icon = document.getElementById('clipboard-icon');
            icon.classList.replace('far', 'fas');
            icon.classList.replace('fa-clipboard', 'fa-check');
            copied.hidden = false;
            setTimeout(() => {
                icon.classList.replace('fas', 'far');
                icon.classList.replace('fa-check', 'fa-clipboard');
                copied.hidden = true;
            }, 1000);
        })
}

let howExtra = 1;
function makeExtraSpecial(el){
    howExtra++;
    el.innerHTML = "extra ".repeat(howExtra);
}
