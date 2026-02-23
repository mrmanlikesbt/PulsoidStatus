# PulsoidStatus

PulsoidStatus is a [BetterDiscord](https://betterdiscord.app) plugin that will set your discord status to your heart rate every ~30 seconds using [Pulsoid](https://pulsoid.net)

Due to [modern net safety features](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Origin), a local python server is required to be a middleman in-between the plugin and Pulsoid.

# How do I actually get it to work

1. Ensure you have a [compatible heart rate monitor](https://blog.pulsoid.net/monitors)
2. [Register an account](https://pulsoid.net/registration)
3. [Register an API key](https://pulsoid.net/ui/keys)
4. Replace `YOUR_API_TOKEN` in [PulsoidLocalhost.bat](Python/PulsoidLocalhost.bat) with your newly acquired token
5. Install [BetterDiscord](https://betterdiscord.app)
6. Move the [plugin](Plugin/PulsoidStatus.plugin.js) to your BetterDiscord plugins folder
7. Enable the plugin and run `PulsoidLocalhost.bat`
