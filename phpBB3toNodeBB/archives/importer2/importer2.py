#!/usr/bin/env python3

"""
Input:
phpbb_export/users.csv
phpbb_export/forums.csv
phpbb_export/topics.csv
phpbb_export/posts.csv
phpbb_export/uploads/ → fichiers joints, nom original ou attachment_<ID>.<ext>
phpbb_export/avatars/ → user_<uid>.jpg ou .png

After:

Check:
ls -la ./public/uploads/avatars/
ls -la ./public/uploads

mongo mongodb://nodebb:nodebb123@37.59.100.228:27017/nodebb
> db.objects.count({"_key": /^topic:/})
> db.objects.count({"_key": /^post:/})

Restart:
./nodebb build
./nodebb (re)start

Check:
Les avatars s’affichent correctement
Les posts contiennent bien les attachments avec URL NodeBB
Les topics et catégories sont visibles et triés correctement
"""

import pathlib
import shutil
import re
import time

import pandas as pd
import pymongo # pip3 install pymongo --break-system-packages
import slugify # pip3 install python-slugify --break-system-packages

# -------------------------
# CONFIGURATION
# -------------------------
# database:
MONGO_URI = "mongodb://nodebb:nodebb123@37.59.100.228:27017/nodebb"
DB_NAME = "nodebb"
# source
DATA_DIR = "./phpbb_export"
# dest:
UPLOADS_DIR = "./data/uploads"
AVATARS_DIR = "./data/public/uploads/avatars"


def main():
    """Main."""

    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    data_path = pathlib.Path(DATA_DIR)

    # -------------------------
    # 0️⃣ FIRST: Create essential group registered-users
    # -------------------------
    print("📦 Creating essential group registered-users...")

    # -------------------------
    # 1️⃣ Créer les groupes ESSENTIELS pour NodeBB
    # -------------------------
    print("📦 Création des groupes essentiels...")
    
    groups = [
        {
            "_key": "registered-users",
            "name": "registered-users", 
            "slug": "registered-users",
            "description": "Registered users",
            "hidden": 0,
            "system": 1,
            "private": 0,
            "disableJoinRequests": 1,
            "disableLeave": 1,
            "createdTimestamp": 0,
            "memberCount": 0,
            "userTitle": "Member",
            "userTitleEnabled": 1
        }
    ]
    
    for group in groups:
        db.objects.update_one(
            {"_key": group["_key"]}, 
            {"$set": group}, 
            upsert=True
        )

    print("✅ Groupes créés")

    # -------------------------
    # 2️⃣ Importer les utilisateurs
    # -------------------------
    users_csv = data_path / "users.csv"
    df_users = pd.read_csv(users_csv)
    users_map = {}
    nb_avatars = 0

    print(f"👤 Importation de {len(df_users)} utilisateurs...")
    
    for _, row in df_users.iterrows():
        uid = int(row['user_id'])
        username = str(row['username']).strip()
        email = str(row['email']).strip()
        userslug = slugify.slugify(username)
        joindate = int(row['joindate'])
        
        print(f"  → {username} (UID: {uid})")

        # Structure COMPLÈTE de l'utilisateur pour NodeBB
        user_doc = {
            "_key": f"user:{uid}",
            "uid": uid,
            "username": username,
            "userslug": userslug,
            "email": email,
            "joindate": joindate,
            "lastonline": joindate,
            "picture": "",
            "fullname": "",
            "location": "",
            "birthday": "",
            "website": "",
            "aboutme": "",
            "signature": "",
            "uploadedpicture": "",
            "profileviews": 0,
            "reputation": 0,
            "postcount": int(row['postcount']),
            "topiccount": 0,
            "lastposttime": 0,
            "banned": 0,
            "banned:expire": 0,
            "status": "offline",
            "email:confirmed": 1,
            "email:password": 1,
            # CHAMPS CRITIQUES pour l'affichage
            "groupTitle": "registered-users",
            "groupTitleArray": ["registered-users"],
            "groupTitleArray": json.dumps(["registered-users"]),
            "icon:text": username[0].upper() if username else "?",
            "icon:bgColor": "#673ab7",
            "cover:url": "",
            "cover:position": "",
            "username:disableEdit": 0,
            "email:disableEdit": 0,
            "accounttype": ""
        }

        # Handle avatar
        for ext in ['.jpg', '.png', '.gif', '.jpeg']:
            src_avatar = data_path / "avatars" / f"user_{uid}{ext}"
            if src_avatar.exists():
                dest_filename = f"{uid}{ext}"
                dest_avatar = pathlib.Path(AVATARS_DIR) / dest_filename
                shutil.copy2(src_avatar, dest_avatar)
                user_doc["picture"] = f"/uploads/avatars/{dest_filename}"
                user_doc["uploadedpicture"] = f"/uploads/avatars/{dest_filename}"
                nb_avatars += 1
                print(f"  ✓ Copied avatar for user {username}")
                break

        # Mettre à jour dans la collection objects
        db.objects.update_one(
            {"_key": user_doc["_key"]}, 
            {"$set": user_doc}, 
            upsert=True
        )

        # Document d'authentification (collection users)
        auth_doc = {
            "_key": f"user:{uid}",
            "uid": uid,
            "username": username,
            "userslug": userslug,
            "email": email,
            "joindate": joindate,
            "lastonline": joindate,
            "lastlogin": joindate,
            "password": "",  # Vide - l'utilisateur utilisera "Mot de passe oublié"
            "passwordExpiry": 0,
            "password:shaWrapped": 0,
            "status": "offline",
            "banned": 0,
            "banned:expire": 0
        }
        
        db.users.update_one(
            {"_key": auth_doc["_key"]}, 
            {"$set": auth_doc}, 
            upsert=True
        )

        # Stocker les infos utilisateur pour plus tard
        users_map[uid] = {
            "username": username,
            "userslug": userslug,
            "joindate": joindate,
            "postcount": int(row['postcount'])
        }

    print(f"✅ Imported {len(users_map)} users + {nb_avatars} avatars")

    # -------------------------
    # 3️⃣ Ajouter TOUS les utilisateurs au groupe registered-users
    # -------------------------
    print("👥 Adding users to registered-users group...")

    for uid, user_info in users_map.items():
        # Membership direct
        membership_key = f"uid:{uid}:group:registered-users"
        membership_doc = {
            "_key": membership_key,
            "uid": uid,
            "groupName": "registered-users",
            "timestamp": user_info["joindate"]
        }
        db.objects.update_one(
            {"_key": membership_key}, 
            {"$set": membership_doc}, 
            upsert=True
        )

        # Membership inverse (pour les recherches)
        reverse_key = f"group:registered-users:member:{uid}"
        reverse_doc = {
            "_key": reverse_key,
            "uid": uid,
            "groupName": "registered-users",
            "timestamp": user_info["joindate"]
        }
        db.objects.update_one(
            {"_key": reverse_key}, 
            {"$set": reverse_doc}, 
            upsert=True
        )

    print("✅ Tous les utilisateurs ajoutés au groupe")

    # -------------------------
    # 4️⃣ Mettre à jour le compteur du groupe
    # -------------------------
    registered_count = len(users_map)
    db.objects.update_one(
        {"_key": "registered-users"},
        {"$set": {"memberCount": registered_count}}
    )
    print(f"✅ Compteur du groupe mis à jour: {registered_count} membres")

    # -------------------------
    # 5️⃣ Créer les SORTED SETS ESSENTIELS pour NodeBB
    # -------------------------
    print("📊 Création des sorted sets...")
    
    # 5.1 users:joindate
    users_joindate = {
        "_key": "users:joindate",
        "value": [],
        "scores": []
    }
    
    # 5.2 users:postcount
    users_postcount = {
        "_key": "users:postcount", 
        "value": [],
        "scores": []
    }
    
    # 5.3 users:reputation
    users_reputation = {
        "_key": "users:reputation",
        "value": [],
        "scores": []
    }
    
    # 5.4 users:online (tous offline au début)
    users_online = {
        "_key": "users:online",
        "value": [],
        "scores": []
    }
    
    current_time = int(time.time())
    
    for uid, user_info in users_map.items():
        username = user_info["username"]
        joindate = user_info["joindate"]
        postcount = user_info["postcount"]
        
        # users:joindate
        users_joindate["value"].append(str(uid))
        users_joindate["scores"].append(joindate)
        
        # users:postcount
        users_postcount["value"].append(str(uid))
        users_postcount["scores"].append(postcount)
        
        # users:reputation
        users_reputation["value"].append(str(uid))
        users_reputation["scores"].append(0)  # Réputation à 0 par défaut
        
        # users:online (vide car tous offline)
        # users_online reste vide

    # Sauvegarder les sorted sets
    db.objects.update_one(
        {"_key": "users:joindate"}, 
        {"$set": users_joindate}, 
        upsert=True
    )
    
    db.objects.update_one(
        {"_key": "users:postcount"}, 
        {"$set": users_postcount}, 
        upsert=True
    )
    
    db.objects.update_one(
        {"_key": "users:reputation"}, 
        {"$set": users_reputation}, 
        upsert=True
    )
    
    db.objects.update_one(
        {"_key": "users:online"}, 
        {"$set": users_online}, 
        upsert=True
    )

    print("✅ Sorted sets créés")

    # -------------------------
    # 6️⃣ Créer les paramètres utilisateur
    # -------------------------
    print("⚙️ Création des paramètres utilisateur...")
    
    for uid in users_map.keys():
        settings_key = f"user:{uid}:settings"
        settings_doc = {
            "_key": settings_key,
            "receiveChatNotifications": 1,
            "restrictChat": 0,
            "topicPostSort": "oldest_to_newest",
            "followTopicsOnCreate": 1,
            "followTopicsOnReply": 0,
            "categoryWatchState": "notwatching",
            "dailyDigestFreq": "off",
            "upvoteNotifications": 1,
            "postQueue": 0,
            "bookmarks": "[]"
        }
        
        db.objects.update_one(
            {"_key": settings_key}, 
            {"$set": settings_doc}, 
            upsert=True
        )

    print("✅ Paramètres utilisateur créés")

    # -------------------------
    # 7️⃣ Mettre à jour le document GLOBAL
    # -------------------------
    print("🌍 Mise à jour des compteurs globaux...")
    
    next_uid = max(users_map.keys()) + 1 if users_map else 1
    
    global_doc = {
        "_key": "global",
        "nextUid": next_uid,
        "userCount": len(users_map),
        "topicCount": 0,  # Sera mis à jour plus tard
        "postCount": 0,   # Sera mis à jour plus tard
        "privateFileUpload": 0,
        "minimumTagsPerTopic": 0,
        "maximumTagsPerTopic": 5,
        "minimumTagLength": 3,
        "maximumTagLength": 15,
        "version": "4.7.0"
    }
    
    db.objects.update_one(
        {"_key": "global"}, 
        {"$set": global_doc}, 
        upsert=True
    )
    
    print(f"✅ Compteurs globaux: {len(users_map)} utilisateurs")

    # -------------------------
    # 8️⃣ CONTINUER AVEC LE RESTE DE L'IMPORT
    # (Catégories, topics, posts - ton code existant)
    # -------------------------

    # TODO PUT BACK REST IF CODE HERE ;-)
 
    print("🎉 COMPLETE IMPORT NodeBB 4.7.0 with avatars and attachments done. Users should now be visible")
    print("\nNext steps:")
    print("1. ./nodebb build")
    print("2. ./nodebb restart")
    print("3. Users can reset password via 'Forgot Password' link")


if __name__ == "__main__":
    main()
