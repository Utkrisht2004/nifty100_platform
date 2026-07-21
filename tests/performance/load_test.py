import time
import concurrent.futures
import requests

API_URL = "http://127.0.0.1:8000/api/v1/screener/?min_roe=15&max_de=1"


def fetch_api(thread_id):
    start = time.time()
    try:
        response = requests.get(API_URL, timeout=5)
        duration = time.time() - start
        return thread_id, response.status_code, duration
    except Exception as e:
        return thread_id, str(e), time.time() - start


if __name__ == "__main__":
    print("\n--- DAY 43: API CONCURRENT LOAD TEST ---")
    print(f"[*] Targeting: {API_URL}")
    print("[*] Launching 10 concurrent threads...\n")

    start_total = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_api, i) for i in range(1, 11)]
        for future in concurrent.futures.as_completed(futures):
            t_id, status, duration = future.result()
            print(f"Thread {t_id:02d} | Status: {status} | Time: {duration:.3f}s")

    total_time = time.time() - start_total
    print(f"\n[✓] 10 concurrent requests completed in {total_time:.3f} seconds.")

    if total_time < 10.0:
        print("[✓] SPRINT TARGET MET: Completed in under 10 seconds.")
    else:
        print("[!] TARGET FAILED: Took longer than 10 seconds.")
