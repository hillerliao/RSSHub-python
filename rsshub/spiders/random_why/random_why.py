
import random
import requests
from rsshub.extensions import cache

def ctx(dataset_name="Mxode/I_Wonder_Why-Chinese"):
    # Extract project name from dataset_name (format: "username/project_name")
    project_name = dataset_name.split("/")[-1] if "/" in dataset_name else dataset_name
    feed_title = f"{project_name.upper()} Random Question"
    feed_link = f"https://huggingface.co/datasets/{dataset_name}"
    
    try:
        # Check cache first
        cache_key = f'random_why_content:{dataset_name}'
        random_item = cache.get(cache_key)
        
        if not random_item:
            # Use Hugging Face Datasets Server API to avoid heavy 'datasets' library
            try:
                # 1. Get dataset size and configs
                # We use datasets-server.huggingface.co which works even if hf-mirror is used for files
                size_url = f"https://datasets-server.huggingface.co/size?dataset={dataset_name}"
                resp = requests.get(size_url, timeout=5)
                # If 404 or other error, return helpful message
                if resp.status_code != 200:
                    return {
                        'title': feed_title,
                        'link': feed_link,
                        'description': f'Error: Could not fetch dataset info (Status {resp.status_code})',
                        'items': []
                    }
                
                data = resp.json()
                
                # Determine config - prefer 'general'
                config = 'default' 
                if 'size' in data and 'configs' in data['size']:
                    # data['size']['configs'] is a list of dicts with 'config' key
                    available_configs = [c['config'] for c in data['size']['configs']]
                    if 'general' in available_configs:
                        config = 'general'
                    elif available_configs:
                        config = available_configs[0]
                    else:
                        return {
                            'title': feed_title,
                            'link': feed_link,
                            'description': 'Error: No configurations found. This dataset might not be indexed by Hugging Face Datasets Server (it needs to be in a supported format like Parquet, CSV, or standard JSONL).',
                            'items': []
                        }
                else:
                    return {
                        'title': feed_title,
                        'link': feed_link,
                        'description': 'Error: Invalid API response format from HF',
                        'items': []
                    }

                # Find num_rows for split 'train'
                num_rows = 0
                if 'size' in data and 'splits' in data['size']:
                    for s in data['size']['splits']:
                        if s['config'] == config and s['split'] == 'train':
                            num_rows = s['num_rows']
                            break
                
                if num_rows == 0:
                    return {
                        'title': feed_title,
                        'link': feed_link,
                        'description': 'Error: No rows found in train split',
                        'items': []
                    }
                
                # 2. Pick random index
                idx = random.randint(0, num_rows - 1)
                
                # 3. Fetch row
                rows_url = f"https://datasets-server.huggingface.co/rows?dataset={dataset_name}&config={config}&split=train&offset={idx}&length=1"
                resp = requests.get(rows_url, timeout=5)
                resp.raise_for_status()
                row_data = resp.json()
                
                if 'rows' not in row_data or not row_data['rows']:
                    return {
                        'title': feed_title,
                        'link': feed_link,
                        'description': 'Error: Empty response from rows API',
                        'items': []
                    }
                
                # Extract the row content
                random_item = row_data['rows'][0]['row']
                # Store index for linking
                random_item['_index'] = idx
                random_item['_config'] = config
                
                # Map fields if needed
                # Questions/Prompts
                if 'question' not in random_item:
                    for k in ['prompt', 'instruction', 'context', 'title', 'input']:
                        if k in random_item and random_item[k]:
                            random_item['question'] = str(random_item[k])
                            break
                
                # Answers/Responses
                if 'answer' not in random_item:
                    for k in ['response', 'content', 'output', 'answer_text']:
                        if k in random_item and random_item[k]:
                            random_item['answer'] = str(random_item[k])
                            break
                
                # Special case for poetry: title + author -> question, content -> answer
                if 'title' in random_item and 'author' in random_item:
                    q = f"《{random_item['title']}》 - {random_item['author']}"
                    random_item['question'] = q

            except Exception as api_e:
                import traceback
                traceback.print_exc()
                return {
                    'title': feed_title,
                    'link': feed_link,
                    'description': f'Error fetching random item: {str(api_e)}',
                    'items': []
                }
            
            # Cache the random item for 30 minutes
            cache.set(cache_key, random_item, timeout=1800)
        
        # Format the item for RSS
        question = random_item.get('question', '').strip()
        answer = random_item.get('answer', '').strip()
        idx = random_item.get('_index', 0)
        config = random_item.get('_config', 'default')
        
        if not question:
            return {
                'title': feed_title,
                'link': feed_link,
                'description': 'Error: no question found in random item',
                'items': []
            }
        
        title = question
        description = answer if answer else question
        
        # Link to the viewer
        item_link = f"{feed_link}/viewer/{config}/train?row={idx}"
        
        item = {
            'title': title,
            'description': description,
            'link': item_link,
            'pubDate': '',  # No date information available
        }
        
        return {
            'title': feed_title,
            'link': feed_link,
            'description': f'Random question and answer from {project_name} dataset',
            'items': [item]
        }
    
    except Exception as e:
        return {
            'title': feed_title,
            'link': feed_link,
            'description': f'Error: {str(e)}',
            'items': []
        }
