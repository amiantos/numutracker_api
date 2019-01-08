[![Build Status](https://travis-ci.org/amiantos/numutracker_api.svg?branch=master)](https://travis-ci.org/amiantos/numutracker_api)

# Numu Tracker API

This is the home for the third version of the Numu Tracker API. If you're not familiar with what Numu Tracker is, check out [the iOS App repository](https://www.github.com/amiantos/numutracker_ios) to see what it is all about, or keep reading.

## About

The Numu Tracker API is a service that allows users to follow a list of musicians, and receive a personalized 'to-do list' of releases by those musicians that they need to listen to. Users can mark releases as "Listened" to check them off their list. Releases by artists can also be browsed individually, and the personalized release list can be filtered in various ways (by Album, EP, Single, Live Albums, Remixes, Other). Numu Tracker can also provide simple statistics letting a user know how much of their releases they've listened to.

It supports an iOS app that receives push notifications of various types (which are sent by the API using Pusher):
1. On the day new releases come out.
    - And when recent (last 6 mos) releases are added.
2. When upcoming releases are added.
3. When past releases are added.

User privacy is very important to Numu Tracker. The official instance of Numu Tracker running at numutracker.com should feature a simple privacy policy that states that any user data (email address, the user's artist list and release listening history) will never be monetized for any reason, and any user activity (app usage, etc) is only shared with third parties when necessary in an effort to improve the software.

## What's new in v3?

APIv3 is being built to support the next generation of the iOS app. The main goals of the project are:

1. Expand the Numu Tracker API to be more fully featured (e.g. support password reset requests)
1. Better infrastructure / code architecture
1. More FOSS friendly for local / distributed development.
1. Improve the app experience with the following feature improvements:
    - Releases by multiple artists should be properly supported (no more duplicate releases).
    - You should be able to add individual releases to Your Releases without following the artist.
    - Links to Apple Music (or Spotify) should be handled server-side so that incorrect links can be corrected for all users.
    - Improved API performance / response times.
1. Seamless account import between versions.
1. Better library statistics.
1. Some day: Recommendations!


## To Install

1. `git clone https://github.com/amiantos/numutracker_api.git .`
1. `docker-compose build`
1. `docker-compose up`


## Author

* [Brad Root](https://bradroot.me) - [amiantos](https://github.com/amiantos)

See also the list of [contributors](https://github.com/amiantos/numutracker_api/contributors).

## Beta Testers

If you'd like to beta test production versions of Numu Tracker for iOS, you can join via [this TestFlight link](https://testflight.apple.com/join/Voa7rsgJ).

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details

## Acknowledgements
Numu Tracker wouldn't exist without the following services:
- [MusicBrainz.org](http://www.musicbrainz.org) - Artist and Release Information
- [Last.FM](http://www.last.fm) - Artist and Release Images
