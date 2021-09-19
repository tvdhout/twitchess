const text = 'TWITCHESS';

async function type(){
    const el = document.getElementById('twitchess');
    for (let i = 0; i <= text.length; i++) {
        el.innerHTML = text.substr(0, i);
        await new Promise(r => setTimeout(r, i*10 + 30));
    }
    el.style.fill = 'whitesmoke';
}

type();  // Typing animation of title
