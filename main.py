import os, random, time, sys
from datetime import datetime
from dateutil import tz
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

USERNAME = os.getenv("X_USERNAME")  # email/username du compte bot
PASSWORD = os.getenv("X_PASSWORD")  # mot de passe du compte bot

# ------------ Réglages / listes à personnaliser ------------
ARTISTS_NFT = ["artistNFT1", "artistNFT2", "artistNFT3"]     # handles SANS @
ARTISTS_NONNFT = ["artist1", "artist2", "artist3"]           # handles SANS @
P_ARTISTS = 0.70    # ≈ 70% RT artistes
P_PROMO   = 0.0025  # ≈ 2–3 promos/mois (avec 15 runs/jour)
RANDOM_WAIT = (0.6, 1.4)  # petites pauses "humaines"

PICTNART_PROMOS = [
    "Discover our partner Pictnart for creative support and artistic growth 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
    "Looking for motivation in your art journey? 🌟 Check out our partner Pictnart 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
    "Elevate your craft with the help of our partner Pictnart 🎨 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
]
# -----------------------------------------------------------

def human_pause(a=RANDOM_WAIT[0], b=RANDOM_WAIT[1]):
    time.sleep(random.uniform(a, b))

def snap(page, label="snap"):
    try:
        page.screenshot(path=f"{label}.png", full_page=True)
        print(f"[DEBUG] screenshot saved: {label}.png")
    except Exception as e:
        print(f"[DEBUG] screenshot failed: {e}")

def login(page):
    # Flow de login plus stable
    page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")

    # 1) Champ "Phone, email, or username"
    page.wait_for_selector('input[name="text"]', timeout=30000)
    page.fill('input[name="text"]', USERNAME)
    human_pause()
    page.keyboard.press("Enter")  # plus robuste que cliquer "Next"

    # 1bis) Parfois X redemande un identifiant (challenge)
    try:
        page.wait_for_selector('input[name="text"]', timeout=4000)
        if page.is_visible('input[name="text"]'):
            page.fill('input[name="text"]', USERNAME)
            human_pause()
            page.keyboard.press("Enter")
    except PWTimeout:
        pass

    # 2) Password
    page.wait_for_selector('input[name="password"]', timeout=30000)
    page.fill('input[name="password"]', PASSWORD)
    human_pause()
    # Soumission: Enter d'abord
    try:
        page.keyboard.press("Enter")
    except:
        pass
    human_pause()

    # Fallback si nécessaire (boutons localisés)
    if page.is_visible('div[data-testid="LoginForm_Login_Button"]'):
        page.click('div[data-testid="LoginForm_Login_Button"]')
    elif page.is_visible('div[role="button"]:has-text("Log in")'):
        page.click('div[role="button"]:has-text("Log in")')
    elif page.is_visible('div[role="button"]:has-text("Se connecter")'):
        page.click('div[role="button"]:has-text("Se connecter")')

    # 3) Attendre l'arrivée sur la timeline/éditeur
    page.wait_for_selector(
        'div[aria-label="Post"], div[data-testid="tweetTextarea_0"], div[role="textbox"]',
        timeout=30000
    )

def post_text(page, text):
    # Ouvrir l'éditeur
    if page.is_visible('div[aria-label="Post"]'):
        page.click('div[aria-label="Post"]')
    else:
        try:
            page.click('div[data-testid="tweetTextarea_0"]')
        except:
            page.click('div[role="textbox"]')
    human_pause()

    # Saisir le texte (plusieurs sélecteurs possibles)
    if page.is_visible('div[aria-label="Post text"]'):
        page.fill('div[aria-label="Post text"]', text)
    else:
        page.fill('div[role="textbox"][data-testid="tweetTextarea_0"], div[role="textbox"]', text)
    human_pause()

    # Bouton pour envoyer
    if page.is_visible('div[data-testid="tweetButtonInline"]'):
        page.click('div[data-testid="tweetButtonInline"]')
    else:
        page.click('div[role="button"]:has-text("Post"), div[role="button"]:has-text("Tweeter")')

    human_pause(1.2, 2.2)

def retweet_latest(page, handle_without_at):
    h = handle_without_at.lstrip("@")
    page.goto(f"https://x.com/{h}", wait_until="domcontentloaded")
    page.wait_for_selector('article', timeout=30000)
    human_pause()

    # Essayer le bouton retweet direct
    try:
        page.click('article div[data-testid="retweet"]', delay=random.randint(60, 140))
    except:
        # Fallback: ouvrir un menu (caret) si présent
        try:
            page.click('article div[data-testid="caret"]', delay=random.randint(60, 140))
        except:
            # Dernier recours: ouvrir le menu "share"
            page.click('article div[data-testid="share"]', delay=random.randint(60, 140))
    human_pause()

    # Confirmer le retweet (FR/EN)
    page.click('div[role="menuitem"]:has-text("Retweet"), div[role="menuitem"]:has-text("Retweeter")')
    human_pause(1.2, 2.2)

def post_pictnart_promo(page):
    post_text(page, random.choice(PICTNART_PROMOS))

def post_loufis(page):
    # RT @loufisart sinon fallback texte
    try:
        retweet_latest(page, "loufisart")
    except Exception as e:
        print(f"[WARN] RT loufisart failed: {e}")
        post_text(page, "A new piece from @loufisart — dive into the world of Loufi’s Art ✨")

def post_artists(page):
    lst = ARTISTS_NFT if random.random() < 0.5 else ARTISTS_NONNFT
    random.shuffle(lst)
    for h in lst:
        try:
            retweet_latest(page, h)
            return
        except Exception as e:
            print(f"[WARN] RT {h} failed: {e}")
            continue
    # Si rien trouvé
    post_text(page, "Discover inspiring art today ✨ #art #inspiration")

def main():
    brussels = tz.gettz("Europe/Brussels")
    now = datetime.utcnow().replace(tzinfo=tz.UTC).astimezone(brussels)
    print(f"[ArtLift] Run at {now.isoformat()}")

    if not USERNAME or not PASSWORD:
        print("ERROR: Missing X_USERNAME or X_PASSWORD env vars.", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as p:
        # Navigateur
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        try:
            login(page)
            snap(page, "after_login")

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

            snap(page, "after_post")
            browser.close()
        except Exception as e:
            print(f"[FATAL] {e}", file=sys.stderr)
            # Dernière chance: capture d'écran d'erreur
            try:
                snap(page, "error")
            except:
                pass
            try:
                browser.close()
            except:
                pass
            sys.exit(1)

if __name__ == "__main__":
    main()
