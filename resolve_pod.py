import requests
import json
import os

def resolve_pod():
    config_path = "config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    api_key = config.get("runpod_api_key")
    pod_id = config.get("runpod_pod_id")
    
    if not api_key or not pod_id:
        print("Error: Missing API Key or Pod ID in config.")
        return

    headers = {"Authorization": f"Bearer {api_key}"}
    query = """
    query Pods {
      myself {
        pods {
          id
          name
          desiredStatus
          imageName
          runtime {
            ports {
              ip
              publicPort
              privatePort
            }
          }
        }
      }
    }
    """
    
    try:
        response = requests.post(
            "https://api.runpod.io/graphql", 
            json={"query": query}, 
            headers=headers,
            timeout=10
        )
        pods = response.json().get("data", {}).get("myself", {}).get("pods", [])
        if pods:
            print(json.dumps(pods, indent=2))
        else:
            print("No pods found or API error.")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    resolve_pod()
