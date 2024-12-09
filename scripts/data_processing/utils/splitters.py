# This module handles splitting the dataset into training, validation, and test sets.
# It ensures balanced splits by categories if possible.

import random
from typing import List, Dict, Tuple

def split_dataset(entries: List[Dict], train_ratio=0.8, val_ratio=0.1, test_ratio=0.1) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Split the dataset into train, val, and test sets.
    Ensures a random split while maintaining balanced categories if possible.
    
    For simplicity, this just does a random shuffle and split by ratio.
    More sophisticated balancing can be added if needed.
    """
    random.shuffle(entries)
    total = len(entries)
    train_end = int(train_ratio * total)
    val_end = train_end + int(val_ratio * total)

    train_set = entries[:train_end]
    val_set = entries[train_end:val_end]
    test_set = entries[val_end:]
    return train_set, val_set, test_set
