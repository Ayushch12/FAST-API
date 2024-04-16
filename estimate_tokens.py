def estimate_tokens(text, method="max"):
    """
    Estimate the number of tokens in the given text.
    
    Parameters:
    - text (str): The input text to estimate tokens for.
    - method (str): The method of estimation. Options: "average", "words", "chars", "max", "min".
                    Defaults to "max".
                    
    Returns:
    int: An estimation of the number of tokens.
    """
    
    # Calculating word and character counts
    word_count = len(text.split())
    char_count = len(text)
    
    # Estimating tokens based on words and characters
    tokens_count_word_est = word_count / 0.75
    tokens_count_char_est = char_count / 4.0
    
    # Selecting estimation method
    if method == "average":
        output = (tokens_count_word_est + tokens_count_char_est) / 2
    elif method == "words":
        output = tokens_count_word_est
    elif method == "chars":
        output = tokens_count_char_est
    elif method == 'max':
        output = max(tokens_count_word_est, tokens_count_char_est)
    elif method == 'min':
        output = min(tokens_count_word_est, tokens_count_char_est)
    else:
        raise ValueError("Invalid method. Use 'average', 'words', 'chars', 'max', or 'min'.")
    
    return int(output)