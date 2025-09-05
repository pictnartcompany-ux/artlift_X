import os, random, time
from datetime import datetime
from dateutil import tz
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

USERNAME = os.getenv("X_USERNAME")  # email/username
PASSWORD = os.getenv("X_PASSWORD")  # mot de passe

# Listes (à personnaliser)
ARTISTS_NFT = ["artistNFT1", "artistNFT2"]
ARTISTS_NONNFT = ["artist1", "artist2"]
PICTNART_PROMOS = [
    "Discover our partner Pictnart for creative support and artistic growth 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
    "Looking for motivation in your art journey? 🌟 Check out our partner Pictnart 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
    "Elevate your craft with the help of our partner Pictnart 🎨 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
]

P_ARTISTS = 0.70   # 70% retweets d'artistes
P_PROMO   = 0.0025 # ~2–3 promos/mois sur 465 runs
RANDOM_WAIT = (2.0, 5.0)  # petites pauses humaines

def human_pause(a=RANDOM_WAIT[0], b=RANDOM_WAIT[1]):
    time.sleep(random.uniform(a, b))

def login(page):
    page.goto("https://x.com/login", wait_until="domcontentloaded")
    page.wait_for_selector('input[name="text"]', timeout=20000)
    page.fill('input[name="text"]', USERNAME)
    human_pause()
    page.click('div[role="button"]:has-text("Next"), div[role="button"]:has-text("Suivant")')

    # Étape intermédiaire possible: X demande email/tél/username à nouveau
    try:
        page.wait_for_selector('input[name="text"]', timeout=5000)
        # si un second champ texte réapparaît, on remet l’USERNAME
        if page.is_visible('input[name="text"]'):
            page.fill('input[name="text"]', USERNAME)
            human_pause()
            page.click('div[role="button"]:has-text("Next"), div[role="button"]:has-text("Suivant")')
    except PWTimeout:
        pass

    page.wait_for_selector('input[name="password"]', timeout=20000)
    page.fill('input[name="password"]', PASSWORD)
    human_pause()
    page.click('div[role="button"]:has-text("Log in"), div[role="button"]:has-text("Se connecter")')

    # Attendre que la timeline ou le bouton "Post" soit présent
    page.wait_for_selector('div[aria-label="Post"], div[data-testid="tweetTextarea_0"]', timeout=30000)

def post_text(page, text):
    # Ouvrir la boîte de post
    if page.is_visible('div[aria-label="Post"]'):
        page.click('div[aria-label="Post"]')
    else:
        page.click('div[data-testid="tweetTextarea_0"]')
    human_pause()
    # Zone de texte
    page.fill('div[aria-label="Post text"], div[role="textbox"][data-testid="tweetTextarea_0"]', text)
    human_pause()
    # Bouton "Tweet"
    page.click('div[data-testid="tweetButtonInline"]')
    # Attendre un petit signe que c'est parti (pas toujours fiable, mais ok)
    human_pause(3, 6)

def retweet_latest(page, handle):
    # handle sans '@'
    h = handle.lstrip("@")
    page.goto(f"https://x.com/{h}", wait_until="domcontentloaded")
    # attendre un tweet
    page.wait_for_selector('article div[data-testid="retweet"]', timeout=20000)
    human_pause()
    # cliquer sur le premier retweet dispo
    page.click('article div[data-testid="retweet"]', delay=random.randint(50,120))
    human_pause()
    # confirmer "Retweet"
    page.click('div[role="menuitem"]:has-text("Retweet")')
    human_pause(2,4)

def post_pictnart_promo(page):
    post_text(page, random.choice(PICTNART_PROMOS))

def post_loufis(page):
    # soit retweet d'@loufisart (si accessible), soit fallback texte
    try:
        retweet_latest(page, "loufisart")
    except Exception as e:
        post_text(page, "A new piece from @loufisart — dive into the world of Loufi’s Art ✨")

def post_artists(page):
    lst = ARTISTS_NFT if random.random() < 0.5 else ARTISTS_NONNFT
    random.shuffle(lst)
    for h in lst:
        try:
            retweet_latest(page, h)
            return
        except Exception:
            continue
    # fallback léger si aucun RT possible
    post_text(page, "Discover inspiring art today ✨ #art #inspiration")

def main():
    # Logs horodatés Europe/Brussels
    brussels = tz.gettz("Europe/Brussels")
    now = datetime.utcnow().replace(tzinfo=tz.UTC).astimezone(brussels)
    print(f"[ArtLift] Run at {now.isoformat()}")

    if not USERNAME or not PASSWORD:
        raise RuntimeError("Missing X_USERNAME or X_PASSWORD env vars.")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(locale="en-US", user_agent=None)
        page = context.new_page()

        login(page)

        roll = random.random()
        if roll < P_PROMO:
            post_pictnart_promo(page)
        elif roll < P_PROMO + P_ARTISTS:
            post_artists(page)
        else:
            post_loufis(page)

        browser.close()

if __name__ == "__main__":
    main()
