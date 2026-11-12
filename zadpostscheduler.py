import os
import pandas as pd
from datetime import datetime
import pytz
import urllib.request
import urllib.parse
import json
import time

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")

if not ACCESS_TOKEN or not IG_USER_ID or not FB_PAGE_ID:
    print("-> [ERROR] Missing required environment variables.")
    exit(1)

API_VERSION = "v22.0"
EGYPT_TZ = pytz.timezone('Africa/Cairo')

def is_video_file(url):
    return url.lower().endswith(('.mp4', '.mov', '.avi'))

def post_to_instagram(media_urls, caption):
    print("-> Publishing to ZAD Instagram...")
    try:
        if len(media_urls) == 1:
            url = media_urls[0]
            is_vid = is_video_file(url)
            create_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media"
            payload = {'caption': caption, 'access_token': ACCESS_TOKEN}
            if is_vid:
                payload['media_type'] = 'REELS'
                payload['video_url'] = url
            else:
                payload['image_url'] = url
                
            data = urllib.parse.urlencode(payload).encode('utf-8')
            req = urllib.request.Request(create_url, data=data, method='POST')
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode())
                creation_id = res_data.get('id')
                
            if is_vid:
                print("-> Waiting for Instagram video processing...")
                start_time = time.time()
                while time.time() - start_time < 300:
                    status_url = f"https://graph.facebook.com/{API_VERSION}/{creation_id}?fields=status_code&access_token={ACCESS_TOKEN}"
                    with urllib.request.urlopen(status_url) as s_res:
                        code = json.loads(s_res.read().decode()).get('status_code')
                        if code == 'FINISHED':
                            break
                        elif code == 'ERROR':
                            return False
                    time.sleep(15)
            return publish_ig_container(creation_id)
        else:
            children_ids = []
            for url in media_urls:
                is_vid = is_video_file(url)
                item_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media"
                payload = {'access_token': ACCESS_TOKEN, 'is_carousel_item': 'true'}
                if is_vid:
                    payload['media_type'] = 'VIDEO'
                    payload['video_url'] = url
                else:
                    payload['image_url'] = url

                data = urllib.parse.urlencode(payload).encode('utf-8')
                req = urllib.request.Request(item_url, data=data, method='POST')
                with urllib.request.urlopen(req) as resp:
                    child_id = json.loads(resp.read().decode()).get('id')
                    if is_vid:
                        while True:
                            s_url = f"https://graph.facebook.com/{API_VERSION}/{child_id}?fields=status_code&access_token={ACCESS_TOKEN}"
                            with urllib.request.urlopen(s_url) as s_res:
                                if json.loads(s_res.read().decode()).get('status_code') == 'FINISHED':
                                    break
                            time.sleep(10)
                    children_ids.append(child_id)

            carousel_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media"
            carousel_payload = {
                'media_type': 'CAROUSEL',
                'children': ','.join(children_ids),
                'caption': caption,
                'access_token': ACCESS_TOKEN
            }
            c_data = urllib.parse.urlencode(carousel_payload).encode('utf-8')
            c_req = urllib.request.Request(carousel_url, data=c_data, method='POST')
            with urllib.request.urlopen(c_req) as resp:
                creation_id = json.loads(resp.read().decode()).get('id')

            return publish_ig_container(creation_id)
    except Exception as e:
        print(f"-> [ERROR] Instagram failed: {e}")
        return False

def publish_ig_container(creation_id):
    publish_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish"
    pub_data = urllib.parse.urlencode({'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).encode('utf-8')
    for attempt in range(3):
        try:
            pub_req = urllib.request.Request(publish_url, data=pub_data, method='POST')
            with urllib.request.urlopen(pub_req) as pub_response:
                pub_res = json.loads(pub_response.read().decode())
                print(f"-> ZAD Instagram Success! Post ID: {pub_res.get('id')}")
                return True
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            if "9007" in error_body and attempt < 2:
                time.sleep(10)
                continue
            print(f"-> [ERROR] Instagram API Details: {error_body}")
            return False
    return False

def post_to_facebook(media_urls, caption):
    print("-> Publishing to ZAD Facebook Page...")
    try:
        if len(media_urls) == 1:
            url = media_urls[0]
            is_vid = is_video_file(url)
            endpoint = "videos" if is_vid else "photos"
            url_endpoint = f"https://graph.facebook.com/{API_VERSION}/{FB_PAGE_ID}/{endpoint}"
            payload = {'access_token': ACCESS_TOKEN}
            if is_vid:
                payload['description'] = caption
                payload['title'] = caption[:100]
                payload['file_url'] = url
            else:
                payload['message'] = caption
                payload['url'] = url
            data = urllib.parse.urlencode(payload).encode('utf-8')
            req = urllib.request.Request(url_endpoint, data=data, method='POST')
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode())
                print(f"-> ZAD Facebook Success! Post ID: {res_data.get('id')}")
                return True
        else:
            attached_media = []
            for url in media_urls:
                is_vid = is_video_file(url)
                endpoint = "videos" if is_vid else "photos"
                item_url = f"https://graph.facebook.com/{API_VERSION}/{FB_PAGE_ID}/{endpoint}"
                payload = {'access_token': ACCESS_TOKEN, 'published': 'false'}
                if is_vid:
                    payload['file_url'] = url
                else:
                    payload['url'] = url
                data = urllib.parse.urlencode(payload).encode('utf-8')
                req = urllib.request.Request(item_url, data=data, method='POST')
                with urllib.request.urlopen(req) as resp:
                    res_data = json.loads(resp.read().decode())
                    attached_media.append({'media_fbid': res_data.get('id')})

            feed_url = f"https://graph.facebook.com/{API_VERSION}/{FB_PAGE_ID}/feed"
            feed_payload = {
                'message': caption,
                'attached_media': json.dumps(attached_media),
                'access_token': ACCESS_TOKEN
            }
            feed_data = urllib.parse.urlencode(feed_payload).encode('utf-8')
            feed_req = urllib.request.Request(feed_url, data=feed_data, method='POST')
            with urllib.request.urlopen(feed_req) as resp:
                res_data = json.loads(resp.read().decode())
                print(f"-> ZAD Facebook Multi-Item Success! Post ID: {res_data.get('id')}")
                return True
    except Exception as e:
        print(f"-> [ERROR] Facebook failed: {e}")
        return False

def run_scheduler():
    print("--- ZAD Cloud Publisher V2 Running (Egypt Time) ---")
    excel_path = 'schedule.xlsx'

    if not os.path.exists(excel_path):
        print("-> [ERROR] schedule.xlsx not found.")
        return

    try:
        df = pd.read_excel(excel_path)
        
        if 'status' not in df.columns or 'scheduled_time' not in df.columns:
            print("-> [ERROR] Missing required columns (status, scheduled_time).")
            return

        now_egypt = datetime.now(EGYPT_TZ)
        print(f"-> Current Egypt Time: {now_egypt}")

        processed_count = 0
        failed_count = 0

        for i, row in df.iterrows():
            status = str(row.get('status', '')).strip().lower()
            if status != 'pending':
                continue

            scheduled_str = str(row.get('scheduled_time', '')).strip()
            parsed_dt = None

            # محاولة قراءة صيغ التواريخ المختلفة بما فيها AM/PM
            for fmt in (
                '%m/%d/%Y %I:%M:%S %p',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y %I:%M %p',
                '%m/%d/%Y %H:%M',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M'
            ):
                try:
                    parsed_dt = datetime.strptime(scheduled_str, fmt)
                    break
                except ValueError:
                    continue

            if parsed_dt:
                # ربط الوقت بتوقيت مصر
                scheduled_dt_egypt = EGYPT_TZ.localize(parsed_dt)
                if now_egypt < scheduled_dt_egypt:
                    print(f"-> Skipping Row {i+2}: Scheduled for {scheduled_str} (Future time).")
                    continue
            else:
                print(f"-> [WARNING] Could not parse date format for '{scheduled_str}' on Row {i+2}")
                continue

            print(f"-> Publishing Due Row {i+2}...")
            platform = str(row.get('platform', '')).strip().lower()
            media_raw = str(row.get('media_url', '')).strip()
            caption = str(row.get('caption', ''))

            media_urls = [u.strip().strip('"') for u in media_raw.split(',') if u.strip()]

            if not media_urls:
                print(f"-> [ERROR] No media URLs in Row {i+2}")
                failed_count += 1
                continue

            success = False
            if platform == 'instagram':
                success = post_to_instagram(media_urls, caption)
            elif platform == 'facebook':
                success = post_to_facebook(media_urls, caption)
            else:
                print(f"-> [WARNING] Unsupported platform '{platform}' on Row {i+2}")
                failed_count += 1
                continue

            if success:
                df.at[i, 'status'] = 'posted'
                processed_count += 1
                df.to_excel(excel_path, index=False)
                print(f"-> Row {i+2} successfully published and saved to Excel!")
                time.sleep(3)
            else:
                print(f"-> [ERROR] Publishing failed for Row {i+2}")
                failed_count += 1

        print("--------------------------------")
        print(f"-> Successfully published: {processed_count}")
        print(f"-> Failed posts: {failed_count}")
        print("--------------------------------")

    except Exception as e:
        print(f"-> [FATAL ERROR] {e}")

if __name__ == "__main__":
    run_scheduler()
