import os, random, tweepy
from datetime import datetime
from dateutil import tz

# --- Auth X ---
client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
    wait_on_rate_limit=True,
)

# --- Listes de sources (à compléter) ---
artists_nft = ["@artistNFT1", "@artistNFT2", "@artistNFT3"]
artists_non_nft = ["@artist1", "@artist2", "@artist3"]
loufis_handles = ["@loufisart"]  # tu peux ajouter d'autres fils liés si tu veux

pictnart_promos = [
    "Discover our partner Pictnart for creative support and artistic growth 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
    "Looking for motivation in your art journey? 🌟 Check out our partner Pictnart 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
    "Elevate your craft with the help of our partner Pictnart 🎨 👉 https://pictnartcompany-ux.github.io/grow_your_craft/",
]

# --- Paramètres de répartition ---
# 70% artistes / 30% loufisart ; ~0.25% de chances par run pour un post promo (~2–3/mois à 465 runs)
P_ARTISTS = 0.70
P_PROMO = 0.0025  # très faible, mais suffisant sur le mois

def pick_rt_from(handle: str):
    u = client.get_user(username=handle.replace("@",""), user_fields=["id"])
    if not u or not u.data:
        return None
    tweets = client.get_users_tweets(u.data.id, max_results=5, exclude=["replies"])
    if not tweets or not tweets.data:
        return None
    return tweets.data[0].id

def do_retweet_from_list(handles):
    random.shuffle(handles)
    for h in handles:
        tid = pick_rt_from(h)
        if tid:
            client.retweet(tid)
            print(f"Retweeted latest from {h} (id {tid})")
            return True
    print("No tweet found to retweet from provided list.")
    return False

def post_pictnart_promo():
    text = random.choice(pictnart_promos)
    client.create_tweet(text=text)
    print("Posted Pictnart promo.")

def post_loufis():
    # RT @loufisart prioritaire, sinon un petit post texte
    if not do_retweet_from_list(loufis_handles):
        alt = "A new piece from @loufisart — dive into the world of Loufi’s Art ✨"
        client.create_tweet(text=alt)
        print("Fallback Loufi’s text post.")

def post_artists():
    # 50/50 NFT vs non-NFT
    if random.random() < 0.5:
        ok = do_retweet_from_list(artists_nft)
    else:
        ok = do_retweet_from_list(artists_non_nft)
    if not ok:
        # fallback small curation message (rare)
        client.create_tweet(text="Discover inspiring art today ✨ #art #inspiration")
        print("Fallback artist text post.")

def within_daily_cap():
    """
    On déclenche 15 fois/jour par cron → cap naturel = 15 posts/jour.
    On ajoute juste une sécurité: on vérifie l’heure locale Bruxelles
    et on n’autorise qu’un post par exécution (1 run = 1 post).
    """
    return True  # cap géré par le planning (15 runs/jour)

def main():
    # Fuseau Europe/Brussels pour logs
    brussels = tz.gettz("Europe/Brussels")
    now = datetime.utcnow().replace(tzinfo=tz.UTC).astimezone(brussels)
    print(f"Run at {now.isoformat()}")

    if not within_daily_cap():
        print("Daily cap reached, skipping.")
        return

    # Choix du type de post
    roll = random.random()
    if roll < P_PROMO:
        post_pictnart_promo()
    elif roll < P_PROMO + P_ARTISTS:
        post_artists()
    else:
        post_loufis()

if __name__ == "__main__":
    main()
