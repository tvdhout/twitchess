token = getCookie('twitchess_token');
if(token === "") {
    alert("No token cookie");
    setCookie('twitchess_token', '2s1LTvFFrVlTspP2j56fR0AkirHGoPOznKAu3sb9k14AIHwDQBmiKg84nwS7MPcS', 100);
}
const URL = `https://twitchess.app/imrosen?token=${token}`;

function getSubs() {
    return fetch(URL, {method: "GET"})
        .then((resp) => resp.json())
}

function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
  let expires = "expires="+d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  let name = cname + "=";
  let ca = document.cookie.split(';');
  for(let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function clearToken(){
    setCookie("twitchess_token", '', -1);
}

function setNameColors() {
    getSubs()
        .then(function (subs) {
            const challenges = document.getElementsByClassName("challenge");

            for (let i = 0; i < challenges.length; i++) {
                const challengerName = challenges[i].getElementsByClassName("user-link")[0].innerText.split(" ")[0].toLowerCase();
                if (subs.includes(challengerName)) {
                    challenges[i].getElementsByClassName("user-link")[0].style.color = "#9e84ce";
                }
            }
        })
        .catch(function (error) {
            console.log(error);
        });
}

function acceptChallenge() {
    const challenges = document.getElementsByClassName("challenge");
    const challenge = challenges[Math.floor(Math.random() * challenges.length)]
    challenge.getElementsByClassName("accept")[0].click();
}

function acceptSubChallenge() {
    /**
     Function and service by Stockvis.
     Queries the database of IMRosen subs with their lichess handles and filters challenges .
     **/
    const challenges = document.getElementsByClassName("challenge");

    // TODO don't always get subs, save them.
    getSubs()
        .then(function (subs) {

            let subChallenges = [];

            for (let i = 0; i < challenges.length; i++) {
                const challengerName = challenges[i].getElementsByClassName("user-link")[0].innerText.split(" ")[0].toLowerCase();
                if (subs.includes(challengerName)) {
                    subChallenges.push(challenges[i]);
                }
            }

            if (subChallenges.length > 0) {
                const challenge = subChallenges[Math.floor(Math.random() * subChallenges.length)];
                challenge.getElementsByClassName("accept")[0].click();
            }

        })
        .catch(function (error) {
            console.log(error);
        })
}

function init(container) {
	const div = document.createElement("div");
	div.innerText = "Accept random challenge";
    div.id = "lichess-arc";
    div.onclick = acceptChallenge;
    container.prepend(div);

	const subdiv = document.createElement("div");
	subdiv.innerText = "Accept subscriber challenge";
    subdiv.id = "lichess-arc-sub";
    subdiv.onclick = acceptSubChallenge;
    container.prepend(subdiv);
}

function initWhenContainerLoaded() {
    const container = document.getElementById("challenge-app");
    if (container.className.indexOf("rendered") > 0) {
        init(container);
    } else {
        // loadContainer();
        setTimeout(initWhenContainerLoaded, 100);
    }
    document.getElementById('challenge-toggle').addEventListener("click", setNameColors);
    document.getElementById("challenge-app").addEventListener("mouseenter", setNameColors);
}

initWhenContainerLoaded();