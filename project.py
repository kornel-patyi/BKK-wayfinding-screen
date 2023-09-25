import os
import tabulate
import sys
import json
import requests
import threading
import time

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from dataclasses import dataclass
from collections.abc import Collection

pygame.init()

# Initialiting the fonts used
pygame.font.init()
STICKER_FONT = pygame.font.Font("fonts/arial.ttf", 40)
STICKER_FONT_SMALL = pygame.font.Font("fonts/arial.ttf", 21)
SCREEN_FONT = pygame.font.Font("fonts/JD-LCD-Rounded.ttf", 85)

# Defining the colors used by Pygame
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
WHITE = (255, 255, 255)
SCREEN_BLACK = (41, 34, 16)
SCREEN_WHITE = (255, 255, 95)


@dataclass
class Sprite:
    surface: pygame.Surface
    rect: pygame.rect

    @classmethod
    def from_dict(cls, img_dict):
        surface = pygame.image.load(img_dict["path"]).convert_alpha()
        rect = eval(
            f"surface.get_rect({img_dict['pos']['align']}={img_dict['pos']['pos']})"
        )
        return Sprite(surface=surface, rect=rect)


@dataclass
class Text(Sprite):
    text: str

    @classmethod
    def from_dict(cls, text_dict):
        if text_dict["size"] == "standard":
            surface = STICKER_FONT.render(text_dict["text"], True, WHITE)
        elif text_dict["size"] == "small":
            surface = STICKER_FONT_SMALL.render(text_dict["text"], True, WHITE)
        else:
            raise ValueError("Invalid text_dict")
        rect = eval(
            f"surface.get_rect({text_dict['pos']['align']}={text_dict['pos']['pos']})"
        )
        return Text(text=text_dict["text"], surface=surface, rect=rect)


def add(n1, n2):
    return n1 + n2


def get_stop_name(api_key):
    while True:
        stop_name = input("Please give a stop name: ")

        if is_valid_search(stop_name):
            url = "https://futar.bkk.hu/api/query/v1/ws/otp/api/where/search"
            params = {
                "query": stop_name,
                "version": 2,
                "includeReferences": "false",
                "key": api_key
            }
            api_response = requests.get(url, params)
            if api_response.status_code == 200:
                result = api_response.json()
                try:
                    stops = result["data"]["entry"]["stopIds"]
                except:
                    pass
                else:
                    if stops:
                        return stops
            else:
                print("BKK API error")


def is_int_between(MIN_NUM, MAX_NUM, num):
    try:
        num = int(num)
    except ValueError:
        return False
    else:
        if MIN_NUM <= num <= MAX_NUM:
            return True
        else:
            return False


def is_valid_search(query):
    return len(query) > 2 and not query.isspace()


def get_data_for_stops(api_key: str, stop_ids: Collection) -> list:
    url = "https://futar.bkk.hu/api/query/v1/ws/otp/api/where/arrivals-and-departures-for-stop"
    params = {
        "minutesBefore": 2,
        "minutesAfter": 30,
        "stopId": tuple(stop_ids),
        "onlyDepartures": True,
        "limit": 60,
        "minResult": 5,
        "version": 2,
        "includeReferences": True,
        "key": api_key
    }
    api_response = requests.get(url, params).json()
    api_references = api_response["data"]["references"]
    api_stops = api_references["stops"]
    api_routes = api_references["routes"]
    stops = []
    for stop_id in stop_ids:
        api_stop = api_stops[stop_id]
        stop_name = api_stop["name"]
        stop_color = api_stop["style"]["colors"][0]
        stop_route_ids = api_stop["routeIds"]
        if stop_route_ids:
            stop_routes = []
            for id in stop_route_ids:
                curr_route = api_routes[id]
                stop_routes.append({
                    "type": curr_route["type"],
                    "name": curr_route["shortName"],
                    "description": curr_route["description"],
                    "style": {
                        "color": curr_route["style"]["color"],
                        "iconText": curr_route["style"]["icon"]["text"],
                        "textColor": curr_route["style"]["icon"]["textColor"]
                    }
                })
            stops.append({
                "id": stop_id,
                "name": stop_name,
                "color": stop_color,
                "routes": stop_routes
            })

    return stops


departures = []
def refresh_data(api_key: str, stop_id: str) -> None:
    url = "https://futar.bkk.hu/api/query/v1/ws/otp/api/where/arrivals-and-departures-for-stop"
    params = {
        "minutesBefore": 0,
        "minutesAfter": 60,
        "stopId": (stop_id),
        "onlyDepartures": True,
        "limit": 60,
        "minResult": 5,
        "version": 2,
        "includeReferences": True,
        "key": api_key
    }
    api_response = requests.get(url, params)
    api_response_json = api_response.json()
    api_departures = api_response_json["data"]["entry"]["stopTimes"]
    api_trips = api_response_json["data"]["references"]["trips"]
    api_routes = api_response_json["data"]["references"]["routes"]
    departures_func = []
    for api_departure in api_departures:
        trip_id = api_departure["tripId"]
        sign_text = api_departure["stopHeadsign"]
        if "predictedDepartureTime" in api_departures:
            departure_time = api_departure["predictedDepartureTime"]
        else:
            departure_time = api_departure["departureTime"]

        route_id = api_trips[trip_id]["routeId"]
        line_name = api_routes[route_id]["shortName"]
        departures_func.append({
            "line_name": line_name,
            "sign_text": sign_text,
            "departure_time": departure_time
        })


    global departures
    departures = departures_func


def shorten_text(font, text, max_width):
    width = font.size(text)[0]
    while width > max_width:
        text = text[:-1]
        width = font.size(text)[0]
    return text

def main():
    ########################
    # checking the api key #
    ########################
    api_key = os.environ.get("BKK_API_KEY")
    if not api_key:
        raise RuntimeError("BKK api key not set")

    ##################################
    # getting the stop from the user #
    ##################################
    stops = get_stop_name(api_key)

    # getting the date for the stop selection
    stops = get_data_for_stops(api_key, stops)
    stops.sort(key=lambda stop: (bool(stop["routes"]), stop["name"], len(stop["routes"])))
    stops_to_tabulate = []
    MIN_STOP_NUM = 1
    for i, stop in enumerate(stops, start=MIN_STOP_NUM):
        routes = []
        for route in stop["routes"]:
            routes.append(f"{route['name']} - {route['description']}")
        stops_to_tabulate.append({
            "button": i,
            "name": stop["name"],
            "routes": "\n".join(routes)
        })
    MAX_STOP_NUM = i

    # displaying the table
    headers = {
        "button": "Text to select",
        "name": "Name of stop",
        "routes": "Lines of stop"
    }
    print(tabulate.tabulate(stops_to_tabulate, headers, tablefmt="grid"))

    # getting the correct stop number from the user
    while True:
        stop_num = input("Please choose a stop: ")
        if is_int_between(MIN_STOP_NUM, MAX_STOP_NUM, stop_num):
            stop_num = int(stop_num)
            break
        else:
            print("Incorrect value given")

    CHOOSEN_STOP = stops[stop_num - 1]


    #####################################################
    # Initializing Pygame and opening the Pygame window #
    #####################################################
    size = (1080, 400)
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("BKK display")

    # Loop until the user clicks the close button.
    done = False

    clock = pygame.time.Clock()

    # Creating the rectangle for the display itself
    display_panel_rect = pygame.Rect(60, 70, 960, 260)

    # Reading in and creating all the static elements for the wayfinding screen
    static_elements = []
    with open("assets/static_elements.json", encoding="utf-8") as file:
        data = file.read()
        static_elements_file = json.loads(data)
        texts = static_elements_file["texts"]
        for text in texts:
            if text["text"] == "!!!choosen stop!!!":
                text["text"] = CHOOSEN_STOP["name"]
            static_elements.append(Text.from_dict(text))

        images = static_elements_file["images"]
        for image in images:
            static_elements.append(Sprite.from_dict(image))


    REFRESH_DATA = pygame.USEREVENT
    pygame.time.set_timer(REFRESH_DATA, 5000)

    refresh_data(api_key, CHOOSEN_STOP["id"])

    # drawing all the static elements which doesn't need to be redrawn
    for static_element in static_elements:
        screen.blit(static_element.surface, static_element.rect)

    while not done:
        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == REFRESH_DATA:
                x = threading.Thread(
                    target=refresh_data, args=(api_key, CHOOSEN_STOP["id"])
                )
                x.start()

        pygame.draw.rect(screen, SCREEN_BLACK, display_panel_rect)
        curr_epoch_time = time.time()

        i = 0
        for departure in departures:
            minutes_for_departure = round(
                (departure["departure_time"]-curr_epoch_time) / 60
            )
            if minutes_for_departure > 0:
                line_name = departure["line_name"]
                sign_text = departure["sign_text"]
                departure_time_text = f"{minutes_for_departure}'"

                # line number
                line_num_surface = SCREEN_FONT.render(line_name, True, SCREEN_WHITE)
                line_num_rect = line_num_surface.get_rect(topleft=(65, 65 + 60*i))
                screen.blit(line_num_surface, line_num_rect)

                # line direction
                sign_text = shorten_text(SCREEN_FONT, sign_text, 700)
                line_direction_surface = SCREEN_FONT.render(sign_text, True, SCREEN_WHITE)
                line_direction_rect = line_direction_surface.get_rect(topleft=(200, 65 + 60*i))
                screen.blit(line_direction_surface, line_direction_rect)

                # depature time
                departure_time_surface = SCREEN_FONT.render(departure_time_text, True, SCREEN_WHITE)
                departure_time_rect = departure_time_surface.get_rect(topright=(1020, 65 + 60*i))
                screen.blit(departure_time_surface, departure_time_rect)
                if i >= 3:
                    break
                else:
                    i += 1

        pygame.display.update()

        # Limit to 60 frames per second
        clock.tick(60)

    # Close the window and quit.
    pygame.quit()


if __name__ == "__main__":
    main()
