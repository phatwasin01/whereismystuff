# WiMs: Where is My Stuffs

DES323 Multi-platform Software Development

# Database

Setting located in `Settings.py`

- PostgreSQL
- Name: whereismystuffs
- User: root
- Password: secret
- Port: 5436

# API Keys

In `views.py`

```
# New York Times Books API
async def getBestSellingBooks(request):
....
...
..
.
    API_KEY = ''
```

```
# OpenAI API
def createBookOCR(request):
....
...
.
        api_key = ""
```
