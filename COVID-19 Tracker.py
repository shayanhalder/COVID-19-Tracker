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
world_map_button = tk.Button(canvas, text='Show World Map', bg='#d7dbd7', font=('Calibri', 15),
                             command=lambda: show_world_map())
world_map_button.place(relx=0.75, rely=0.4, relwidth=0.18, relheight=0.05)


# Make class to create multiple entries
class Entry:
    def __init__(self, entry_number):
        self.entry_number = entry_number
        self.entry = tk.Entry(entry_frame, font=('Calibri', 15))

    def place(self):
        self.entry.place(relx=0, rely=self.entry_number * 0.15 + 0.05, relheight=0.08)


# Create the default entry in the GUI.
entry_list = []
entry_number = 1
e = Entry(entry_number)
e.place()
entry_list.append(e)


def create_entry():
    """Runs when the user presses the button to create an entry for another country option."""

    global entry_number
    if len(entry_list) < 5:
        a = Entry(entry_number + 1)
        a.place()
        entry_list.append(a)
        entry_number += 1
    else:
        error_message(5)


def delete_entry():
    """Runs when the user presses the button to delete an existing entry."""

    global entry_number
    if len(entry_list) > 1:
        deleted_entry = entry_list.pop()
        deleted_entry.entry.destroy()
        entry_number -= 1
    else:
        error_message(6)


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

# API URL
url = 'https://corona.lmao.ninja/v2/historical'
country_cases = []  # Will hold the data to be graphed. Will hold nested lists of COVID-19 data.


def check_empty(entry):
    """Check if the user input entires have been filled out"""

    if entry.entry.get():
        return True
    else:
        return False


def check_input():
    """Make sure that dates are correctly formatted, countries are spelled right, etc..."""

    filtered_list = filter(check_empty, entry_list)  # Filter the list to get entries that only have something in them.
    global countries
    countries = [c.name for c in pycountry.countries]
    if len(list(filtered_list)) == len(entry_list):  # Make sures there input for every entry.
        for country in entry_list:
            if country.entry.get().strip().lower() != 'uk' and country.entry.get().strip().lower() != 'usa':
                # Exceptions to country spell-checking
                try:
                    difflib.get_close_matches(country.entry.get(), countries)[0]  # Country spell checking feature
                except IndexError:
                    error_message(4)  # Country spelling error
                    return
        try:
            datetime.strptime(start_date_entry.get().lstrip('0'), '%m/%d/%y')  # Make sure dates correctly formatted
            datetime.strptime(end_date_entry.get().lstrip('0'), '%m/%d/%y')
        except ValueError:
            error_message(2)  # Date formatting error
        else:
            search_entries()  # If all these tests for user input pass, proceed to search data.
    else:
        error_message(1)  # Entries not filled error


def search_entries():
    """Search COVID-19 data for each country."""

    for i in range(len(entry_list)):
        search_data(i)
    if country_cases[-1]:  # Make sure that data has been collected.
        plot_data(country_cases)
    else:
        error_message(3)  # Earliest date AFTER 1/22/20 error (will not return data if before this)


def get_province_data(data, start_date, end_date):
    """Return a list of nested dictionaries on the COVID-19 rates of provinces of countries."""

    country_list = []  # List to store the nested dictionaries on data of each country and its province.
    for country in data:
        country_dict = {'country': country['country'], 'cases': {}}  # Dictionary that will be appended to output
        in_range = False  # To check if a date key-value pair is between the start and end dates.
        for date, case in country['timeline']['cases'].items():
            if date == start_date:
                in_range = True  # Dates inside range start.
                country_dict['cases'][date] = case
            if in_range:
                country_dict['cases'][date] = case
            if date == end_date:
                in_range = False  # Dates inside range end.
        country_list.append(country_dict)
    return country_list


def add_province_data(country_list, country_name):
    """Parse through the data and add up the data on each of the provinces of one country."""

    num_cases = len(country_list[0]['cases'].values())
    cases = [0 for i in range(num_cases)]

    for country in country_list:  # Parse through the data to add up the data from the provinces of one country
        if country['country'] == country_name:
            cases = [sum(i) for i in zip(cases, country['cases'].values())]
    return cases


def search_data(entry_num):
    """Search COVID-19 data for a specific country"""

    country_name = entry_list[entry_num].entry.get()
    if country_name.title().strip() == 'United States':
        country_name = 'usa'
    elif country_name.title().strip() == 'United Kingdom':
        country_name = 'uk'
    elif country_name.lower() != 'uk' and country_name.lower() != 'usa':  # Exceptions for country spell check
        country_name = difflib.get_close_matches(country_name, countries)[0].lower()
    start_date = start_date_entry.get().lstrip('0')  # In case date formatted incorrectly
    end_date = end_date_entry.get().lstrip('0')

    global response
    response = requests.get(url)
    formatted_response = response.json()
    country_list = get_province_data(formatted_response, start_date, end_date)
    cases = add_province_data(country_list, country_name)

    global dates
    dates = list(country_list[0]['cases'].keys())  # Parse through the data to get a list of the dates
    dates = [datetime.strptime(date, '%m/%d/%y') for date in dates]  # Format the data into time objects for the graph
    country_cases.append(cases)


def plot_data(data):
    """Plot data. Handle exceptions like the US and UK."""

    fig = plt.figure(figsize=(10, 6))
    for i in range(len(data)):  # Loop through the data on each country and plot it.
        if entry_list[i].entry.get() == 'uk':
            plt.plot(dates, data[i], label='uk')
        elif entry_list[i].entry.get() == 'usa':
            plt.plot(dates, data[i], label='usa')
        else:
            plt.plot(dates, data[i], label=difflib.get_close_matches(entry_list[i].entry.get(), countries)[0])
            # Try to spell-check the country name for the label (above).
    plt.legend(loc='upper left')
    plt.title(f'{start_date_entry.get()} to {end_date_entry.get()} COVID-19 Cases', fontsize=15)
    plt.xlabel('', fontsize=5)
    fig.autofmt_xdate()
    plt.ylabel('Number of COVID-19 Cases', fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=12)
    plt.savefig('covid_19.png')
    show_graph()


def show_graph():
    """Display the graph on the left side of the GUI."""

    img = Image.open('covid_19.png')
    img = img.resize((750, 450), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img, master=root)

    img_label = tk.Label(graph_frame, image=img)
    img_label.image = img
    img_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    country_cases.clear()  # Clear for the next search


def country_cases_dictionary(request_response, cases_dict):
    """Parse through the data and return a dictionary with countries and cases (provinces added up in countries)."""

    database_countries = [item['country'] for item in request_response]
    database_countries = sorted(list(set(database_countries)))  # Order alphabetically and eliminate duplicates

    for database_country in database_countries:
        for country in request_response:
            if database_country == country['country']:
                case = country['timeline']['cases'][end_date_entry.get()]
                try:
                    cases_dict[database_country] += case
                except KeyError:
                    cases_dict[database_country] = case


def filter_countries(world_map_dict, cases_dict, world_countries):
    """Filter out the uncommon countries between pycountry and pygal and account for country naming exceptions."""

    for country in cases_dict.keys():
        for world_country in world_countries:
            if country == world_country.lower():
                world_map_dict[world_country] = cases_dict[country]

    # Catch the exceptions in country name formatting
    world_map_dict['United States'] = cases_dict['usa']
    world_map_dict['United Kingdom'] = cases_dict['uk']


def show_world_map():
    """Get country codes and COVID-19 values and store them in a dictionary to use in the world map."""

    cases_dict = {}
    try:  # If the user tries to press the button to show the map before they make a graph.
        request_response = response.json()
    except NameError:
        error_message(7)  # Graph not made error
        return

    country_cases_dictionary(request_response, cases_dict)

    world_map_dict = {}  # Dictionary which will store key-value pairs of country names and their respective codes.
    world_countries = [item for item in COUNTRIES.values()]
    world_codes = [item for item in COUNTRIES.keys()]

    filter_countries(world_map_dict, cases_dict, world_countries)

    world_map_data = {}  # Dictionary with data that will be inputted into the world map.

    # Convert the country names in the keys to the country codes so pygal can make a world map.
    for country, cases in world_map_dict.items():
        world_map_data[world_codes[world_countries.index(country)]] = cases

    # Use the data in the world_map_data dictionary to create a world map using pygal.
    wm = pygal.maps.world.World()
    wm.title = 'Global COVID-19 Rates during ' + end_date_entry.get()
    wm.add(end_date_entry.get(), world_map_data)
    wm.render_to_file('covid_19_world_map.svg')
    url = 'covid_19_world_map.svg'
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'

    try:
        webbrowser.get(chrome_path).open(url)
    except:
        webbrowser.open(url)


def error_message(error_type):
    """Handle all the types of errors."""

    if error_type == 1:
        error_label = tk.Label(graph_frame, text='Please fill out all the information!', font=('Calibri', 30))
        error_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    elif error_type == 2:
        error_label = tk.Label(graph_frame, text='Make sure the dates are formatted correctly! \n Example: 1/1/20',
                               font=('Calibri', 25))
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
