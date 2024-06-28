# Hello, I'm RinBot!

RinBot is a multi-purpose discord bot fully developed in Python using the `nextcord` library.

### Requirements
| Requirement | Version |
| - | - |
| Python | 3.9+ and the necessary modules under requirements.txt |
| Java | 17+ |

## Overview

- Programmed with both Windows and Linux in mind.
- AI functionality with Gemini, StableDiffusion and Kobold.
- Rewards system for active server members.
- Command Cog extensions structure for easy functionality expansion.
- Built-in logger with colours, multiple categories and tracebacks (errors) logging.
- User ID tied command permission class system (explained below).
- User blacklisting to prevent undesired users to use the bot.
- "Warning" system, which automatically kicks users past a certain amount of warnings.
- SQL database to store data.
- Server moderation tools.
- Music playback with search queries and playlists support.
    (Youtube and Soundcloud supported by default, Spotify, Deezer and others can be enabled on the config files.)
- Rule34 and Danbooru integration if you're into that.
- Integration with the FortniteAPI to show the daily shop and player statistics.
- Much more...

### Economy system
As of update 1.8, RinBot now has a economy system with oranges as the currency.
**The way it works is as follows:**
* Users will receive 500 oranges by default upon entering a server and being registered in the economy database.
* Users will be rewarded 25 oranges every 50 messages sent.
* Users can transfer oranges between eachother using the `/orange transfer` command.
* Users can see the top 10 users with the most oranges using the `/orange rank` command.
* Users can use their oranges to buy items from the shop using the `/orange store` and `/orange buy` command.
## NOTE: Currently only roles are supported by the orange store, more item types will be added in the future.

### User ID permission class system

It looks complicated, but it's easy to understand. RinBot has a "class" system composed of 3 classes, these being: **"Owners", "Admins" and "Blacklisted"**.

The **"owners"** class are the ones to have absolute full control of the entire bot. They can reset it, shut it down, manipulate extensions, add/remove users from the admin class, and of course, they can use any commands. As soon as you run the `init.py` file, and it creates a fresh database, you will be prompted to add your discord ID to be set as the owner of the bot.

The **"admins"** class is meant for administrators / moderators of the server the bot is on. It provides access to commands of the "moderation" command cog, where they can blacklist users, manipulate warnings and use the `/censor` command. To add / remove users from this class, a user with admin priv on the server needs to use the `/admins set` command.

Users inside the **blacklisted** class are well... blacklisted from using ANY functionality of the bot. To add / remove users from this class, a user in the admins or owners class needs to use the `/blacklist` command.

## Commands

### General
| Command | Description |
| - | - |
| `/rininfo` | Shows information about the bot |
| `/help` | You just used it. |
| `/translate` | Translates a text from one language to another using the "Translate" library |
| `/list-languages` | Lists the compatible languages for some functionalities |
| `/specs` | Shows the specs. of the system running the bot |

### Core
| Command | Description |
| - | - |
| `/extension list` | Shows the list of loaded extensions |
| `/extension load` | Loads a bot extension |
| `/extension unload` | Unloads a bot extension |
| `/extension reload` | Reloads a bot extension |
| `/owners add` | Adds a user to the owners class |
| `/owners remove` | Removes a user from the owners class  |
| `/ping` | Pong! |
| `/shutdown` | Shuts the bot down. |

### Config
| Command | Description |
| - | - |
| `/set welcome-channel` | Sets a text channel on your server for RinBot to greet new members with a custom message |
| `/set daily-shop-channel fortnite` | Sets a text channel on your server for RinBot to send the daily fortnite item shop (Updates  |everyday at 00:05 UTC)
| `/toggle daily-shop fortnite` | Toggles on and off the fortnite daily shop |

### Moderation
| Command | Description |
| - | - |
| `/warnings show` | Shows a user's warnings |
| `/warnings add` | Adds a warning to a user |
| `/warnings remove` | Removes a warning from a user |
| `/admins add` | Adds a user to the admins class |
| `/admins remove` | Removes a user from the admins class |
| `/admins add-me` | Checks if you're an admin and adds you to the class |
| `/blacklist show` | Shows the users inside the blacklist (if any) |
| `/blacklist add` | Adds a user to the blacklist |
| `/blacklist remove` | Removes a user from the blacklist |
| `/censor` | Deletes a specified number of messages from the text channel it was typed in |

### Fun
| Command | Description |
| - | - |
| `/pet` | Pets someone :3 |
| `/cat` | Shows a random picture or gif of a cat |
| `/dog` | Shows a random picture, gif or video of a dog |
| `/fact` | Shows a random useless fact |
| `/heads-or-tails` | Plays heads or tails |
| `/rps` | Plays Rock Paper Scissors |
| `/stickbug` | Nekobot's stickbug command |
| `/threats` | Nekobot's threats command |
| `/captcha` | Nekobot's captcha command |
| `/deepfry` | Nekobot's deepfry command |
| `/whowouldwin` | Nekobot's captcha command |

### Gemini
| Command | Description |
| - | - |
| `/gemini talk` | Starts or continues a conversation with Google's Gemini |
| `/gemini reset` | Resets your conversation with Gemini |

### Music
| Command | Description |
| - | - |
| `/play` | Plays tracks from various sources on a voice channel |
| `/queue show` | Shows the current song queue |
| `/queue clear` | Clears tracks from the current song queue |
| `/queue shuffle` | Shuffles the current queue |
| `/recommend` | Toggles the autoplay of recommended tracks on and off |
| `/nightcore` | Toggles a nightcore effect on and off |
| `/controls` | Shows the multimedia controls |
| `/favourite tracks show` | Shows your favourite tracks |
| `/favourite tracks add` | Adds a track to your favourite tracks |
| `/favourite tracks edit` | Shows your favourite tracks and allows you to choose and remove them |
| `/favourite tracks play` | Plays one or more of your favourite tracks |
| `/favourite playlists show` | Shows your favourite playlists |
| `/favourite playlists add` | Adds a playlist to your favourite playlists |
| `/favourite playlists edit` | Shows your favourite playlists and allows you to choose and remove them |
| `/favourite playlists play` | Plays one or more of your favourite playlists |

## NOTE: In order to use track sources like spotify, deezer, etc, make sure to open the "application.yml" lavalink config file and setup LavaSrc properly, by default RinBot does not provide any access tokens for those sources for obvious reasons. If you leave everything untouched, only Youtube, YoutubeMusic and SoundCloud will work.

### Economy
| Command | Description |
| - | - |
| `/orange rank` | Shows the top 10 members with the most oranges |
| `/orange transfer` | Transfer oranges between users |
| `/orange store show` | Shows the items on the store |
| `/orange store create-item` | Creates and adds an item to the store |
| `/orange store buy` | Buys an item from the store (by name) |

### TTS
| Command | Description |
| - | - |
| `/tts connect` | Connects a TTS instance to your channel |
| `/tts disconnect` | Disconnects the TTS instance from your channel |

### Fortnite
| Command | Description |
| - | - |
| `/fortnite daily-shop` | Shows the fortnite daily shop on the channel |
| `/fortnite stats` | Shows your fortnite account statistics on the channel |

### Booru
| Command | Description |
| - | - |
| `/booru random` | Shows an image or gif from danbooru with your given tags |

## NOTE: In order to use Danbooru, the user has to configure it properly through the .env file, by changing the "BOORU_ENABLE" flag from False to True, and adding their username and API key.

## NOTE 2: If you have a "Gold" danbooru account, make sure to change the "BOORU_IS_GOLD" flag inside .env from False to True, so you can take advantage of your 6 max tags search.

### Rule34
| Command | Description |
| - | - |
| `/rule34 random` | Shows an image or gif from rule34 with your given tags |
| `/rule34 i-came` | Shows the top 10 characters on rule34's i came list |

## NOTE: Due to the nature of Rule34 and Danbooru, their functionallity are disabled by default, in order to use them, an owner of the bot must change the "ENABLE_LEWD" flag inside the /rinbot/config/client/rin.json config file from False to True

## Ok, cool! How do I host my own instance of RinBot?
#### It's easy:
- Download and install python and java. (check required versions above)
- Download the latest release or clone this repository.
- Open a command line inside RinBot's directory and run `pip install -r requirements.txt` or create a venv and do the same.
- Run the `init.py` file and follow the start-up instructions.
