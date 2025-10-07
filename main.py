# -*- coding: utf-8 -*-
import os, random, time, sys, pathlib
from datetime import datetime, time as dtime
from dateutil import tz
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

USERNAME = os.getenv("X_USERNAME")
PASSWORD = os.getenv("X_PASSWORD")

AUTH_DIR = pathlib.Path(".auth"); AUTH_DIR.mkdir(exist_ok=True)
AUTH_STATE = str(AUTH_DIR / "state.json")

# --- Réglages ---
ARTISTS_NFT = ["artistNFT1", "artistNFT2", "artistNFT3"]   # sans @
ARTISTS_NONNFT = ["artist1", "artist2", "artist3"]
PICTNART_PROMOS = [
    "Discover our partner Pictnart for creative support and artistic growth 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
    "Looking for motivation in your art journey? 🌟 Check out our partner Pictnart 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
    "Elevate your craft with the help of our partner Pictnart 🎨 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
]

# Probabilités/paramètres globaux (hors créneau 19–22h)
P_ARTISTS = 0.70
P_PROMO   = 0.0025
RANDOM_WAIT = (0.6, 1.4)
MAX_LIKES_TIMELINE = (3, 8)       # likes aléatoires sur la timeline
MAX_LIKES_PROFILE  = (2, 4)       # likes quand on visite un artiste

def human_pause(a=RANDOM_WAIT[0], b=RANDOM_WAIT[1]):
    time.sleep(random.uniform(a, b))

def snap(page, label="snap"):
    try:
        page.screenshot(path=f"{label}.png", full_page=True)
        print(f"[DEBUG] screenshot saved: {label}.png")
    except Exception as e:
        print(f"[DEBUG] screenshot failed: {e}")

# ------------------------- Helpers UI ----------------------------------------
def accept_cookies(page):
    selectors = [
        'button:has-text("Accept all")', 'button:has-text("Accept all cookies")',
        'button:has-text("Allow all cookies")', 'div[role="button"]:has-text("Accept")',
        'button:has-text("Tout accepter")', 'button:has-text("Accepter")',
        'div[role="button"]:has-text("Tout accepter")', 'div[role="button"]:has-text("Accepter")',
    ]
    for sel in selectors:
        try:
            if page.is_visible(sel):
                page.click(sel, delay=random.randint(40,100))
                human_pause()
                print("[INFO] Cookies accepted with:", sel)
                return
        except:
            continue

def ensure_logged_in(page):
    print("[INFO] Ensuring session is logged in…")
    page.goto("https://x.com/home", wait_until="domcontentloaded")
    accept_cookies(page)
    if page.url.startswith("https://x.com/i/flow/login") or "login" in page.url:
        login(page)
    try:
        page.wait_for_selector('a[href="/home"], nav', timeout=15000)
    except PWTimeout:
        page.goto("https://x.com/home", wait_until="domcontentloaded")

def go_to_composer(page):
    print("[INFO] Opening composer…")
    page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded")
    accept_cookies(page)
    page.wait_for_selector('div[role="textbox"], div[data-testid="tweetTextarea_0"], textarea', timeout=30000)
    print("[OK] Composer is ready.")

# --------------------------- Login -------------------------------------------
def login(page):
    print("[INFO] Navigating to login flow…")
    page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
    accept_cookies(page)

    print("[INFO] Filling username/email…")
    page.wait_for_selector('input[name="text"]', timeout=30000)
    page.fill('input[name="text"]', USERNAME)
    human_pause()
    page.keyboard.press("Enter")

    try:
        page.wait_for_selector('input[name="text"]', timeout=4000)
        if page.is_visible('input[name="text"]'):
            print("[INFO] Extra identifier prompt detected. Refilling…")
            page.fill('input[name="text"]', USERNAME)
            human_pause()
            page.keyboard.press("Enter")
    except PWTimeout:
        pass

    print("[INFO] Filling password…")
    page.wait_for_selector('input[name="password"]', timeout=30000)
    page.fill('input[name="password"]', PASSWORD)
    human_pause()
    page.keyboard.press("Enter")
    human_pause()

    for sel in [
        'div[data-testid="LoginForm_Login_Button"]',
        'div[role="button"]:has-text("Log in")',
        'div[role="button"]:has-text("Se connecter")'
    ]:
        try:
            if page.is_visible(sel):
                page.click(sel)
                human_pause()
                break
        except:
            continue

    print("[INFO] Waiting for home UI…")
    try:
        page.wait_for_selector('a[href="/home"], nav', timeout=30000)
    except PWTimeout:
        page.goto("https://x.com/home", wait_until="domcontentloaded")

    print("[OK] Logged in.")
    snap(page, "after_login")

# ------------------------ Post / RT / Quote ----------------------------------
def post_text(page, text):
    go_to_composer(page)
    for sel in ['div[role="textbox"]', 'div[data-testid="tweetTextarea_0"]', 'textarea']:
        try:
            if page.is_visible(sel):
                page.fill(sel, text)
                break
        except:
            continue
    human_pause()
    for sel in ['div[data-testid="tweetButtonInline"]',
                'div[role="button"]:has-text("Post")',
                'div[role="button"]:has-text("Tweeter")']:
        try:
            if page.is_visible(sel):
                page.click(sel)
                human_pause(1.2, 2.2)
                print("[OK] Text posted.")
                return
        except:
            continue
    raise RuntimeError("Could not find send button in composer.")

def retweet_latest(page, handle_without_at):
    h = handle_without_at.lstrip("@")
    print(f"[INFO] Visiting profile @{h}…")
    page.goto(f"https://x.com/{h}", wait_until="domcontentloaded")
    accept_cookies(page)
    page.wait_for_selector('article', timeout=30000)
    human_pause()
    try:
        page.click('article div[data-testid="retweet"]', delay=random.randint(60, 140))
    except:
        try:
            page.click('article div[data-testid="caret"]', delay=random.randint(60, 140))
        except:
            page.click('article div[data-testid="share"]', delay=random.randint(60, 140))
    human_pause()
    page.click('div[role="menuitem"]:has-text("Retweet"), div[role="menuitem"]:has-text("Retweeter")')
    human_pause(1.2, 2.2)
    print("[OK] Retweet done.")

def quote_retweet(page, handle_without_at, comment):
    h = handle_without_at.lstrip("@")
    print(f"[INFO] Quote-RT @{h}…")
    page.goto(f"https://x.com/{h}", wait_until="domcontentloaded")
    accept_cookies(page)
    page.wait_for_selector('article', timeout=30000)
    page.click('article div[data-testid="retweet"]', delay=random.randint(60,140))
    human_pause()
    page.click('div[role="menuitem"]:has-text("Quote"), div[role="menuitem"]:has-text("Citer")')
    human_pause()
    post_text(page, comment)

def post_pictnart_promo(page):
    post_text(page, random.choice(PICTNART_PROMOS))

def post_loufis(page):
    try:
        retweet_latest(page, "loufisart")
    except Exception as e:
        print(f"[WARN] RT loufisart failed: {e}")
        post_text(page, "A new piece from @loufisart — dive into the world of Loufi’s Art ✨")

# ----------------------------- LIKE ENGINE -----------------------------------
def like_visible_tweets(page, max_likes):
    """
    Like des tweets visibles dans la timeline / une page profil.
    max_likes : nombre maximum de likes à tenter (quelques uns seulement).
    """
    print(f"[INFO] Liking up to {max_likes} tweets on current view…")
    likes_done = 0
    try:
        page.wait_for_selector('article', timeout=8000)
    except PWTimeout:
        return 0

    # On scrolle un peu pour varier
    for _ in range(random.randint(1,3)):
        page.mouse.wheel(0, random.randint(600, 1200))
        human_pause(0.8, 1.6)

    buttons = page.query_selector_all('article div[data-testid="like"]')
    random.shuffle(buttons)
    for btn in buttons:
        try:
            # éviter de spammer : léger hasard + limite
            if random.random() < 0.7:
                btn.click(delay=random.randint(30, 90))
                likes_done += 1
                human_pause(0.6, 1.2)
                if likes_done >= max_likes:
                    break
        except:
            continue
    print(f"[OK] Likes done: {likes_done}")
    return likes_done

def like_timeline(page):
    # Aller sur home et liker quelques tweets
    page.goto("https://x.com/home", wait_until="domcontentloaded")
    accept_cookies(page)
    return like_visible_tweets(page, random.randint(*MAX_LIKES_TIMELINE))

def like_from_profile(page, handle_without_at):
    h = handle_without_at.lstrip("@")
    page.goto(f"https://x.com/{h}", wait_until="domcontentloaded")
    accept_cookies(page)
    return like_visible_tweets(page, random.randint(*MAX_LIKES_PROFILE))

# ------------------- IMAGE DETECTION + RT IMAGE ------------------------------
def retweet_first_image_from_current_view(page):
    """
    Cherche le premier article avec image visible et le retweet.
    Renvoie True si RT effectué.
    """
    print("[INFO] Searching an image tweet on current view…")
    try:
        page.wait_for_selector('article', timeout=8000)
    except PWTimeout:
        return False

    articles = page.query_selector_all('article')
    for art in articles:
        try:
            # Heuristiques d'image
            has_img = (
                art.query_selector('div[data-testid="tweetPhoto"]') or
                art.query_selector('img[alt][draggable="true"]') or
                art.query_selector('a[href*="/photo/"]')
            )
            if not has_img:
                continue
            # Retweet menu
            rt_btn = art.query_selector('div[data-testid="retweet"]') or \
                     art.query_selector('div[data-testid="share"]') or \
                     art.query_selector('div[data-testid="caret"]')
            if not rt_btn:
                continue
            rt_btn.click(delay=random.randint(60,140))
            human_pause()
            menu_item = page.query_selector('div[role="menuitem"]:has-text("Retweet"), div[role="menuitem"]:has-text("Retweeter")')
            if menu_item:
                menu_item.click()
                human_pause(1.1, 1.9)
                print("[OK] Retweeted an image tweet.")
                return True
        except:
            continue
    print("[INFO] No image tweet found on current view.")
    return False

def retweet_image_from_handle(page, handle_without_at):
    """
    Essaie d’ouvrir le profil et RT le premier tweet image.
    Essaie sinon via la recherche 'from:<handle> filter:images'.
    """
    h = handle_without_at.lstrip("@")
    print(f"[INFO] Trying image RT from @{h} profile…")
    page.goto(f"https://x.com/{h}", wait_until="domcontentloaded")
    accept_cookies(page)
    if retweet_first_image_from_current_view(page):
        return True

    # fallback: recherche “from:<handle> filter:images”
    q = f"from%3A{h}%20filter%3Aimages"
    search_url = f"https://x.com/search?q={q}&f=live"
    print(f"[INFO] Fallback search for images: {search_url}")
    page.goto(search_url, wait_until="domcontentloaded")
    accept_cookies(page)
    return retweet_first_image_from_current_view(page)

# --------------------------- Logique métier -----------------------------------
def post_artists(page):
    lst = ARTISTS_NFT if random.random() < 0.5 else ARTISTS_NONNFT
    random.shuffle(lst)
    for h in lst:
        try:
            # 30%: Quote RT avec un petit com
            if random.random() < 0.3:
                quote_retweet(page, h, random.choice([
                    "Stunning piece ✨", "Love this style.", "Great composition!", "Texture goals."
                ]))
            else:
                retweet_latest(page, h)
            # Like quelques posts chez l’artiste
            like_from_profile(page, h)
            return
        except Exception as e:
            print(f"[WARN] Artist action failed for {h}: {e}")
            continue
    post_text(page, "Discover inspiring art today ✨ #art #inspiration")

def evening_window_brussels(now_dt):
    """True si entre 19:00 et 22:00 (inclus début, exclus fin) Europe/Brussels."""
    t = now_dt.timedefault if hasattr(now_dt, 'timedefault') else None
    start = dtime(19, 0)
    end   = dtime(22, 0)
    cur   = now_dt.time()
    return (cur >= start) and (cur < end)

def evening_routine(page):
    """
    Routine forcée 19–22h:
      1) RT loufisart (ou fallback post)
      2) RT au moins 1 tweet image d'un autre utilisateur (liste artistes)
      3) liker un peu la timeline
    """
    print("[INFO] Evening routine (19–22h)…")
    post_loufis(page)

    # RT image d’un autre utilisateur (pas Loufisart)
    pool = list(set(ARTISTS_NFT + ARTISTS_NONNFT))
    random.shuffle(pool)
    success = False
    for h in pool:
        if h.lower() in ["loufisart", "@loufisart"]:
            continue
        try:
            if retweet_image_from_handle(page, h):
                success = True
                # like sur le profil juste après
                like_from_profile(page, h)
                break
        except Exception as e:
            print(f"[WARN] Image RT failed for {h}: {e}")
            continue

    if not success:
        print("[WARN] Could not find image tweet to RT; trying timeline search as last resort.")
        page.goto("https://x.com/home", wait_until="domcontentloaded")
        accept_cookies(page)
        retweet_first_image_from_current_view(page)

    # toujours quelques likes en fin de routine
    like_timeline(page)

def casual_routine(page):
    """
    Routine en dehors du créneau 19–22h :
      - qq likes timeline (toujours)
      - 3% run humain: rien
      - sinon P_PROMO > P_ARTISTS > loufis
    """
    # likes d'abord pour paraître humain
    like_timeline(page)

    if random.random() < 0.03:
        print("[OK] Human-like skip (no post this run).")
        return

    roll = random.random()
    if roll < P_PROMO:
        post_pictnart_promo(page)
        print("[OK] Posted Pictnart promo.")
    elif roll < P_PROMO + P_ARTISTS:
        post_artists(page)
        print("[OK] Posted artist RT/text.")
    else:
        post_loufis(page)
        print("[OK] Posted loufis RT/text.")

# ------------------------------ Main -----------------------------------------
def main():
    brussels = tz.gettz("Europe/Brussels")
    now = datetime.utcnow().replace(tzinfo=tz.UTC).astimezone(brussels)
    print(f"[ArtLift] Run at {now.isoformat()}")

    if not USERNAME or not PASSWORD:
        print("ERROR: Missing X_USERNAME or X_PASSWORD env vars.", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as p:
        def launch_chromium():
            return p.chromium.launch(headless=True)
        try:
            browser = launch_chromium()
        except Exception as e:
            print(f"[WARN] Chromium not found, installing… ({e})")
            import subprocess
            subprocess.run(
                ["python", "-m", "playwright", "install", "chromium", "--with-deps"],
                check=False
            )
            browser = launch_chromium()

        context_kwargs = dict(
            locale="fr-FR",
            timezone_id="Europe/Brussels",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 850},
        )

        context = browser.new_context(**context_kwargs)
        context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()

        try:
            if os.path.exists(AUTH_STATE):
                print("[INFO] Loading saved auth state…")
                context.close()
                context = browser.new_context(storage_state=AUTH_STATE, **context_kwargs)
                context.tracing.start(screenshots=True, snapshots=True)
                page = context.new_page()
                page.goto("https://x.com/home", wait_until="domcontentloaded")
                accept_cookies(page)
                if page.url.startswith("https://x.com/i/flow/login") or "login" in page.url:
                    print("[INFO] Saved state invalid, logging in again…")
                    login(page)
                    context.storage_state(path=AUTH_STATE)
            else:
                login(page)
                context.storage_state(path=AUTH_STATE)

            # Variabilité humaine légère
            page.wait_for_timeout(random.randint(600, 1600))
            page.keyboard.press("PageDown")
            page.wait_for_timeout(random.randint(500, 1200))

            # --- ROUTINES ---
            if evening_window_brussels(now):
                evening_routine(page)
            else:
                casual_routine(page)

            snap(page, "after_actions")
            context.tracing.stop(path="trace.zip")
            browser.close()

        except Exception as e:
            print(f"[FATAL] {e}", file=sys.stderr)
            try:
                snap(page, "error")
                context.tracing.stop(path="trace.zip")
            except:
                pass
            try:
                browser.close()
            except:
                pass
            sys.exit(1)

if __name__ == "__main__":
    main()
