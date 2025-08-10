I'm making a New Game and Set myself these rules

I must Use Python and its full Compatibilities
and I can only use AI
(Yes With the New GPT 5 I've set myself to the challenge and use it to see how far it can go and how much it will take my job)
The game will be about stealing a Tesco Van so if you want any suggestions to the game Let me Know

This will be incredibly funny 😭 (This game is for My older brother Who loves Tescos :sob:)
So Here it is
# Tesco - Alex's Grand Adventure — Pixel Runner (single-file Python game)

**Van Snatcher v2** is a small pixel-art endless runner with a top-down theft intro.
Everything is contained in a single Python file (`van_snatcher_v2.py`) that procedurally
generates pixel sprites, handles login/signup with a local `users.json`, and saves progress.

## Requirements
- Python 3.8+
- Pillow (required): `pip install pillow`
- Optional: pygame for better audio: `pip install pygame`
- Run: `python van_snatcher_v2.py`

## Controls
- Arrow keys or A/D / ← → : move left / right (in both phases)
- W/S / ↑ ↓ : move up / down (Phase 1 top-down)
- SPACE : sprint in Phase 1 (consumes stamina)
- ESC : return to menu / pause
- Click UI buttons with mouse

## Gameplay
1. **Login / Sign-up** — create account; passwords are hashed locally.
2. **Main Menu** — Play, Shop, Log out, Quit.
3. **Phase 1 (Top-down)** — Move Alex around the map, avoid Tesco workers and steal the van on the right.
4. **Phase 2 (Runner)** — After stealing the van, the game becomes an infinite runner. Move between lanes to avoid obstacles (workers, cones, crates) and collect coins. Speed increases over time.
5. **Shop** — buy cosmetics (Alex outfits, van skins) and upgrades (sneakers, mask, wallet x2). Purchases persist to your account.
6. **Score & Coins** — coins & highscore are saved to your account. "Wallet x2" doubles coin pickups.

## Files
- `van_snatcher_v2.py` — main game script (single file).
- `users.json` — created automatically when you sign up; stores users and their progress.
- 'Tesco.png" - Tesco Image
## Tips & Notes
- The game generates pixel sprites at run-time; it may take a small moment on first launch.
- If you want richer sound, install `pygame`. If not available, the script will fallback gracefully.
- Cosmetic items are purely visual; upgrades affect gameplay as described.
- To logout and switch user, use "Log out" in the main menu. Remaining signed-in persists until you logout.

## Future ideas
- More cosmetic items (hats, stickers, wheel types).
- Animated coin FX and particle trails.
- Save slots and cloud sync.
- Levels / daily challenges.

Enjoy! This game is for entertainment — do not replicate or enact any real-life wrongdoing.
(THIS IS ALL MADE BY AI NOT ME THIS IS MADE TO TEST THE POWER OF GPT 5)
