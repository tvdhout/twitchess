// popup.js

chrome.runtime.sendMessage({'message': 'check_connected'}, response => {
    document.getElementById('dots').hidden = true;

    if(response['valid']){
        document.getElementById('connected').hidden = false;
        document.getElementById('help-box').hidden = false;
        document.getElementById('not-connected').hidden = true;
    } else{
        document.getElementById('connected').hidden = true;
        document.getElementById('help-box').hidden = true;
        document.getElementById('not-connected').hidden = false;
    }
});
