A small app for exploring idols with similar faces.

The faces are compared using the Facenet implementation from [github.com/davidsandberg/facenet](https://github.com/davidsandberg/facenet).

## Try it yourself

Download model [20180402-114759](https://drive.google.com/open?id=1EXPBSXwTaqrSC0OhUdXNmKSh9qJUQ55-).

Extract it into models directory.

### Setup environment

I only tested with Python 3.5.x

```
git clone https://github.com/bobbytrapz/lookalike
cd lookalike
python3.5 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Build lookalike.json

face similarities are calculated and stored in lookalike.json

```
python lookalike.py
```

### Lookup data for an idol by name

```
python lookalike.py 齊藤京子
```
