import argparse

# Define the version number
# Updated to reflect the new features and improvements
__version__ = "6.2.0"


def version():
    """Parses command-line arguments for version display."""
    parser = argparse.ArgumentParser(description='Hiddify Telegram Bot Version Information')
    parser.add_argument("--version", action="version", version=f"Hiddify Telegram Bot v{__version__}")
    args = parser.parse_args()
    return args


def is_version_less(version1, version2):
    """
    Compares two version strings.
    
    Args:
        version1 (str): The first version string.
        version2 (str): The second version string.
        
    Returns:
        bool: True if version1 is less than version2, False otherwise.
    """
    try:
        # Split version strings into parts and convert to integers
        v1_parts = [int(part) for part in version1.split('.')]
        v2_parts = [int(part) for part in version2.split('.')]
        
        # Pad the shorter version with zeros
        max_length = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_length - len(v1_parts)))
        v2_parts.extend([0] * (max_length - len(v2_parts)))
        
        # Compare each part
        for part1, part2 in zip(v1_parts, v2_parts):
            if part1 < part2:
                return True
            elif part1 > part2:
                return False
                
        # If all parts are equal
        return False
    except (ValueError, AttributeError):
        # In case of invalid version strings, assume version1 is not less
        return False


def get_version_tuple(version_str):
    """
    Converts a version string to a tuple of integers for easier comparison.
    
    Args:
        version_str (str): The version string.
        
    Returns:
        tuple: A tuple of integers representing the version.
    """
    try:
        return tuple(int(part) for part in version_str.split('.'))
    except ValueError:
        return (0, 0, 0)  # Return a default tuple if conversion fails


def compare_versions(version1, version2):
    """
    Compares two version strings and returns an integer indicating their relationship.
    
    Args:
        version1 (str): The first version string.
        version2 (str): The second version string.
        
    Returns:
        int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2.
    """
    v1_tuple = get_version_tuple(version1)
    v2_tuple = get_version_tuple(version2)
    
    if v1_tuple < v2_tuple:
        return -1
    elif v1_tuple > v2_tuple:
        return 1
    else:
        return 0


# Example usage (if needed in other parts of the application)
def get_current_version():
    """Returns the current version of the bot."""
    return __version__


if __name__ == "__main__":
    # When run directly, display version information
    version()
