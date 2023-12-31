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
- Rule34 and Danbooru integration if you're into that.
- Integration with the fnbr Fortnite API

## Economy system
As of update 1.8, RinBot now has a economy system with oranges as the currency.
**The way it works is as follows:**
* Users will receive 500 oranges by default upon entering a server and being registered in the economy database.
* Users will be rewarded 25 oranges every 50 messages sent. `A anti-spam measure was applied to ensure this feature isn't abused.`
* Users can transfer oranges between eachother using the `/orange transfer` command.
* Users can see the top 10 users with the most oranges using the `/orange rank` command.
* Users can use their oranges to buy items from the shop using the `/orange store` and `/orange buy` command.
## NOTE: Currently only roles are supported by the orange store, more item types will be added in the future.

## User ID permission class system

It looks complicated, but it's easy to understand. RinBot has a "class" system composed of 3 classes, those are: **"Owners", "Admins", "Blacklisted"**.

The **"owners"** class are the ones to have absolute full control of the entire bot. They can reset it, shut it down, manipulate extensions, add/remove users from the admin class, and of course, they can use any commands. As soon as you run the `init.py` file, and it creates a fresh database, you will be prompted to add your discord ID to be set as the owner of the bot.

The **"admins"** class is meant for administrators / moderators of the server the bot is on. It provides access to commands of the "moderation" command cog, where they can blacklist users, manipulate warnings and use the `/censor` command. To add / remove users from this class, a user with admin priv on the server needs to use the `/admins set` command.

Users inside the **blacklisted** class are well... blacklisted from using ANY functionality of the bot. To add / remove users from this class, a user in the admins or owners class needs to use the `/blacklist` command.

## Commands

#### General
| Command | Description |
| - | - |
| `/help` | Shows a paged embed with all of rinbot's commands. |
| `/rininfo` | Shows information about the bot |
| `/specs` | Shows the specs. of the system running the bot |
| `/ping` | Pong! |
| `/translate` | Translates a text from one language to another using the "Translate" library |

#### Config
| Command | Description |
| - | - |
| `/set welcome-channel` | Sets a text channel on your server for RinBot to greet new members with a custom message |
| `/set fortnite-daily-shop-channel` | Sets a text channel on your server for RinBot to send the daily fortnite item shop (Updates everyday at 00:05 UTC) |
| `/toggle welcome-channel` | Toggles on and off the welcome channel functionality |
| `/toggle fortnite-daily-shop-channel` | Toggles on and off the fortnite daily shop functionality |
## NOTE: In order to use the fortnite daily shop function, a user must have a valid fnbr API Key configured on the .env file

#### Moderation
| Command | Description |
| - | - |
| `/censor` | Deletes a specified number of messages from the text channel it was typed in |
| `/admins add` | Adds a user to the admins class |
| `/admins remove` | Removes a user from the admins class |
| `/blacklist show` | Shows the users inside the blacklist (if any) |
| `/blacklist add` | Adds a user to the blacklist |
| `/blacklist remove` | Removes a user from the blacklist |
| `/warnings show` | Shows a user's warnings |
| `/warnings add` | Adds a warning to a user |
| `/warnings remove` | Removes a warning from a user by it's warn ID |

#### Owner
| Command | Description |
| - | - |
| `/shutdown` |  Shuts the bot down. |
| `/owners add` | Adds a user to the owners class |
| `/owners remove` | Removes a user from the owners class  |
| `/extension load` | Loads a bot extension |
| `/extension unload` | Unloads a bot extension |
| `/extension reload` | Reloads a bot extension |

#### Fun
| Command | Description |
| - | - |
| `/cat` | Shows a random picture or gif of a cat |
| `/dog` | Shows a random picture, gif or video of a dog |
| `/pet` | Pets someone :3 |
| `/fact` | Shows a random useless fact |
| `/heads-or-tails` |  Plays heads or tails |
| `/rps` |  Plays Rock Paper Scissors |

#### Music
| Command | Description |
| - | - |
| `/showcontrols` | Shows multimedia controls for current media player |
| `/play link` | Plays music through youtube links (single or list of links, playlists and shorts are supported) |
| `/play search` | Plays music from a youtube search query (you can select up to 25 search results) |
| `/play search_playlist` | Plays music from one or more selected playlists from a search query (you can select up to 25 playlists) |
| `/queue show` | Shows the current song queue |
| `/queue show url=Yes` | Same as **/queue show** but titles are switched for URLs |
| `/queue clear` | Clears the current song queue |
| `/queue clear id=?` | Clears a specific track from the song queue by their ID (number) |
| `/history show` | Shows the server's song history (last 25 played songs) |
| `/history show url=Yes` | Same as **/history show** but titles are switched for URLs |
| `/history clear` | Clears the server's song history |

#### Economy
| Command | Description |
| - | - |
| `/orange rank` |  Shows the top 10 members with the most oranges |
| `/orange transfer` |  Transfer oranges between users |
| `/orange store` |  Shows the items on the store |
| `/orange new_role` |  Adds a role item to be bought from the store |
| `/orange buy` |  Buys an item from the store (by name) |

#### Booru
| Command | Description |
| - | - |
| `/booru random` | Shows a random image from danbooru using the tags and rating given by the user |

## NOTE: In order to use Danbooru, the user has to configure it properly through the .env file, by changing the "BOORU_ENABLE" flag from False to True, and adding their username and API key.
## NOTE 2: If you have a "Gold" danbooru account, make sure to change the "BOORU_IS_GOLD" flag inside .env from False to True, so you can take advantage of your 6 max tags search.

#### Rule 34
| Command | Description |
| - | - |
| `/rule34 random` | Shows an image or gif from rule34 with your given tags |
| `/rule34 icame` | Shows the top 10 characters on rule34's i came list |

## NOTE: Due to the nature of Rule34, it's functionallity is disabled by default, in order to use Rule34, an owner of the bot must change the "RULE_34_ENABLED" flag inside the .env file from False to True

## AI (Kobold and StableDiffusion)
#### To integrate RinBot with your running instance of Kobold / StableDiffusion or both, follow these steps:
- Open `.env` and set the `use_ai` variable to `True` (this will make the bot load the necessary ai extensions located inside the `ai` folder)
- Still inside `.env`, change the `ENDPOINT` value to whatever URL:PORT you're using to access Kobold, the one already present is the default and should probably work if you're running the language model localy, same thing goes for stablediffusion, through the `STABLE_DIFFUSION_ENDPOINT` value.
- Next, copy the ID of a empty / new discord text chat from your server, and paste it on the `CHANNEL_ID` value. This will make the bot behave like a "chatGPT", but on your discord server!
- To use StableDiffusion, make sure to open the webui with the `-api` flag, or else the bot won't be able to use it

## Ok, cool! How do I host my own instance of RinBot?
#### It's easy:
- Download and install python
- Download the latest release or clone this repository
- Open a command line inside RinBot's directory and run `pip install -r requirements.txt`
- Add your discord bot token to the `.env` file
- Run the `init.py` file and follow the start-up instructions
