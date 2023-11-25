# Hello, I'm RinBot!

RinBot is a discord bot fully developed in Python using libraries such as `discord.py`.

She was private code a while back, but I decided to publish at least a "alternative" version of her on github, to work as a starting point for future bots, or for you to just tinker with it.

## Code overview

- Programmed with both Windows and Linux in mind.
- AI functionality with StableDiffusion for image generation and Kobold for chatbots built-in and ready to go.
- Rewarding and engaging economy system
- Command Cog based structure for easy debugging and 'on-the-fly' coding.
- Built-in logger with colors and categories.
- User ID tied command permission class system (explained below).
- User blacklisting to prevent undesired users to use the bot.
- "Warning" system, which automatically kicks users past a certain amount of warnings.
- SQL database to store important data.
- Server moderation tools such as the command `/censor` that clears a certain amount of messages in a text chat.
- YouTube music playback with search queries and support for playlists.
- Little games like "Rock, Paper Scissors" and "Heads or Tails".
- Rule34 integration if you're into that.

## Economy system
As of update 1.8, RinBot now has a economy system with oranges as the currency.
**The way it works is as follows:**
* Users will receive 500 oranges by default upon entering a server and being registered in the economy database.
* Users will be rewarded 25 oranges every 50 messages sent. `A anti-spam measure was applied to ensure this feature isn't abused.`
* Users can transfer oranges between eachother using the `/orange_transfer` command.
* Users can see the top 10 users with the most oranges using the `/orange_rank` command.
* Users can use their oranges to buy items from the shop using the `/orange_store` and `/orange_buy` command.
## NOTE: Currently only roles are supported by the orange store, more item types will be added in the future.

## User ID permission class system

It looks complicated, but it's easy to understand. RinBot has a "class" system composed of 3 classes, those are: **"Owners", "Admins", "Blacklisted"**.

The **"owners"** class are the ones to have absolute full control of the entire bot. They can reset it, shut it down, manipulate extensions, add/remove users from the admin class, and of course, they can use any commands. As soon as you run the `init.py` file, and it creates a fresh database, you will be prompted to add your discord ID to be set as the owner of the bot.

The **"admins"** class is meant for administrators / moderators of the server the bot is on. It provides access to commands of the "moderation" command cog, where they can blacklist users, manipulate warnings and use the `/censor` command. To add / remove users from this class, a user in the "owners" class needs to use the `/admins` command.

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
| `/censor`| Deletes a specified number of messages from the text channel it was typed in |
| `/admins` | Manipulates (adds / removes) users from the admins class |
| `/blacklist` | Manipulates (adds / removes / shows) users from the blacklisted class |
| `/warning` | Manipulates (adds / removes / shows) user warnings |
| `/nickname` | Changes the server nickname of a member |
| `/kick` | Kicks a server member |
| `/ban` | Bans a server member |

#### Owner Cog
| Command | Description |
| - | - |
| `/extension`| Manipulates (loads / unloads / reloads) command cogs (extensions) |
| `/reset` | Starts a new instance of the bot by executing the `init.py` script using the subprocess library, and then killing the original instance |
| `/shutdown` | Shuts the bot down. |
| `/owners` | Manipulates (adds / removes) users from the owners class |

#### Fun Cog
| Command | Description |
| - | - |
| `/cat`| Shows a random picture of a cat |
| `/dog`| Shows a random picture of a dog |
| `/ocr`| Reads text from an image attachment and sends back the result |
| `/meme`| Memes on someone's last message |
| `/pet`| Pets someone :3 |
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
| `/showplaylist` | Shows a list of songs from a given playlist |
| `/playlists` | Manipulates (adds / removes / clears) your individual list of favourite playlists |

#### Economy Cog
| Command | Description |
| - | - |
| `/orange_rank` | Shows the top 10 members with the most oranges |
| `/orange_transfer` | Transfer oranges between users |
| `/orange_store` | Shows the items on the store |
| `/orange_new_role` | Adds a role item to be bought from the store |
| `/orange_buy` | Buys an item from the store (by name) |

#### StableDiffusion Cog
| Command | Description |
| - | - |
| `/generateimage`| Generates an image using AI through a StableDiffusion instance ("masterpiece, best quality") are already included on the positive prompt, so you can omit those |

#### Booru Cog
| Command | Description |
| - | - |
| `/booru-random` | Shows a random image from danbooru using the tags and rating given by the user |

## NOTE: In order to use Danbooru, the user has to configure it properly through the .env file, by changing the "BOORU_ENABLE" flag from False to True, and adding their username and API key.
## NOTE 2: If you have a "Gold" danbooru account, make sure to change the "BOORU_IS_GOLD" flag inside .env from False to True, so you can take advantage of your 6 max tags search.

#### Rule 34 Cog
| Command | Description |
| - | - |
| `/rule34-random` | Shows an image or gif from rule34 with your given tags |
| `/rule34-icame` | Shows the top 10 characters on rule34's i came list |

## NOTE: Due to the nature of Rule34, it's functionallity is disabled by default, in order to use Rule34, an owner of the bot must change the "RULE_34_ENABLED" flag inside the .env file from False to True

## AI (Kobold and StableDiffusion)
#### To integrate RinBot with your running instance of Kobold / StableDiffusion or both, follow these steps:
- Open `.env` and set the `use_ai` variable to `True` (this will make the bot load the necessary ai extensions located inside the `ai` folder)
- Still inside `.env`, change the `ENDPOINT` value to whatever URL:PORT you're using to access Kobold, the one already present is the default and should probably work if you're running the language model localy, same thing goes for stablediffusion, through the `STABLE_DIFFUSION_ENDPOINT` value.
- Next, copy the ID of a empty / new discord text chat from your server, and paste it on the `CHANNEL_ID` value. This will make the bot behave like a "chatGPT", but on your discord server!
- To use StableDiffusion, make sure to open the webui with the `-api` flag, or else the bot won't be able to use it

## Ok, cool! How do I host my own instance of RinBot?
#### It's easy:
- Download the latest release or clone this repository
- Download and install python
- Open a command line inside RinBot's directory and run `pip install -r requirements.txt`
- Add your discord bot token to the `.env` file
- Run the `init.py` file
