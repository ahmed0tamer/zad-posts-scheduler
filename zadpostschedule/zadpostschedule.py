import csv
from datetime import datetime

def dry_run_scheduler():
    print("--- ZAD Scheduler: Dry Run Test ---")
    try:
        with open('schedule.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            count = 0
            for row in reader:
                count += 1
                print(f"\n[Post #{count}]")
                print(f"  Platform: {row['platform']}")
                print(f"  Scheduled Time: {row['scheduled_time']}")
                print(f"  Status: {row['status']}")
                print(f"  Media URL: {row['media_url']}")
                print(f"  Caption: {row['caption']}")
                print("-" * 50)
            print(f"\nSuccessfully parsed {count} row(s) from schedule.csv.")
    except FileNotFoundError:
        print("Error: schedule.csv could not be found in your project directory.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    dry_run_scheduler()