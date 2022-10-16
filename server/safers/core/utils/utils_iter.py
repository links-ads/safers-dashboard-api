def chunk(lst, chunk_size):
    """
    split lst into sublists of size chunk_size
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]
