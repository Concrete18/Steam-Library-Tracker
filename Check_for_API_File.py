import os

def Check_for_API():
    '''Checks for an api_key.txt and asks for an API key to create one if it does not exist.'''
    if os.path.isfile('api_key.txt') is False:
        api_key = ''
        with open(os.path.join(os.getcwd(), 'api_key.txt'), 'w') as f:
            api_key = input('Enter your Steam API Key.\n')
            f.write(api_key)
    with open('api_key.txt') as f:
        api_key = f.read()
    return api_key
