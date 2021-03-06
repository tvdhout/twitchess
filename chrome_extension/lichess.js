function setNameColors() {
    chrome.runtime.sendMessage({'message': 'get_subs'}, response => {
        if (!response.success){
            notConnected();
            return;
        }
        const subs = response.data.subs;
        const challenges = document.getElementsByClassName("challenge");

        Array.from(challenges).forEach(challenge => {
            const challengerName = challenge.getElementsByClassName("user-link")[0].innerText
                .split(" ")[0].toLowerCase();
            try{
                if (subs.includes(challengerName)) {
                    challenge.getElementsByClassName("user-link")[0].style.color = "#9e84ce";
                }
            } catch (TypeError) {}
        })
    })
}

function acceptRandomChallenge(){
    const challenges = document.getElementsByClassName("challenge");
    if (challenges.length > 0){
        const challenge = challenges[Math.floor(Math.random() * challenges.length)];
        challenge.getElementsByClassName("accept")[0].click();
    }
}

function acceptSubscriberChallenge(){
    chrome.runtime.sendMessage({'message': 'get_subs'}, response => {
        if (!response.success){
            notConnected();
            return;
        }

        const challenges = document.getElementsByClassName("challenge");
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
    subChallengeDiv.style.background = `#6441A4 url('${chrome.runtime.getURL('images/twitch_logo.png')}') no-repeat left center`;
    subChallengeDiv.style.backgroundSize = "19px 19px";
    subChallengeDiv.style.backgroundOrigin = 'content-box';
    container.prepend(subChallengeDiv);
}

function initWhenContainerLoaded() {
    const challengeToggle = document.getElementById("challenge-toggle");
    challengeToggle.click();
    challengeToggle.click();

    let container = document.getElementById("challenge-app");
    if (container.className.indexOf("rendered") > 0) {
        init();
    } else {
        setTimeout(initWhenContainerLoaded, 500);
        return;
    }

    chrome.runtime.sendMessage({'message': 'check_connected'}, response => {
        if (response.valid) {
            document.getElementById('challenge-toggle').addEventListener("click", setNameColors);
            document.getElementById("challenge-app").addEventListener("mouseenter", setNameColors);
        } else {
            notConnected();
        }
    });
}

function notConnected(){
    const challengeButton = document.getElementById('subscriber-challenge')
    challengeButton.style.background = '';
    challengeButton.style.backgroundColor = '#001d24';
    challengeButton.innerHTML = '<b>Not connected! <span style="color: #ffab61">Click here</span> to setup Twitchess.</b>';
    challengeButton.onclick = () => location.href = 'https://www.twitchess.app/setup';
}

initWhenContainerLoaded();