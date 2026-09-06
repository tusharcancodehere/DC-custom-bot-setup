# TODO

## Foundation

* [x] Create bot core
* [x] Load environment variables
* [x] Implement Discord client
* [x] Implement Cog loading
* [x] Implement slash command synchronization
* [x] Add global error handling
* [x] Add application logging
* [x] Add permission checks
* [x] Add common utilities
* [x] Add common Discord embeds/views

## Database

* [x] Configure PostgreSQL connection environment
* [x] Configure SQLAlchemy async engine and sessionmaker
* [x] Configure asyncpg driver support
* [x] Configure Alembic dependency
* [ ] Create initial database models
* [ ] Create migration workflow
* [ ] Add guild configuration model
* [ ] Add user model

## Admin

* [ ] Server information
* [ ] Channel management
* [ ] Role management
* [ ] Server configuration
* [ ] Announcement command
* [ ] Feature enable/disable system

## Moderation

* [x] Ban (`/ban`)
* [x] Unban (`/unban`)
* [x] Kick (`/kick`)
* [x] Timeout (`/timeout`)
* [x] Warn (`/warn`)
* [ ] Warning history
* [x] Purge messages (`/purge`)
* [ ] Lock channel
* [ ] Unlock channel
* [ ] Slowmode
* [ ] Moderation logging
* [ ] Basic automod
* [ ] Spam protection
* [ ] Invite/link filtering

## Welcome

* [x] Welcome message embed (`/welcome`)
* [ ] Leave message
* [ ] Welcome channel configuration
* [ ] Leave channel configuration
* [ ] Auto-role
* [x] Custom welcome messages (`embed.json`)
* [ ] Welcome image support
* [ ] `/welcome setup`
* [ ] `/welcome test`

## Tickets

* [ ] Ticket panel
* [ ] Create ticket button
* [ ] Close ticket button
* [ ] Claim ticket
* [ ] Add user
* [ ] Remove user
* [ ] Ticket categories
* [ ] Staff permissions
* [ ] Ticket configuration
* [ ] Ticket logging
* [ ] Ticket transcripts

## Level System

* [x] XP tracking (in-memory)
* [ ] XP cooldown
* [x] Level calculation
* [x] Rank card command (`/level`)
* [ ] Leaderboard
* [ ] Level-up messages
* [ ] Level rewards
* [ ] Role rewards
* [x] Level configuration (`embed.json`)

## Games

* [ ] Coin flip
* [ ] Dice roll
* [ ] Rock Paper Scissors
* [ ] 8 Ball
* [ ] Trivia
* [ ] Tic Tac Toe
* [ ] Connect Four
* [ ] Blackjack
* [ ] Game cooldowns
* [ ] Game statistics

## Music

* [x] Voice connection
* [x] Audio playback (yt-dlp + FFmpeg)
* [x] Play command (`/play`)
* [x] Pause (`/pause`)
* [x] Resume (`/resume`)
* [x] Skip (`/skip`)
* [x] Stop (`/stop`)
* [x] Queue (`/queue`)
* [x] 24/7 voice mode (`/247`)
* [x] Volume (`/volume`)
* [x] Now playing player view (`/player`)
* [x] Music error handling
* [x] Queue cleanup

## AI

* [x] OpenAI integration (`gpt-5-mini`)
* [x] Google Gemini fallback (`gemini-2.5-flash`)
* [x] AI command (`/ask`)
* [x] Conversation handling
* [x] Message/context handling
* [x] AI response limits
* [x] Error handling
* [x] AI configuration
* [x] Conversation history reset (`/clear`)
* [ ] AI moderation tools
* [ ] Ticket AI assistant

## Quality

* [ ] Add pytest tests
* [ ] Add Ruff configuration
* [ ] Add type checking
* [x] Improve logging
* [x] Add structured error messages
* [ ] Test database operations
* [ ] Test major feature logic

## Documentation

* [x] Complete README
* [x] Write CONTRIBUTING.md
* [x] Add CODE_OF_CONDUCT.md
* [x] Add SECURITY.md
* [x] Document environment variables
* [x] Document bot permissions
* [x] Document Discord intents
* [x] Document PostgreSQL setup (`docs/database.md`)
* [x] Document local development
* [x] Document feature development

## Deployment

* [ ] Create Dockerfile
* [ ] Create development Compose configuration
* [ ] PostgreSQL container configuration
* [ ] Production configuration
* [ ] Health checks
* [ ] Graceful shutdown
* [ ] Deployment documentation

## Future Features

* [ ] Economy
* [ ] Giveaways
* [ ] Polls
* [ ] Reminders
* [ ] Reaction roles
* [ ] Suggestions
* [ ] Starboard
* [ ] Custom commands
* [ ] Verification system
* [ ] Temporary voice channels
* [ ] Server statistics
* [ ] Advanced automod
* [ ] Web dashboard
* [ ] Public API

## Long-Term

* [ ] Improve scalability
* [ ] Evaluate Redis when needed
* [ ] Evaluate sharding when needed
* [ ] Improve monitoring
* [ ] Improve developer tooling
* [ ] Improve contributor experience
* [ ] Establish release/versioning process
