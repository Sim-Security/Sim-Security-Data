# scripts/data_processing/utils/splitters.py
# This module splits the annotated dataset into training, validation, and test sets.

import random
from typing import List, Dict, Tuple

def split_dataset(entries: List[Dict], train_ratio=0.8, val_ratio=0.1, test_ratio=0.1) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Randomly shuffle and split the dataset into train, val, and test sets.
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("Train/Val/Test ratios must sum to 1.0")

    random.shuffle(entries)
    total = len(entries)
    train_end = int(train_ratio * total)
    val_end = train_end + int(val_ratio * total)

    train_set = entries[:train_end]
    val_set = entries[train_end:val_end]
    test_set = entries[val_end:]

    return train_set, val_set, test_set
