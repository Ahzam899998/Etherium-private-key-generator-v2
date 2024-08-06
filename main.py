import os
import requests
from eth_account import Account
import threading
from concurrent.futures import ThreadPoolExecutor

# Generate a random private key
def generate_private_key():
    return os.urandom(32).hex()

# Derive address from private key
def private_key_to_address(private_key):
    return Account.from_key(private_key).address

# Check balance of address using Infura API
def get_balance(address):
    api_key = "cec17ce1af8446de9046be035d8c96a4"  # Replace this with your Infura API key
    url = f"https://mainnet.infura.io/v3/{api_key}"
    data = {"jsonrpc":"2.0","method":"eth_getBalance","params":[address,"latest"],"id":1}
    response = requests.post(url, json=data)
    
    try:
        response_data = response.json()
        balance_wei = int(response_data["result"], 16)
        return balance_wei / 10**18  # Convert from wei to ether
    except KeyError:
        print(f"Error fetching balance for address {address}: 'result' key not found")
        return 0.0
    except (ValueError, TypeError) as e:
        print(f"Error processing balance for address {address}: {e}")
        return 0.0

def worker(counter, lock, stop_event, batch_size=10):
    while not stop_event.is_set():
        for _ in range(batch_size):
            if stop_event.is_set():
                break
            
            private_key = generate_private_key()
            address = private_key_to_address(private_key)
            balance = get_balance(address)
            
            with lock:
                counter[0] += 1
                count = counter[0]
            
            print(f"Private Key: {private_key} ({count} generated)")
            print("Address:", address)
            print(f"Balance (ETH): {balance:.7f}")
            
            if balance > 0.0000000:
                with open("result.txt", "a") as file:
                    file.write(f"Private Key: {private_key}\nAddress: {address}\nBalance (ETH): {balance:.7f}\n\n")
                stop_event.set()
                print("Found a non-zero balance. Stopping...")
                break

def main():
    num_threads = 32  # Increase the number of threads to improve performance
    batch_size = 20   # Number of keys processed per batch in each thread
    counter = [0]
    lock = threading.Lock()
    stop_event = threading.Event()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, counter, lock, stop_event, batch_size) for _ in range(num_threads)]

        # Wait for all threads to complete
        for future in futures:
            future.result()

    print("Total private keys generated:", counter[0])

if __name__ == "__main__":
    main()
    