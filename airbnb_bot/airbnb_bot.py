import re
import string
import sqlite3 as sql
from os.path import isfile


location_regex = [
    # first entry in every tuple is a regex for matching user inputs
    # second entry in every tuple is a possible value
    #   for the key neighbourhood_group in our sql file
    (r'(charlottenburg)|(wilmersdorf)', 'Charlottenburg-Wilm.'),
    (r'(friedrichshain)|(kreuzberg)', 'Friedrichshain-Kreuzberg'),
    (r'lichtenberg', 'Lichtenberg'),
    (r'(marzahn)|(Hellersdorf)', 'Marzahn - Hellersdorf'),
    (r'mitte', 'Mitte'),
    (r'neukölln', 'Neukölln'),
    (r'pankow', 'Pankow'),
    (r'reinickendorf', 'Reinickendorf'),
    (r'spandau', 'Spandau'),
    (r'(steglitz)|(zehlendorf)', 'Steglitz - Zehlendorf'),
    (r'(tempelhof)|(schöneberg)', 'Tempelhof - Schöneberg'),
    (r'(treptow)|(köpenick)', 'Treptow - Köpenick')
]


def get_location_from_input(loc_sent, regex_list=location_regex):
    """
    get valid location names from user input using RegEx
    """
    # iterate through regular expressions and associated values in regex_list
    for regex, value in regex_list:
        match = re.search(regex, loc_sent)
        if match:
            # if a regex matches the input: return the corresponding value
            return value
    # return None if no regular expression matches the input
    print("Sorry, ich habe nicht verstanden. Kannst du deine Wünsche etwa unformulieren?")
    return None


room_type_regex = [
    (r'wohnung', 'Entire home/apt'),
    (r'haus', 'Entire home/apt'),
    (r'apartment', 'Entire home/apt'),
    (r'familie', 'Entire home/apt'),
    (r'raum', 'Private room'),
    (r'zimmer', 'Private room'),
    (r'wg', 'Private room'),
    (r'hostel', 'Private room'),
    (r'geteilt', 'Private room')
]


def get_room_type(room_type_sent, regex_list=room_type_regex):
    # basically the same as the function get_location_from_input(...) earlier
    for regex, value in regex_list:
        match = re.search(regex, room_type_sent)
        if match:
            # if a regex matches the input: return the corresponding value
            return value
    # return None if no regular expression matches the input
    print("Sorry, ich habe nicht verstanden. Kannst du deine Wünsche etwa unformulieren?")
    return None


def check_validity(var, answer):
    answer = answer
    # var = input('Input a number (int) for the Episode you want to check: ')
    try:
        for char in var:
            if char in "0123456789":
                answer = False
            else:
                raise ValueError
        return True
    except(ValueError):
        print("Bitte gib nur eine Zahl ein, damit ich Mathematik machen kann!")


def query_sql(key, value, budget, stay_nights, wished_room_type, columns, sql_file):
    """
    Query a sqlite file for entries where "key" has the value "value".
    Return the values corresponding to columns as a list.
    """

    # set up sqlite connection
    conn = sql.connect(sql_file)
    c = conn.cursor()


    # prepare query string that contains all three conditions
    query_template = '''SELECT {columns}
                        FROM listings
                        WHERE {key} = "{value}" AND price <= {budget}
                        AND minimum_nights <= {stay_nights} AND room_type = "{wished_room_type}"'''
    columns_string = ', '.join(columns)  # e.g. [location, price] -> 'location, price'
    # replace the curly brackets in query_template with the corresponding info
    query = query_template.format(columns=columns_string, key=key, value=value,
                                  budget=budget, stay_nights=stay_nights, wished_room_type=wished_room_type)

    # execute query
    r = c.execute(query)
    # get results as list
    results = r.fetchall()


    # close connection
    conn.close()

    return results


def airbnb_bot(sql_file, top_n):
    """
    find flats in a given location.

    main steps:
    1) get input sentence from the user; normalize upper/lowercase
    2) extract the location name from the user input
    3) query sql_file for flats in the given location
    4) print the top_n results
    """

    # (Step 0: make sure sql_file exists)
    if not isfile(sql_file):
        # raise an error if the file is not found
        raise FileNotFoundError(
            'Die Datei {} konnte nicht gefunden werden!'.format(sql_file)
        )

    #################################################
    # STEP 1: say hi and show basic functionalities #
    #################################################

    start_sent = input('Hallöchen! Bist du bereit für eine schöne Reise nach Berlin? ')
    start_sent = start_sent.lower().translate(str.maketrans('', '', string.punctuation))

    confirmation = ['ok', 'klar', 'ja', 'natürlich', 'sicher', 'doch', 'yes', 'auf jeden fall']
    for i in range(len(confirmation)):
        if confirmation[i] in start_sent:

            # print available neighbourhoods
            neighbourhoods = [
                'Charlottenburg-Wilm.', 'Friedrichshain-Kreuzberg',
                'Lichtenberg', 'Marzahn - Hellersdorf', 'Mitte', 'Neukölln', 'Pankow',
                'Reinickendorf', 'Spandau', 'Steglitz - Zehlendorf',
                'Tempelhof - Schöneberg', 'Treptow - Köpenick']
            print('\nSehr schön! Wir haben Appartements in folgenden Stadtteilen:')
            print(', '.join(neighbourhoods))


            #####################################################################
            # STEP 2: ask user for four inputs and extract location, budget,    #
            #         nights of staying and prefered room typ of the user       #
            # if input cannot be processed, ask for new inputs till one could   #
            #####################################################################

            # NLU - Sprache verstehen

            # get where the user is about to stay
            answer = True
            while answer:
                loc_sent = input('\nWo möchtest du denn übernachten? ')
                loc_sent = loc_sent.lower()
                if get_location_from_input(loc_sent, regex_list=location_regex) != None:
                    location = get_location_from_input(loc_sent, regex_list=location_regex)
                    break

            # get budget
            answer = True
            while answer:
                budget = input('\nWas ist dein Budget pro Nacht? ')
                if check_validity(budget, answer) == True:
                    break

            # get how many nights the user wants to stay
            answer = True
            while answer:
                stay_nights = input('\nWie viele Nächte möchtest du übernachten? ')
                if check_validity(stay_nights, answer) == True:
                    break

            # get wished room type
            answer = True
            while answer:
                room_type_sent = input('\nWelche Residenzart gefällt dir besser? Ganzes Haus/Apartment oder nur ein privates Zimmer? ')
                room_type_sent = room_type_sent.lower()
                if get_room_type(room_type_sent, regex_list=room_type_regex) != None:
                    wished_room_type = get_room_type(room_type_sent, regex_list=room_type_regex)
                    break


            #####################################################################
            # STEP 3: query sqlite file for flats in the area given by the user #
            #####################################################################

            # get matches from csv file
            columns = ['name', 'neighbourhood', 'price', 'minimum_nights', 'room_type']
            results = query_sql(
                key='neighbourhood_group', value=location, budget=budget, stay_nights=stay_nights, wished_room_type=wished_room_type,
                columns=columns, sql_file=sql_file,
            )

            # if there are no results: apologize & quit
            if len(results) == 0:
                print('Tut mir Leid, ich konnte leider nichts finden!')
                return


            #############################################################################
            # STEP 4: print information about the first top_n flats in the results list #
            #############################################################################

            # NLG- Sprachgenerierung

            # return results
            print('\nIch habe {} passende Wohnungen in {} gefunden.\n'.format(
                len(results), location))
            print('Hier sind die {} besten Ergebnisse:\n'.format(top_n))

            # print the first top_n entries from the results list
            for r in results[:top_n]:
                number = '  🏡"{}", {}. Das Apartment kostet {}€ pro Nacht.'.format(
                    # look at the columns list to see what r[0], r[1], r[2] are referring to!
                    r[0], r[1], r[2]
                )
                print(number)
            break
    else:
        print('Leider kann ich vorerst nichts für dich tun :(')


if __name__ == '__main__':
    #  the airbnb_bot() function is called if the script is executed!
    airbnb_bot(sql_file='listings.db', top_n=10)




