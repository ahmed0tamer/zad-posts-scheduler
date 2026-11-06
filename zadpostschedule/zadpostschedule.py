import os
import csv
import urllib.request
import urllib.parse
import json
from datetime import datetime

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")


# def post_to_instagram(media_url, caption):
#     print("-> Publishing to ZAD Instagram...")
#     try:
#         # Step 1: Create Container
#         create_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
#         data = urllib.parse.urlencode({
#             'image_url': media_url,
#             'caption': caption,
#             'access_token': ACCESS_TOKEN
#         }).encode('utf-8')
        
#         req = urllib.request.Request(create_url, data=data, method='POST')
#         with urllib.request.urlopen(req) as response:
#             res_data = json.loads(response.read().decode())
#             creation_id = res_data.get('id')
            
#         # Step 2: Publish Container
#         publish_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish"
#         pub_data = urllib.parse.urlencode({
#             'creation_id': creation_id,
#             'access_token': ACCESS_TOKEN
#         }).encode('utf-8')
        
#         pub_req = urllib.request.Request(publish_url, data=pub_data, method='POST')
#         with urllib.request.urlopen(pub_req) as pub_response:
#             pub_res = json.loads(pub_response.read().decode())
#             print(f"-> ZAD Instagram Success! Post ID: {pub_res.get('id')}")
#             return True
#     except Exception as e:
#         print(f"-> [ERROR] Instagram failed: {e}")
#         return False
def post_to_instagram(media_url, caption):
    print("-> Publishing to ZAD Instagram...")
    try:
        create_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
        data = urllib.parse.urlencode({
            'image_url': media_url,
            'caption': caption,
            'access_token': ACCESS_TOKEN
        }).encode('utf-8')
        
        req = urllib.request.Request(create_url, data=data, method='POST')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            creation_id = res_data.get('id')
            
        publish_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish"
        pub_data = urllib.parse.urlencode({
            'creation_id': creation_id,
            'access_token': ACCESS_TOKEN
        }).encode('utf-8')
        
        pub_req = urllib.request.Request(publish_url, data=pub_data, method='POST')
        with urllib.request.urlopen(pub_req) as pub_response:
            pub_res = json.loads(pub_response.read().decode())
            print(f"-> ZAD Instagram Success! Post ID: {pub_res.get('id')}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"-> [ERROR] Instagram API Details: {error_body}")
        return False
    except Exception as e:
        print(f"-> [ERROR] Instagram failed: {e}")
        return False

def post_to_facebook(media_url, caption):
    print("-> Publishing to ZAD Facebook Page...")
    try:
        url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"
        data = urllib.parse.urlencode({
            'url': media_url,
            'message': caption,
            'access_token': ACCESS_TOKEN
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='POST')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            print(f"-> ZAD Facebook Success! Post ID: {res_data.get('id')}")
            return True
    except Exception as e:
        print(f"-> [ERROR] Facebook failed: {e}")
        return False

def run_scheduler():
    print("--- ZAD Cloud Publisher Running ---")
    rows = []
    updated = False
    
    try:
        with open('schedule.csv', mode='r', encoding='utf-8') as file:
            reader = list(csv.DictReader(file))
            if not reader:
                print("schedule.csv is empty.")
                return
            fieldnames = reader[0].keys()
            
            for row in reader:
                if row['status'].lower() == 'pending':
                    post_time = datetime.strptime(row['scheduled_time'], "%Y-%m-%d %H:%M:%S")
                    current_time = datetime.now()
                    
                    if current_time >= post_time:
                        platform = row['platform'].lower()
                        success = False
                        
                        if platform == 'instagram':
                            success = post_to_instagram(row['media_url'], row['caption'])
                        elif platform == 'facebook':
                            success = post_to_facebook(row['media_url'], row['caption'])
                            
                        if success:
                            row['status'] = 'posted'
                            updated = True
                    else:
                        print(f"-> Post scheduled for {post_time} is not due yet.")
                rows.append(row)
                
        if updated:
            with open('schedule.csv', mode='w', encoding='utf-8', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print("-> Successfully updated schedule.csv status to 'posted'.")
            
    except Exception as e:
        print(f"Error running scheduler: {e}")

if __name__ == "__main__":
    run_scheduler()