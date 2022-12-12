from pathlib import Path
import re


def timestamp_to_milliseconds(timestamp: str) -> int:
    parts = timestamp.split(':')
    assert len(parts) == 3, 'A timestamp should have 2 colons'
    parts[-1] = parts[-1].replace('.', '')
    hours, mins, msecs = [int(x) for x in parts]
    return 60 * 60 * 1000 * hours + 60 * 1000 * mins + msecs


def test_timestamp_line(line: str) -> bool:
    '''
    Tests whether a line with timestamps in the vtt has a difference of 10 milliseconds or not.
    If it does, then this method returns False.
    This method assumes that a line contains two timestamps.
    '''
    ts_start, ts_end = re.findall(r'\d+:\d+:\d+\.\d+', line)
    return timestamp_to_milliseconds(ts_end) - timestamp_to_milliseconds(ts_start) != 10


def fix_vtt(subs_path) -> str:
    raw_file = subs_path.read_text()
    # Find all timestamps and make a list with only the lines with
    # timestamp_difference != 10 ms
    timestamps = re.findall(r'\d+:\d+:\d+.*%', raw_file)
    timestamps = [line for line in timestamps if test_timestamp_line(line)]
    # Find the first bulk of text after a timestamp
    # Use double space as a delimiter for the individual lines
    subs = re.search(r'%\n \n(.*)', raw_file)
    subs = subs[1].split('  ')
    # Remove everything within angle brackets "<...>"
    subs = [re.sub('<.*?>', '', line) for line in subs]
    assert len(timestamps) == len(
        subs), 'Length of timestamps and lines with subs should be equal'
    # Generate new vtt, doesn't include the first few lines with metadata
    new_subs = ''.join([f"{ts}\n{line}\n\n" for ts,
                       line in zip(timestamps, subs)])
    return new_subs
    # Cleaner output:
    timestamps = [re.search(r'\d+:\d+:\d+', ts)[0] for ts in timestamps]
    new_subs = '\n'.join([f"{ts} {line}" for ts,
                          line in zip(timestamps, subs)])


def get_path_fixed(subs_raw_path):
    '''
    Takes a pathlib object as input and adds '_fixed' before the suffixes.
    Returns a new pathlib object.
    '''
    suffix_str = ''.join(subs_raw_path.suffixes)
    new_title = subs_raw_path.name[:-
                                   len(suffix_str)] + '_fixed' + suffix_str
    # print(new_title)
    new_path = subs_raw_path.parent / new_title
    return new_path

def fix_sub(path):
    subs_raw_path = Path(path)
    return fix_vtt(subs_raw_path)

