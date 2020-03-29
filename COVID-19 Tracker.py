import requests
import tkinter as tk
from matplotlib import pyplot as plt
from datetime import datetime
from PIL import ImageTk, Image
import pycountry
import difflib
import pygal
from pygal.maps.world import COUNTRIES
import webbrowser

# Create a root window
root = tk.Tk()
root.resizable(width=False, height=False)
root.title('COVID-19 Tracker')
root.iconbitmap('earth.ico')
# Remember to set an icon later

# Window Dimensions

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 900

# Create Canvas
canvas = tk.Canvas(root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
canvas.pack()
canvas.create_line(795, 0, 795, SCREEN_HEIGHT, fill='black')

# Make a frame to hold the button and the entries
entry_frame = tk.Frame(canvas)
entry_frame.place(relx=0.55, rely=0.15, relwidth=0.4, relheight=0.9)

# Make a label for countries/city input
entry_label = tk.Label(canvas, text='Countries', font=('Calibri', 15))
entry_label.place(relx=0.545, rely=0.26, relwidth=0.15, relheight=0.05)

# Make a label for start date input
start_date_label = tk.Label(canvas, text='Start Date\n Earliest: 1/22/20', font=('Calibri', 13))
start_date_label.place(relx=0.73, rely=0.26, relwidth=0.1, relheight=0.05)

# Make a label for end date input
end_date_label = tk.Label(canvas, text='End Date', font=('Calibri', 15))
end_date_label.place(relx=0.835, rely=0.26, relwidth=0.1, relheight=0.05)

# Make an entry for start date input
start_date_entry = tk.Entry(canvas, font=('Calibri', 15))
start_date_entry.place(relx=0.75, rely=0.33, relwidth=0.07, relheight=0.05)

# Make an entry for end date input
end_date_entry = tk.Entry(canvas, font=('Calibri', 15))
end_date_entry.place(relx=0.86, rely=0.33, relwidth=0.07, relheight=0.05)

# Make a frame to hold the image of the graphs
graph_frame = tk.Frame(canvas)
graph_frame.place(relx=0, rely=0.1, relwidth=0.52, relheight=0.8)

# Make a button for world map
world_map_button = tk.Button(canvas, text='Show World Map',  bg='#d7dbd7', font=('Calibri', 15),
                         command=lambda: show_world_map())
world_map_button.place(relx=0.75, rely=0.4, relwidth=0.18, relheight=0.05)



# Make class to create multiple entries if needed

class Entry:
    def __init__(self, entry_number):
        self.entry_number = entry_number
        self.entry = tk.Entry(entry_frame, font=('Calibri', 15))

    def place(self):
        self.entry.place(relx=0, rely=self.entry_number * 0.15 + 0.05, relheight=0.08)


entry_list = []
entry_number = 1
e = Entry(entry_number)
e.place()
entry_list.append(e)


def create_entry():
    global entry_number  # Lets us modify the value of a global variable from this scope. Tells it that we aren't
    # declaring a new local variable here with the same name, but using the global variable we defined previously.
    if len(entry_list) < 5:
        a = Entry(entry_number + 1)
        a.place()
        entry_list.append(a)
        entry_number += 1
    else:
        error_message(5)
    print(entry_list)


def delete_entry():
    global entry_number
    if len(entry_list) > 1:
        deleted_entry = entry_list.pop()
        deleted_entry.entry.destroy()
        entry_number -= 1
    else:
        error_message(6)
    print(entry_list)


# Make the button that is pressed to make more entries for countries
entry_button = tk.Button(entry_frame, text='Add Country', bg='#d7dbd7', font=('Calibri', 15),
                         command=lambda: create_entry())
entry_button.place(relx=0, rely=0, relwidth=0.5, relheight=0.1)

# Make the button that is pressed to delete extra entries for countries
delete_button = tk.Button(entry_frame, text='Remove Country', bg='#d7dbd7', font=('Calibri', 15),
                          command=lambda: delete_entry())
delete_button.place(relx=0.5, rely=0, relwidth=0.5, relheight=0.1)

# Make the button that is pressed to search the contents of the entries
search_button = tk.Button(canvas, text='Search', bg='#d7dbd7', font=('Calibri', 15), command=lambda: check_input())
search_button.place(relx=0.55, rely=0.05, relwidth=0.4, relheight=0.1)

# API URLs

url = 'https://corona.lmao.ninja/v2/historical'

country_cases = []


def check_empty(entry):
    if entry.entry.get():
        return True
    else:
        return False


def check_input():
    filtered_list = filter(check_empty, entry_list)
    global countries
    countries = [c.name for c in pycountry.countries]
    if len(list(filtered_list)) == len(entry_list):
        for country in entry_list:
            if country.entry.get() != 'uk' and country.entry.get() != 'usa':
                try:
                    difflib.get_close_matches(country.entry.get(), countries)[0]
                except IndexError:
                    error_message(4)
                    return
        try:
            datetime.strptime(start_date_entry.get().lstrip('0'), '%m/%d/%y')
            datetime.strptime(end_date_entry.get().lstrip('0'), '%m/%d/%y')
        except ValueError:
            error_message(2)
        else:
            search_entries()
    else:
        error_message(1)


def search_entries():
    for i in range(len(entry_list)):
        search_data(i)
    if country_cases[-1]:
        plot_data(country_cases)
    else:
        error_message(3)


def search_data(entry_num):
    country_name = entry_list[entry_num].entry.get()
    if country_name.lower() != 'uk' and country_name.lower() != 'usa':
        country_name = difflib.get_close_matches(country_name, countries)[0].lower()
    print(country_name)
    start_date = start_date_entry.get().lstrip('0')
    end_date = end_date_entry.get().lstrip('0')

    global response
    response = requests.get(url)
    formatted_response = response.json()

    output = []
    # output = [{'country': 'france', 'cases': {'date': cases,}
    for country in formatted_response:
        country_dict = {'country': country['country'], 'cases': {}}
        in_range = False
        for date, case in country['timeline']['cases'].items():
            if date == start_date:
                in_range = True
                country_dict['cases'][date] = case
            if in_range:
                country_dict['cases'][date] = case
            if date == end_date:
                in_range = False
        output.append(country_dict)

    num_cases = len(output[0]['cases'].values())
    cases = [0 for i in range(num_cases)]

    for country in output:
        if country['country'] == country_name:
            cases = [sum(i) for i in zip(cases, country['cases'].values())]

    global dates
    dates = list(output[0]['cases'].keys())
    dates = [datetime.strptime(date, '%m/%d/%y') for date in dates]
    country_cases.append(cases)
    print(country_cases)
    print(cases)


def plot_data(data):
    """Plot data. Not much to explain."""

    fig = plt.figure(figsize=(10, 6))
    for i in range(len(data)):
        if entry_list[i].entry.get() == 'uk':
            plt.plot(dates, data[i], label='uk')
        elif entry_list[i].entry.get() == 'usa':
            plt.plot(dates, data[i], label='usa')
        else:
            plt.plot(dates, data[i], label=difflib.get_close_matches(entry_list[i].entry.get(), countries)[0])
    # plt.plot(dates, cases, c='red')
    plt.legend(loc='upper left')
    plt.title(f'{start_date_entry.get()} to {end_date_entry.get()} COVID-19 Rates', fontsize=15)
    plt.xlabel('', fontsize=5)
    fig.autofmt_xdate()
    plt.ylabel('Number of COVID-19 Cases', fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=12)
    plt.savefig('covid_19.png')
    show_graph()


def show_graph():
    img = Image.open('covid_19.png')
    img = img.resize((750, 450), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img, master=root)

    global img_label
    img_label = tk.Label(graph_frame, image=img)
    img_label.image = img
    img_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    print(country_cases)
    country_cases.clear()


def show_world_map():
    cases_dict = {}
    try:
        request_response = response.json()
    except NameError:
        error_message(7)
        return
    database_countries = [item['country'] for item in request_response]
    database_countries = sorted(list(set(database_countries)))
    for database_country in database_countries:
        for country in request_response:
            if database_country == country['country']:
                case = country['timeline']['cases'][end_date_entry.get()]
                try:
                    cases_dict[database_country] += case
                except:
                    cases_dict[database_country] = case
    print(cases_dict)
    world_map_dict = {}
    world_countries = [item for item in COUNTRIES.values()]
    world_codes = [item for item in COUNTRIES.keys()]

    for country in cases_dict.keys():
        for world_country in world_countries:
            if country == world_country.lower():
                world_map_dict[world_country] = cases_dict[country]

    # Catch the exceptions in country name formatting
    world_map_dict['United States'] = cases_dict['usa']
    world_map_dict['United Kingdom'] = cases_dict['uk']

    print(world_map_dict)
    world_map_data = {}
    for country, cases in world_map_dict.items():
        world_map_data[world_codes[world_countries.index(country)]] = cases

    wm = pygal.maps.world.World()
    wm.title = 'Global COVID-19 Rates during ' + end_date_entry.get()
    wm.add(end_date_entry.get(), world_map_data)
    wm.render_to_file('covid_19_world_map.svg')
    url = 'covid_19_world_map.svg'
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    webbrowser.get(chrome_path).open(url)

    print(world_map_data)
    #codes = [code for code in COUNTRIES.keys()]


def error_message(error_type):
    if error_type == 1:
        error_label = tk.Label(graph_frame, text='Please fill out all the information!', font=('Calibri', 30))
        error_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    elif error_type == 2:
        error_label = tk.Label(graph_frame, text='Make sure the dates are formatted correctly! \n Example: 1/1/20', font=('Calibri', 25))
        error_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    elif error_type == 3:
        error_label = tk.Label(graph_frame, text='Make sure your earliest date is AFTER 1/22/20!',
                               font=('Calibri', 25))
        country_cases.clear()
        error_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    elif error_type == 4:
        error_label = tk.Label(graph_frame, text='Make sure you spelled your countries correctly!',
                               font=('Calibri', 25))
        error_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    elif error_type == 5:
        error_label = tk.Label(graph_frame, text='Max 5 countries!',
                               font=('Calibri', 25))
        error_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    elif error_type == 6:
        error_label = tk.Label(graph_frame, text='Must have at least one country!',
                               font=('Calibri', 25))
        error_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    elif error_type == 7:
        error_label = tk.Label(graph_frame, text='You need to search for countries first!',
                               font=('Calibri', 25))
        error_label.place(relx=0, rely=0, relwidth=1, relheight=1)


def kill():
    root.quit()


root.protocol("WM_DELETE_WINDOW", kill)
root.mainloop()
print(entry_number)
