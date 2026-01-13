import requests
from flask import Blueprint, request, Response

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

bp = Blueprint('proxy', __name__, url_prefix='/proxy')

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@bp.route('/readability')
def readability():
    if not HAS_TRAFILATURA:
        return "Error: Trafilatura not available in Lite Mode. This feature requires the full installation.", 503
    
    url = request.args.get('url')
    proxy_url = request.args.get('proxy')
    
    if not url:
        return "Error: Missing 'url' parameter", 400

    proxies = None
    if proxy_url:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

    try:
        # manual fetch with requests to control headers and proxies
        response = requests.get(url, headers=DEFAULT_HEADERS, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        # pass the html content to trafilatura
        text = trafilatura.extract(response.text)
        
        if text is None:
             return "Error: Failed to extract content", 404

        return Response(text, mimetype='text/plain')

    except requests.RequestException as e:
        return f"Error: Failed to fetch URL: {str(e)}", 400
    except Exception as e:
        return f"Error: {str(e)}", 500
