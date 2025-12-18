import json
import requests
import random
import os
from datetime import datetime
from collections import defaultdict
from requests.exceptions import ConnectionError, Timeout, RequestException


def ctx(api_url=None):
    """
    Fetch Anki cards that are due for review via Anki Connect API
    Returns context dictionary for RSS template
    """
    
    # Configuration - using environment variables with defaults
    limit = 20
    
    try:
        # Determine base URL for AnkiConnect API
        if api_url:
            # Normalize input: ensure it has a scheme for urlparse
            from urllib.parse import urlparse
            if '://' not in api_url:
                api_url = f'http://{api_url}'
            parsed = urlparse(api_url)
            host = parsed.hostname or 'localhost'
            port = str(parsed.port or 8765)
            base_url = f'http://{host}:{port}'
        else:
            host = os.environ.get('ANKI_CONNECT_HOST', 'localhost')
            port = os.environ.get('ANKI_CONNECT_PORT', '8765')
            base_url = f'http://{host}:{port}'
        
        # Test connection first
        try:
            test_response = requests.post(
                base_url,
                json={"action": "version", "version": 6},
                timeout=5
            )
            if test_response.status_code != 200:
                raise ConnectionError("Anki-Connect returned non-200 status code")
        except (ConnectionError, Timeout):
            # In case of connection error, return informative error message
            return {
                'title': 'Anki Cards Due for Review - Connection Error',
                'description': 'Cannot connect to Anki. Please make sure Anki is running and AnkiConnect is installed.',
                'link': 'https://apps.ankiweb.net/',
                'author': 'Anki RSS Hub',
                'items': [{
                    'title': 'Connection Error: Cannot Connect to Anki',
                    'description': f'''Please ensure that:
1. Anki application is installed and running on {host} (port {port})
2. AnkiConnect addon is installed in Anki:
   - Go to Tools > Add-ons > Get Add-ons in Anki
   - Enter code: 2055492159
   - Restart Anki after installation
3. AnkiConnect is configured to listen on {host}:{port}
   - Go to Tools > Add-ons > AnkiConnect > Config in Anki
   - Make sure the "webBindAddress" is set to "0.0.0.0" or "{host}" and "webBindPort" is set to {port}
   - You may also need to set "webCorsOrigin" to allow requests from your RSSHub instance
4. No firewall is blocking the connection to port {port}''',
                    'link': 'https://foosoft.net/projects/anki-connect/',
                    'author': 'Anki RSS Hub',
                    'pubDate': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                }]
            }
        except RequestException as e:
            # Other request errors
            return {
                'title': 'Anki Cards Due for Review - Request Error',
                'description': f'Error communicating with Anki: {str(e)}',
                'link': 'https://apps.ankiweb.net/',
                'author': 'Anki RSS Hub',
                'items': [{
                    'title': f'Request Error: {str(e)}',
                    'description': 'There was an error communicating with Anki. Please check the logs for more details.',
                    'link': 'https://foosoft.net/projects/anki-connect/',
                    'author': 'Anki RSS Hub',
                    'pubDate': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                }]
            }
        
        # Get due cards for today using findCards with is:due filter
        payload = {
            "action": "findCards",
            "version": 6,
            "params": {
                "query": "is:due"
            }
        }
        
        response = requests.post(base_url, json=payload, timeout=10)
        card_ids = response.json()['result']
        
        # Handle case when no cards are due
        if not card_ids:
            return {
                'title': 'Anki Cards Due for Review',
                'description': 'No cards are currently due for review',
                'link': 'https://apps.ankiweb.net/',
                'author': 'Anki',
                'items': [{
                    'title': 'No Cards Due',
                    'description': 'There are currently no cards scheduled for review. Check back later or add new cards to your deck.',
                    'link': 'https://apps.ankiweb.net/',
                    'author': 'Anki',
                    'pubDate': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                }]
            }
        
        # Get card information for all due cards
        payload = {
            "action": "cardsInfo",
            "version": 6,
            "params": {
                "cards": card_ids
            }
        }
        
        response = requests.post(base_url, json=payload, timeout=10)
        cards_info = response.json()['result']
        
        # Group cards by deck to ensure even distribution
        cards_by_deck = defaultdict(list)
        for card in cards_info:
            cards_by_deck[card['deckName']].append(card)
        
        # Select one card from a randomly selected deck
        # This ensures cards from all decks have a fair chance of being selected
        selected_deck = random.choice(list(cards_by_deck.keys()))
        selected_card = random.choice(cards_by_deck[selected_deck])
        
        # Get note information for the selected card
        note_ids = [selected_card['note']]
        payload = {
            "action": "notesInfo",
            "version": 6,
            "params": {
                "notes": note_ids
            }
        }
        
        response = requests.post(base_url, json=payload, timeout=10)
        notes_info = response.json()['result']
        
        # Create mapping from note id to note info
        note_map = {note['noteId']: note for note in notes_info}
        
        # Process the selected card into RSS items
        items = []
        card = selected_card
        note = note_map[card['note']]
        
        # Extract fields from note
        fields = note['fields']
        question = ''
        answer = ''
        
        # Try to get question and answer fields (common in Anki decks)
        if 'Front' in fields:
            question = fields['Front']['value']
        elif 'Question' in fields:
            question = fields['Question']['value']
            
        if 'Back' in fields:
            answer = fields['Back']['value']
        elif 'Answer' in fields:
            answer = fields['Answer']['value']
        
        # If we couldn't find standard fields, use first two fields
        if not question and not answer and fields:
            field_names = list(fields.keys())
            if len(field_names) >= 1:
                question = fields[field_names[0]]['value']
            if len(field_names) >= 2:
                answer = fields[field_names[1]]['value']
        
        # Get additional card information
        reps = card['reps']  # Number of reviews
        lapses = card['lapses']  # Number of lapses (incorrect reviews)
        due_date = card['due']  # Due date
        interval = card['interval']  # Interval in days
        ease_factor = card['factor'] / 1000.0 if card['factor'] else 0  # Ease factor
        deck_name = card['deckName']  # Deck name
        card_type = card['type']  # Card type (0=new, 1=learning, 2=review, 3=relearning)
        card_queue = card['queue']  # Card queue (-3=sched buried, -2=user buried, -1=suspended, 0=new, 1=learning, 2=review, 3=in learning, 4=preview)
        
        # Get note information
        tags = note['tags']  # Tags
        model_name = note['modelName']  # Model name
        
        # Map card type to human-readable format
        card_type_map = {
            0: "New",
            1: "Learning",
            2: "Review",
            3: "Relearning"
        }
        card_type_text = card_type_map.get(card_type, "Unknown")
        
        # Map card queue to human-readable format
        card_queue_map = {
            -3: "Scheduled Buried",
            -2: "User Buried",
            -1: "Suspended",
            0: "New",
            1: "Learning",
            2: "Review",
            3: "In Learning",
            4: "Preview"
        }
        card_queue_text = card_queue_map.get(card_queue, "Unknown")
        
        # Create detailed description with additional information
        detailed_description = f"""
<p><strong>Card Content:</strong></p>
<p>{answer}</p>

<p><strong>Card Information:</strong></p>
<ul>
<li><strong>Deck:</strong> {deck_name}</li>
<li><strong>Card Type:</strong> {card_type_text}</li>
<li><strong>Queue:</strong> {card_queue_text}</li>
<li><strong>Model:</strong> {model_name}</li>
</ul>

<p><strong>Review Statistics:</strong></p>
<ul>
<li><strong>Total Reviews:</strong> {reps}</li>
<li><strong>Lapses (Incorrect Reviews):</strong> {lapses}</li>
<li><strong>Current Interval:</strong> {interval} days</li>
<li><strong>Ease Factor:</strong> {ease_factor:.2f}</li>
</ul>

<p><strong>Tags:</strong></p>
<ul>
"""
        
        # Add tags to the description
        if tags:
            for tag in tags:
                detailed_description += f"<li>{tag}</li>"
        else:
            detailed_description += "<li>No tags</li>"
        
        detailed_description += """
</ul>
"""
        
        # Create item for RSS with just the question in the title
        items.append({
            'title': f"{question[:100]}{'...' if len(question) > 100 else ''}",
            'description': detailed_description,
            'link': 'https://apps.ankiweb.net/', 
            'author': 'Anki',
            'pubDate': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        })
        
    except Exception as e:
        # In case of any other error, return error message
        return {
            'title': 'Anki Cards Due for Review - Error',
            'description': f'Error fetching cards from Anki: {str(e)}',
            'link': 'https://apps.ankiweb.net/',
            'author': 'Anki RSS Hub',
            'items': [{
                'title': f'Error: {str(e)}',
                'description': 'There was an error processing the request. Please check the logs for more details.',
                'link': 'https://foosoft.net/projects/anki-connect/',
                'author': 'Anki RSS Hub',
                'pubDate': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            }]
        }
    
    return {
        'title': 'Anki Cards Due for Review',
        'description': 'Random Anki card that needs to be reviewed today with detailed information',
        'link': 'https://apps.ankiweb.net/',
        'author': 'Anki',
        'items': items
    }
