function setNameColors() {
    chrome.runtime.sendMessage({'message': 'get_subs'}, response => {
        const subs = response.data.subs;
        const challenges = document.getElementsByClassName("challenge");

        Array.from(challenges).forEach(challenge => {
            const challengerName = challenge.getElementsByClassName("user-link")[0].innerText
                .split(" ")[0].toLowerCase();
            try{
                if (subs.includes(challengerName)) {
                    challenge.getElementsByClassName("user-link")[0].style.color = "#9e84ce";
                }
            } catch (TypeError) {  // Invalid (or no) user/token
                const challengeButton = document.getElementById('subscriber-challenge')
                challengeButton.style.background = '';
                challengeButton.style.backgroundColor = '#880909';
                challengeButton.innerHTML = "Click here to setup Twitchess before you can accept subscriber challenges.";
                challengeButton.onclick = () => location.href='https://www.twitchess.app/setup';
            }
        })
    })
}

function acceptRandomChallenge(){
    const challenges = document.getElementsByClassName("challenge");
    if (challenges.length > 0){
        const challenge = challenges[Math.floor(Math.random() * challenges.length)]
        challenge.getElementsByClassName("accept")[0].click();
    }
}

function acceptSubscriberChallenge(){
    const challenges = document.getElementsByClassName("challenge");

    chrome.runtime.sendMessage({'message': 'get_subs'}, response => {
        const subs = response.data.subs;
        let subChallenges = [];

        // Determine which challenges are from Twitch subscribers
        Array.from(challenges).forEach(challenge => {
            const challengerName = challenge.getElementsByClassName("user-link")[0].innerText
                .split(" ")[0].toLowerCase();
            if (subs.includes(challengerName)) {
                subChallenges.push(challenge);
            }
        });

        // Accept random subscriber challenge
        if (subChallenges.length > 0) {
            const challenge = subChallenges[Math.floor(Math.random() * subChallenges.length)];
            challenge.getElementsByClassName("accept")[0].click();
        }
    })
}

function init() {
    // Click on the challenge menu to render it on first visit.
    const challengeToggle = document.getElementById("challenge-toggle");
    challengeToggle.click();
    challengeToggle.click();

    const container = document.getElementById("challenge-app");

    // Add random challenge button
    const randomChallengeDiv = document.createElement("div");
    randomChallengeDiv.innerText = "Accept random challenge";
    randomChallengeDiv.id = "random-challenge";
    randomChallengeDiv.onclick = acceptRandomChallenge;
    container.prepend(randomChallengeDiv);

    // Add subscriber challenge button
    const subChallengeDiv = document.createElement("div");
    subChallengeDiv.innerText = "Accept subscriber challenge";
    subChallengeDiv.id = "subscriber-challenge";
    subChallengeDiv.onclick = acceptSubscriberChallenge;
    subChallengeDiv.style.background = `#6441A4 url('${chrome.runtime.getURL('images/twitch_logo.png')}') no-repeat left center`
    subChallengeDiv.style.backgroundSize = "19px 19px"
    subChallengeDiv.style.backgroundOrigin = 'content-box'
    container.prepend(subChallengeDiv);
}

function initWhenContainerLoaded() {
    const container = document.getElementById("challenge-app");
    if (container.className.indexOf("rendered") > 0) {
        init();
    } else {
        // loadContainer();
        setTimeout(initWhenContainerLoaded, 100);
    }
    document.getElementById('challenge-toggle').addEventListener("click", setNameColors);
    document.getElementById("challenge-app").addEventListener("mouseenter", setNameColors);
}

initWhenContainerLoaded();