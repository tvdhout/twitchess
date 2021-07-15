# twitchess
Accept Lichess challenges from Twitch subscribers

### Nightbot command:

`$(eval ($(urlfetch https://twitchess.app/username/create?twitch=$(user)&lichess=$(querystring)&token=yourtoken))['message'])`