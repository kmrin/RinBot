# Hello, I'm RinBot!

RinBot is a discord bot fully developed in Python using libraries such as `discord.py`.

She was private code a while back, but I decided to publish at least a "alternative" version of her on github, to work as a starting point for future bots, or for you to just tinker with it.

## Code overview

- Programmed with both Windows and Linux in mind.
- AI functionality with StableDiffusion for image generation and Kobold for chatbots built-in and ready to go.
- Command Cog based structure for easy debugging and 'on-the-fly' coding.
- Built-in logger with colors and categories.
- User ID tied command permission class system (explained below).
- User blacklisting to prevent undesired users to use the bot.
- "Warning" system, which will be integrated with the blacklist in the future.
- SQL database to store class information.
- Server moderation tools such as the command `/sensor` that clears a certain amount of messages in a text chat.
- YouTube music playback with search queries and support for playlists.
- Little games like "Rock, Paper Scissors" and "Heads or Tails".

## User ID permission class system

It looks complicated, but it's easy to understand. RinBot has a "class" system composed of 3 classes, those are: **"Owners", "Admins", "Blacklisted"**.

The **"owners"** class are the ones to have absolute full control of the entire bot. They can reset it, shut it down, manipulate extensions, add/remove users from the admin class, and of course, they can use any commands. Unlike admins and blacklisted, the users inside the owners class are not defined inside the SQL database, but on the `config.json` file located on the root folder of the bot, on the `owners` list. To add a user to the owners class, simply grab their discord user ID *(you can google that if you don't know how to do it)* and insert it on the list, as a string.

#### For example:

```json
  "owners": [
      "1234567890",
      "0987654321"
   ]
```

The **"admins"** class is meant for administrators / moderators of the server the bot is on. It provides access to commands of the "moderation" command cog, where they can blacklist users, manipulate warnings and use the `/sensor` command. To add / remove users from this class, a user in the "owners" class needs to use the `/admins` command. The data for the admins class is stored on the bot's SQL database.

Users inside the **blacklisted** class are well... blacklisted from using ANY functionality of the bot. To add / remove users from this class, a user in the admins or owners class needs to use the `/blacklist` command.
## Commands

#### General Cog
| Command | Description |
| - | - |
| `/translate`| Translates a text from one language to another using the "Translate" library |
| `/rininfo` | Shows information about the bot |
| `/serverinfo` | Shows information about the server |
| `/ping` | Pong! |


#### Moderation Cog
| Command | Description |
| - | - |
| `/sensor`| Deletes a specified number of messages from the text channel it was typed in |
| `/admins` | Manipulates (adds / removes) users from the admins class |
| `/blacklist` | Manipulates (adds / removes / shows) users from the blacklisted class |
| `/warning` | Manipulates (adds / removes / shows) user warnings |

#### Owner Cog
| Command | Description |
| - | - |
| `/extension`| Manipulates (loads / unloads / reloads) command cogs (extensions) |
| `/reset` | Starts a new instance of the bot by executing the `init.py` script using the subprocess library, and then killing the original instance |
| `/shutdown` | Shuts the bot down. |

#### Fun Cog
| Command | Description |
| - | - |
| `/fact`| Shows a random useless fact |
| `/heads-or-tails` | Plays heads or tails |
| `/rps` | Plays Rock Paper Scissors |

#### Music Cog
| Command | Description |
| - | - |
| `/play`| Connects to your voice-channel and starts playing songs from youtube through a given link, search query, or playlist (disconnects after 2 seconds of innactivity) |
| `/queue` | Allows you to view or manipulate the current song queue |
| `/history` | Allows you to view or manipulate the song history (stores the last 50 played songs) |
| `/cancelplaylist` | Stops the current playlist from continuing |
| `/showcontrols` | Shows the multimedia control buttons (useful if the original ones are too far up on the text channel, that's why I made it :p) |

#### StableDiffusion Cog
| Command | Description |
| - | - |
| `/generateimage`| Generates an image using AI through a StableDiffusion instance ("masterpiece, best quality") are already included on the positive prompt, so you can omit those |

## AI (Kobold and StableDiffusion)
#### To integrate RinBot with your running instance of Kobold / StableDiffusion or both, follow these steps:
- Open `config.json` and set the `use_ai` variable to `true` (this will make the bot load the necessary ai extensions located inside the `ai` folder)
- Open `.env` and place your discord bot token, next, change the `ENDPOINT` value to whatever URL:PORT you're using to access Kobold, the one already present is the default and should probably work if you're running the language model localy
- Next, copy the ID of a empty / new discord text chat from your server, and paste it on the `CHANNEL_ID` value. This will make the bot behave like a "chatGPT", but on your discord server!
- To use StableDiffusion, make sure to open the webui with the `-api` flag, or else the bot won't be able to use it
- If StableDiffusion doesn't work, check the `url` variable inside `ai/stablediffusion.py` in line 15 and change it accordingly

### NOTE: `stablediffusion.py` is configured to use "EasyNegativesV2" by default, if you don't have it, get it, insert your own default negative prompt on the code

## Ok, cool! How do I host my own instance of RinBot?
#### It's easy:
- Download this repository
- Download and install python
- Open a command line inside RinBot's directory and run `pip install -r requirements.txt`
- Open the `config.json` file and insert your discord bot token
- On the same file, add your discord user ID to the `owners` list as shown above in this readme
- Run the `init.py` file