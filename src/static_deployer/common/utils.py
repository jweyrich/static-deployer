import re

def interval_string_to_seconds(input: str) -> int:
    SUFFIX_MAP = {
        'y': 'y',
        'year': 'y',
        'years': 'y',
        'w': 'w',
        'week': 'w',
        'weeks': 'w',
        'd': 'd',
        'day': 'd',
        'days': 'd',
        'h': 'h',
        'hour': 'h',
        'hours': 'h',
        'm': 'm',
        'minute': 'm',
        'minute': 'm',
        's': 's',
        'second': 's',
        'seconds': 's',
    }
    SUFFIX_MULTIPLES = {
        'y': 60 * 60 * 24 * 365, # We assume 365 days, not a solar year.
        'w': 60 * 60 * 24 * 7,
        'd': 60 * 60 * 24,
        'h': 60 * 60,
        'm': 60,
        's': 1,
    }
    total = 0
    pattern = re.compile(r'(\d+)[\s,]*([a-zA-Z]+)')
    for match in pattern.finditer(input):
        amount = int(match.group(1))
        suffix = match.group(2).lower()
        if not suffix in SUFFIX_MAP:
            raise ValueError(f'Invalid interval string specified: {input}')
        index = SUFFIX_MAP[suffix]
        multiple = SUFFIX_MULTIPLES[index]
        total += amount * multiple
    return total