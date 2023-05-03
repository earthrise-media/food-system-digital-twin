import requests


def get_route_url(ip, coordinates):
    coords = ";".join([f"{coord[0]},{coord[1]}" for coord in coordinates])
    return f"http://{ip}:5000/route/v1/driving/{coords}?overview=false"


def query_osrm_route(ip, coordinates):
    url = get_route_url(ip, coordinates)
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None


def main():
    ip = "54.152.58.11"
    coordinates_list = [
        [(-122.4194, 37.7749), (-121.8863, 37.3382)],
        [(-121.8863, 37.3382), (-122.4194, 37.7749)]
    ]

    for coordinates in coordinates_list:
        result = query_osrm_route(ip, coordinates)
        if result:
            print(result)


if __name__ == "__main__":
    main()
